import psycopg2
from config import DB_CONFIG

def get_db_connection():
    """Retorna conexão com o PostgreSQL"""
    return psycopg2.connect(**DB_CONFIG)

def get_table_names():
    """Retorna lista de tabelas disponíveis"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public'
    """)
    tables = [row[0] for row in cursor.fetchall()]
    conn.close()
    return tables

def get_table_data(table_name, limit=100, offset=0):
    """Retorna dados de uma tabela com paginação"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(f"SELECT * FROM {table_name} ORDER BY date DESC LIMIT %s OFFSET %s", (limit, offset))
    columns = [desc[0] for desc in cursor.description]
    data = cursor.fetchall()
    conn.close()
    return columns, data

def get_table_row_count(table_name):
    """Retorna o número total de linhas em uma tabela"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
    count = cursor.fetchone()[0]
    conn.close()
    return count

def create_tables():
    """Cria tabelas no PostgreSQL se não existirem"""
    conn = get_db_connection()
    cursor = conn.cursor()

    commands = [
        """
        CREATE TABLE IF NOT EXISTS pld_submarket
        (
            id_subsistema TEXT,
            submarket TEXT,
            date TIMESTAMP,
            pld REAL,
            UNIQUE (id_subsistema, date)
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS ear_submarket
        (
            id_subsistema TEXT,
            submarket TEXT,
            date TIMESTAMP,
            ear REAL,
            UNIQUE (id_subsistema, date)
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS ena_submarket
        (
            id_subsistema TEXT,
            submarket TEXT,
            date TIMESTAMP,
            ena REAL,
            UNIQUE (id_subsistema, date)
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS cmo_submarket
        (
            id_subsistema TEXT,
            submarket TEXT,
            date TIMESTAMP,
            cmo REAL,
            UNIQUE (id_subsistema, date)
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS energy_balance
        (
            id_subsistema TEXT,
            submarket TEXT,
            date TIMESTAMP,
            hydro REAL,
            thermal REAL,
            wind REAL,
            solar REAL,
            load REAL,
            exchange REAL,
            UNIQUE (id_subsistema, date)
        )
        """
    ]

    for command in commands:
        try:
            cursor.execute(command)
            print(f"Tabela criada com sucesso")
        except Exception as e:
            print(f"Erro ao criar tabela: {str(e)}")
            print(f"Comando problemático: {command}")

    conn.commit()
    cursor.close()
    conn.close()

def safe_insert(df, table_name, conn):
    """Insere dados de forma segura no PostgreSQL"""
    if df.empty:
        return

    cursor = conn.cursor()
    tuples = [tuple(x) for x in df.to_numpy()]
    cols = ','.join(df.columns)

    query = f"""
        INSERT INTO {table_name} ({cols})
        VALUES ({','.join(['%s'] * len(df.columns))})
        ON CONFLICT (id_subsistema, date) DO NOTHING
    """

    try:
        cursor.executemany(query, tuples)
        conn.commit()
        print(f"Inserted {cursor.rowcount} rows into {table_name}")
    except Exception as e:
        print(f"Database error: {e}")
    finally:
        cursor.close()

# Ponto de entrada para teste
if __name__ == "__main__":
    print("Criando tabelas no banco de dados...")
    create_tables()
    print("Tabelas criadas com sucesso!")
    
    print("\nTabelas disponíveis:")
    tables = get_table_names()
    for table in tables:
        print(f"- {table}") 