import requests

def verificar_endpoint_pld():
    try:
        url = "https://dadosabertos.ccee.org.br/api/3/action/package_show?id=pld_horario_submercado"
        response = requests.get(url, timeout=15)

        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                resources = data['result']['resources']
                print("\nRecursos disponíveis para PLD:")
                for res in resources:
                    print(f"- {res['name']} (Última atualização: {res.get('last_modified', 'N/A')})")
                return True
        return False
    except Exception as e:
        print(f"Erro ao verificar endpoint PLD: {str(e)}")
        return False


# Adicione no seu main
if __name__ == "__main__":
    if not verificar_endpoint_pld():
        print("\nAVISO: Problemas no endpoint específico do PLD")