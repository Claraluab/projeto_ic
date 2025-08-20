# config.py

# Configuração do PostgreSQL
DB_CONFIG = {
    'dbname': 'energy_database',
    'user': 'postgres',
    'password': 'Caca2013!',
    'host': 'localhost',
    'port': '5432'
}

# Configurações de Requisição
REQUEST_TIMEOUT = 30  # segundos

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

# Configuração de retry para requisições
from urllib3.util.retry import Retry
RETRY_STRATEGY = Retry(
    total=3,
    backoff_factor=1,
    status_forcelist=[429, 500, 502, 503, 504],
    allowed_methods=["GET"]
)

# Configuração da aplicação Flask
SECRET_KEY = 'sua_chave_secreta_aqui'
DEBUG = True