from flask import Flask, render_template, request, jsonify, send_file, Response
import pandas as pd
import io
import csv
from datetime import datetime
from threading import Thread
from sqlalchemy import text

from database_operations import get_db_connection, get_table_names, get_table_data, get_table_row_count
from data_processor import initialize_database, update_ons_data, update_ccee_data

app = Flask(__name__)
app.config.from_pyfile('config.py')

# Tela 1 – Página Inicial
@app.route('/')
def index():
    return render_template('index.html')

# Tela 2 – Listagem de Tabelas
@app.route('/tabelas')
def list_tables():
    try:
        table_names = get_table_names()
        return render_template('tables.html', tables=table_names)
    except Exception as e:
        return render_template('error.html', error=f"Erro ao acessar o banco de dados: {str(e)}") 

# Tela 3 – Visualização de Dados de Tabela
@app.route('/tabelas/<table_name>')
def table_data(table_name):
    try:
        # Obter parâmetros de paginação e filtro
        page = request.args.get('page', 1, type=int)
        per_page = 100  # Itens por página
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')

        conn = get_db_connection()
        cursor = conn.cursor()

        # Descobrir colunas
        cursor.execute(f"SELECT * FROM {table_name} LIMIT 0")
        columns = [desc[0] for desc in cursor.description]

        # Construir consulta base
        query = f"SELECT * FROM {table_name}"
        count_query = f"SELECT COUNT(*) FROM {table_name}"
        conditions = []
        params = []

        # Adicionar filtros de data se fornecidos
        date_column = None
        for col in columns:
            if col.lower() in ['date', 'data', 'timestamp', 'datetime']:
                date_column = col
                break

        if date_column:
            if start_date:
                conditions.append(f"{date_column} >= %s")
                params.append(start_date)
            if end_date:
                conditions.append(f"{date_column} <= %s")
                params.append(end_date)

        if conditions:
            where_clause = " WHERE " + " AND ".join(conditions)
            query += where_clause
            count_query += where_clause

        # Adicionar paginação
        query += f" LIMIT {per_page} OFFSET {(page - 1) * per_page}"

        # Executar consultas
        cursor.execute(query, params)
        data = cursor.fetchall()

        cursor.execute(count_query, params)
        total_count = cursor.fetchone()[0]
        total_pages = (total_count + per_page - 1) // per_page

        conn.close()

        return render_template(
            'table_data.html',
            table_name=table_name,
            columns=columns,
            data=data,
            page=page,
            total_pages=total_pages,
            start_date=start_date,
            end_date=end_date
        )
    except Exception as e:
        return render_template('error.html', error=f"Erro ao acessar tabela: {str(e)}")

# Exportar dados para CSV
@app.route('/export/<table_name>')
def export_csv(table_name):
    try:
        # Obter parâmetros de data
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Primeiro, descubra o nome da coluna de data
        cursor.execute(f"SELECT * FROM {table_name} LIMIT 0")
        columns = [desc[0] for desc in cursor.description]
        
        # Encontrar a coluna de data
        date_column = None
        for col in columns:
            if col.lower() in ['date', 'data', 'timestamp', 'datetime']:
                date_column = col
                break
        
        # Construir consulta com filtros de data se fornecidos
        query = f"SELECT * FROM {table_name}"
        conditions = []
        params = []
        
        if date_column:
            if start_date:
                conditions.append(f"{date_column} >= %s")
                params.append(start_date)
            if end_date:
                conditions.append(f"{date_column} <= %s")
                params.append(end_date)
        
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        
        # Executar a consulta e obter os dados
        cursor.execute(query, params)
        data = cursor.fetchall()
        
        conn.close()
        
        # Criar arquivo CSV em memória
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Escrever cabeçalho
        writer.writerow(columns)
        
        # Escrever dados
        for row in data:
            writer.writerow(row)
        
        output.seek(0)
        
        # Criar nome do arquivo com as datas se existirem
        if start_date and end_date:
            filename = f'{table_name}_{start_date}_{end_date}.csv'
        elif start_date:
            filename = f'{table_name}_{start_date}_to_now.csv'
        elif end_date:
            filename = f'{table_name}_until_{end_date}.csv'
        else:
            filename = f'{table_name}_all.csv'
        
        return Response(
            output.getvalue(),
            mimetype="text/csv",
            headers={"Content-Disposition": f"attachment;filename={filename}"}
        )
    except Exception as e:
        return render_template('error.html', error=f"Erro ao exportar dados: {str(e)}")
    
# Tela 4 – Dashboard Interativo
@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

# API para dados do dashboard
@app.route('/api/dashboard/<chart_type>')
def api_dashboard(chart_type):
    try:
        conn = get_db_connection()

        # Mapeia a tabela e colunas por tipo de gráfico
        if chart_type == 'pld':
            base_query = "SELECT date, submarket, pld FROM pld_submarket"
        elif chart_type == 'ena':
            base_query = "SELECT date, submarket, ena FROM ena_submarket"
        elif chart_type == 'ear':
            base_query = "SELECT date, submarket, ear FROM ear_submarket"
        elif chart_type == 'cmo':
            base_query = "SELECT date, submarket, cmo FROM cmo_submarket"
        elif chart_type == 'geracao':
            base_query = """
                SELECT date, submarket, hydro, thermal, wind, solar
                FROM energy_balance
            """
        else:
            return jsonify({'error': 'Tipo de gráfico não suportado'}), 400

        # Filtros
        conditions = []
        params = []

        start = request.args.get('start')  # 'YYYY-MM-DD'
        end = request.args.get('end')      # 'YYYY-MM-DD'
        subs = request.args.get('subs')    # 'NORTH,NORTHEAST,...'

        if start:
            conditions.append("date >= %s")
            params.append(f"{start} 00:00:00")
        if end:
            conditions.append("date <= %s")
            params.append(f"{end} 23:59:59")

        if subs:
            subs_list = [s.strip() for s in subs.split(',') if s.strip()]
            if subs_list:
                # constrói IN (%s,%s,...) seguro
                placeholders = ",".join(["%s"] * len(subs_list))
                conditions.append(f"submarket IN ({placeholders})")
                params.extend(subs_list)

        where_clause = f" WHERE {' AND '.join(conditions)}" if conditions else ""
        order_clause = " ORDER BY date"

        full_query = base_query + where_clause + order_clause

        # usa pandas para executar com parâmetros
        df = pd.read_sql(full_query, conn, params=params)
        conn.close()

        result = df.to_dict(orient='records')

        # normaliza data para string
        for item in result:
            if 'date' in item and hasattr(item['date'], 'strftime'):
                item['date'] = item['date'].strftime('%Y-%m-%d %H:%M:%S')

        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Tela 5 – Administração/Status
@app.route('/admin')
def admin():
    try:
        # Verificar status do banco de dados
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Verificar quantidade de registros em cada tabela
        tables = get_table_names()
        table_stats = {}
        
        for table in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            cursor.execute(f"SELECT MAX(date) FROM {table}")
            last_date = cursor.fetchone()[0]
            
            table_stats[table] = {
                'count': count,
                'last_date': last_date.strftime('%Y-%m-%d') if last_date else 'N/A'
            }
        
        conn.close()
        
        return render_template('admin.html', table_stats=table_stats)
    except Exception as e:
        return render_template('error.html', error=f"Erro ao acessar painel administrativo: {str(e)}")


# Inicialização do banco
@app.route('/init-db')
def init_db():
    try:
        thread = Thread(target=initialize_database)
        thread.start()
        return jsonify({
            'status': 'success', 
            'message': 'Inicialização do banco iniciada em background. Esta operação pode levar vários minutos.'
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

# Atualização manual de dados
@app.route('/api/update', methods=['POST'])
def manual_update():
    try:
        # Executar atualizações em threads separadas
        thread_ons = Thread(target=update_ons_data)
        thread_ccee = Thread(target=update_ccee_data)
        
        thread_ons.start()
        thread_ccee.start()
        
        return jsonify({
            'status': 'success', 
            'message': 'Atualização de dados iniciada em background. Esta operação pode levar vários minutos.'
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

# Rota para health check
@app.route('/health')
def health_check():
    try:
        conn = get_db_connection()
        conn.close()
        return jsonify({'status': 'healthy', 'database': 'connected'})
    except Exception as e:
        return jsonify({'status': 'unhealthy', 'database': 'disconnected', 'error': str(e)}), 500

# Manipulador de erros
@app.errorhandler(404)
def not_found(error):
    return render_template('error.html', error='Página não encontrada'), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('error.html', error='Erro interno do servidor'), 500

if __name__ == '__main__':
    app.run(debug=app.config['DEBUG'], host='0.0.0.0', port=5000)