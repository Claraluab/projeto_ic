# app.py
from flask import Flask, render_template, request, jsonify, send_file
import pandas as pd
import io
import json
from datetime import datetime
from threading import Thread

from database_operations import get_db_connection, get_table_names, get_table_data, get_table_row_count
from data_processor import initialize_database, update_ons_data, update_ccee_data

app = Flask(__name__)
app.config.from_pyfile('config.py')

# Tela 1 – Página Inicial
@app.route('/')
def index():
    return render_template('index.html')

#  Tela 2 – Listagem de Tabelas
@app.route('/tabelas')
def list_tables():
    try:
        table_names = get_table_names()
        return render_template('tables.html', tables=table_names)
    except Exception as e:
        return render_template('error.html', error=f"Erro ao acessar o banco de dados: {str(e)}")

# Tela 3 – Visualização de Dados da Tabela
@app.route('/tabelas/<table_name>')
def table_data(table_name):
    try:
        page = request.args.get('page', 1, type=int)
        per_page = 50
        
        # Obter total de registros
        total = get_table_row_count(table_name)
        
        # Calcular número total de páginas
        total_pages = (total + per_page - 1) // per_page
        
        # Obter dados paginados
        columns, data = get_table_data(table_name, per_page, (page - 1) * per_page)
        
        return render_template('table_data.html', 
                             table_name=table_name,
                             columns=columns,
                             data=data,
                             page=page,
                             per_page=per_page,
                             total=total,
                             total_pages=total_pages)
    except Exception as e:
        return render_template('error.html', error=f"Erro ao acessar dados da tabela: {str(e)}")

#  Tela 4 – Dashboard Interativo
@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

# API para dados do dashboard
@app.route('/api/dashboard/<chart_type>')
def api_dashboard(chart_type):
    try:
        conn = get_db_connection()
        
        if chart_type == 'pld':
            query = "SELECT date, submarket, pld FROM pld_submarket ORDER BY date"
        elif chart_type == 'ena':
            query = "SELECT date, submarket, ena FROM ena_submarket ORDER BY date"
        elif chart_type == 'ear':
            query = "SELECT date, submarket, ear FROM ear_submarket ORDER BY date"
        elif chart_type == 'cmo':
            query = "SELECT date, submarket, cmo FROM cmo_submarket ORDER BY date"
        elif chart_type == 'geracao':
            query = """
            SELECT date, submarket, hydro, thermal, wind, solar 
            FROM energy_balance 
            ORDER BY date
            """
        else:
            return jsonify({'error': 'Tipo de gráfico não suportado'}), 400
        
        df = pd.read_sql(query, conn)
        conn.close()
        
        # Converter DataFrame para dicionário
        result = df.to_dict(orient='records')
        
        # Converter objetos Timestamp para strings
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

# Exportar CSV
@app.route('/export/<table_name>')
def export_csv(table_name):
    try:
        conn = get_db_connection()
        df = pd.read_sql(f"SELECT * FROM {table_name}", conn)
        conn.close()
        
        output = io.BytesIO()
        df.to_csv(output, index=False, encoding='utf-8')
        output.seek(0)
        
        return send_file(
            output,
            mimetype='text/csv',
            as_attachment=True,
            download_name=f'{table_name}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        )
    except Exception as e:
        return render_template('error.html', error=f"Erro ao exportar dados: {str(e)}")

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