import requests
import pandas as pd
from datetime import datetime
from io import BytesIO
from requests.adapters import HTTPAdapter
from config import REQUEST_TIMEOUT, HEADERS, RETRY_STRATEGY
from database_operations import get_db_connection, safe_insert, create_tables

class dadosAbertosSetorEletrico:
    def __init__(self, instituicao: str):
        self.api = '/api/3/action/'
        self.session = requests.Session()
        self.session.mount('https://', HTTPAdapter(max_retries=RETRY_STRATEGY))

        if str.lower(instituicao) == "ccee":
            self.host = 'https://dadosabertos.ccee.org.br'
        elif str.lower(instituicao) == "ons":
            self.host = 'https://dados.ons.org.br'
        elif str.lower(instituicao) == "aneel":
            self.host = 'https://dadosabertos.aneel.gov.br/'
        else:
            raise ValueError("Instituição não suportada!")

    def __request_with_retry(self, url):
        try:
            response = self.session.get(
                url,
                headers=HEADERS,
                timeout=REQUEST_TIMEOUT
            )
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException as e:
            print(f"Erro na requisição para {url}: {str(e)}")
            return None

    def listar_produtos_disponiveis(self):
        url = self.host + self.api + "package_list"
        response = self.__request_with_retry(url)
        return response.json() if response else None

    def __buscar_resource_ids_por_produto(self, produto: str):
        url = self.host + self.api + f"package_show?id={produto}"
        response = self.__request_with_retry(url)
        if not response or not response.json().get('result'):
            return []
        return [item['id'] for item in response.json()['result']['resources'] if 'id' in item]

    def baixar_dados_produto_completo(self, produto: str):
        limite = 10000
        lista_dfs = []
        resource_ids = self.__buscar_resource_ids_por_produto(produto)

        if not resource_ids:
            print(f"Nenhum resource_id encontrado para o produto {produto}")
            return pd.DataFrame()

        for key in resource_ids:
            offset = 0
            while True:
                url = self.host + self.api + f"datastore_search?resource_id={key}&limit={limite}&offset={offset}"
                response = self.__request_with_retry(url)
                if not response:
                    break

                data = response.json()
                if not data.get("success", False):
                    print(f"Resposta inválida para recurso {key}")
                    break

                registros = data["result"].get("records", [])
                if not registros:
                    break

                lista_dfs.append(pd.DataFrame(registros))
                offset += limite

        return pd.concat(lista_dfs, ignore_index=True) if lista_dfs else pd.DataFrame()

def process_ons_data(year, data_type):
    """Processa dados do ONS para diferentes tipos de dados"""
    try:
        url_map = {
            'ear': f'https://ons-aws-prod-opendata.s3.amazonaws.com/dataset/ear_subsistema_di/EAR_DIARIO_SUBSISTEMA_{year}.xlsx',
            'ena': f'https://ons-aws-prod-opendata.s3.amazonaws.com/dataset/ena_subsistema_di/ENA_DIARIO_SUBSISTEMA_{year}.xlsx',
            'cmo': f'https://ons-aws-prod-opendata.s3.amazonaws.com/dataset/cmo_tm/CMO_SEMIHORARIO_{year}.xlsx',
            'balance': f'https://ons-aws-prod-opendata.s3.amazonaws.com/dataset/balanco_energia_subsistema_ho/BALANCO_ENERGIA_SUBSISTEMA_{year}.xlsx'
        }

        response = requests.get(url_map[data_type])
        response.raise_for_status()
        df = pd.read_excel(BytesIO(response.content))

        # Processamento comum
        submarket_translation = {
            'NORDESTE': 'NORTHEAST',
            'NORTE': 'NORTH',
            'SUDESTE': 'SOUTHEAST',
            'SUDESTE/CENTRO-OESTE': 'SOUTHEAST',
            'SUL': 'SOUTH'
        }

        # Processamento específico
        if data_type == 'ear':
            df = df[['id_subsistema', 'nom_subsistema', 'ear_data', 'ear_verif_subsistema_mwmes']]
            df.columns = ['id_subsistema', 'Submarket', 'Date', 'EAR']
            df['EAR'] = pd.to_numeric(df['EAR'].astype(str).str.replace(',', '.'), errors='coerce')

        elif data_type == 'ena':
            df = df[['id_subsistema', 'nom_subsistema', 'ena_data', 'ena_armazenavel_regiao_mwmed']]
            df.columns = ['id_subsistema', 'Submarket', 'Date', 'ENA']
            df['ENA'] = pd.to_numeric(df['ENA'].astype(str).str.replace(',', '.'), errors='coerce')

        elif data_type == 'cmo':
            df = df[['id_subsistema', 'nom_subsistema', 'din_instante', 'val_cmo']]
            df.columns = ['id_subsistema', 'Submarket', 'Date', 'CMO']
            df = df[pd.to_datetime(df['Date']).dt.minute == 0]  # Filtra horas inteiras
            df['CMO'] = pd.to_numeric(df['CMO'].astype(str).str.replace(',', '.'), errors='coerce')

        elif data_type == 'balance':
            df = df[['id_subsistema', 'nom_subsistema', 'din_instante',
                     'val_gerhidraulica', 'val_gertermica', 'val_gereolica',
                     'val_gersolar', 'val_carga', 'val_intercambio']]
            df.columns = ['id_subsistema', 'Submarket', 'Date',
                          'Hydro', 'Thermal', 'Wind',
                          'Solar', 'Load', 'Exchange']
            for col in ['Hydro', 'Thermal', 'Wind', 'Solar', 'Load', 'Exchange']:
                df[col] = pd.to_numeric(df[col].astype(str).str.replace(',', '.'), errors='coerce')

        # Processamento comum
        df['Submarket'] = df['Submarket'].replace(submarket_translation)
        df['Date'] = pd.to_datetime(df['Date'])
        return df.dropna()

    except Exception as e:
        print(f"Erro processando {data_type} para {year}: {str(e)}")
        return pd.DataFrame()

def update_ons_data():
    """Atualiza todos os dados do ONS"""
    conn = get_db_connection()
    current_year = datetime.now().year

    # Para teste, vamos processar apenas o ano atual
    for year in range(current_year, current_year + 1):
        print(f"\nProcessando ONS ano {year}...")

        for data_type in ['ear', 'ena', 'cmo', 'balance']:
            df = process_ons_data(year, data_type)
            table_name = {
                'ear': 'ear_submarket',
                'ena': 'ena_submarket',
                'cmo': 'cmo_submarket',
                'balance': 'energy_balance'
            }[data_type]
            safe_insert(df, table_name, conn)

    conn.close()

def update_ccee_data():
    """Atualiza dados da CCEE (PLD) com tratamento completo"""
    print("\nProcessando dados CCEE...")
    cliente = dadosAbertosSetorEletrico("ccee")
    df = cliente.baixar_dados_produto_completo("pld_horario_submercado")
    print(f"Total de registros brutos baixados: {len(df)}")
    
    if not df.empty:
        try:
            # Converter período para dia e hora
            df['Dia'] = (df['PERIODO_COMERCIALIZACAO'] - 1) // 24 + 1
            df['Hora'] = (df['PERIODO_COMERCIALIZACAO'] - 1) % 24

            # Criar data completa
            df['Date'] = pd.to_datetime(
                df['MES_REFERENCIA'].astype(str) +
                df['Dia'].astype(str).str.zfill(2),
                format='%Y%m%d', errors='coerce'
            ) + pd.to_timedelta(df['Hora'], unit='h')

            # Padronizar nomes dos submercados
            df['SUBMERCADO'] = df['SUBMERCADO'].str.replace('/', '').str.strip()

            # Mapeamento completo
            submarket_mapping = {
                'NORDESTE': ('NE', 'NORTHEAST'),
                'NORTE': ('N', 'NORTH'),
                'SUDESTECENTROOESTE': ('SE', 'SOUTHEAST'),
                'SUDESTE': ('SE', 'SOUTHEAST'),
                'SUL': ('S', 'SOUTH')
            }

            # Mapear com tratamento de erros
            df['id_subsistema'] = df['SUBMERCADO'].apply(
                lambda x: submarket_mapping.get(x, ('Unknown', 'Unknown'))[0])
            df['Submarket'] = df['SUBMERCADO'].apply(
                lambda x: submarket_mapping.get(x, ('Unknown', 'Unknown'))[1]
            )

            # Verificar submercados não mapeados
            unicos = df[df['id_subsistema'] == 'Unknown']['SUBMERCADO'].unique()
            if len(unicos) > 0:
                print(f"Submercados não mapeados encontrados: {unicos}")

            # Filtrar e formatar
            df = df[df['id_subsistema'] != 'Unknown']
            df = df[['id_subsistema', 'Submarket', 'Date', 'PLD']]
            df['Date'] = pd.to_datetime(df['Date'])

            # Inserir no banco
            conn = get_db_connection()
            safe_insert(df, 'pld_submarket', conn)
            conn.close()

        except Exception as e:
            print(f"Erro crítico: {str(e)}")
    else:
        print("Nenhum dado CCEE encontrado.")

def initialize_database():
    """Função principal para inicializar o banco de dados"""
    print("Inicializando banco de dados...")
    create_tables()
    update_ons_data()
    update_ccee_data()
    print("Banco de dados inicializado com sucesso!")

# Ponto de entrada para teste
if __name__ == "__main__":
    print("Iniciando processamento completo de dados...")
    
    # Criar tabelas se não existirem
    from database_operations import create_tables
    create_tables()
    
    # Processar todos os dados do ONS (todos os anos)
    print("Processando dados do ONS (todos os anos)...")
    conn = get_db_connection()
    current_year = datetime.now().year
    
    for year in range(2010, current_year + 1):
        print(f"\nProcessando ONS ano {year}...")

        for data_type in ['ear', 'ena', 'cmo', 'balance']:
            df = process_ons_data(year, data_type)
            if not df.empty:
                table_name = {
                    'ear': 'ear_submarket',
                    'ena': 'ena_submarket',
                    'cmo': 'cmo_submarket',
                    'balance': 'energy_balance'
                }[data_type]
                safe_insert(df, table_name, conn)
                print(f"  {data_type.upper()}: {len(df)} registros inseridos")
            else:
                print(f"  {data_type.upper()}: Nenhum dado encontrado")

    conn.close()
    
    # Processar dados da CCEE
    print("\nProcessando dados da CCEE...")
    update_ccee_data()
    
    print("\nProcessamento completo concluído!")