"""
Configurações do sistema CIABot Oráculo
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Carrega variáveis de ambiente
load_dotenv()

# Diretórios base
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
PARQUET_DIR = DATA_DIR / "parquet"
TEMP_DIR = DATA_DIR / "temp"
REPORTS_DIR = DATA_DIR / "reports"
POWERBI_REPORTS_DIR = DATA_DIR / "powerbi_reports"  # Relatórios Power BI prontos
LOGS_DIR = BASE_DIR / "logs"

# Criar diretórios se não existirem
for directory in [DATA_DIR, PARQUET_DIR, TEMP_DIR, REPORTS_DIR, POWERBI_REPORTS_DIR, LOGS_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

# Configurações do Telegram
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
ALLOWED_USER_IDS = [int(uid) for uid in os.getenv("ALLOWED_USER_IDS", "").split(",") if uid.strip()]

# Configurações da IA
AI_PROVIDER = os.getenv("AI_PROVIDER", "anthropic")  # anthropic, openai
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
AI_MODEL = os.getenv("AI_MODEL", "claude-3-5-sonnet-20241022")

# Configurações de confiança
CONFIDENCE_THRESHOLD = float(os.getenv("CONFIDENCE_THRESHOLD", "0.90"))  # 90%
MIN_CONFIDENCE_TO_RESPOND = float(os.getenv("MIN_CONFIDENCE_TO_RESPOND", "0.90"))

# Configurações de embeddings
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
VECTOR_DB_PATH = DATA_DIR / "vector_db"
VECTOR_DB_PATH.mkdir(parents=True, exist_ok=True)

# Configurações de logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FILE = LOGS_DIR / "ciabot.log"

# Configurações de safra
SAFRA_INICIO = os.getenv("SAFRA_INICIO", "2024-04-01")  # Data início da safra

# Configurações de processamento
MAX_CONTEXT_TOKENS = int(os.getenv("MAX_CONTEXT_TOKENS", "100000"))
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "1000"))

# Unidades da operação
UNIDADES = [
    "Barra",
    "Piacatu",
    "Univalem",
    "São José",
    # Adicionar outras unidades conforme necessário
]

# Operações disponíveis
OPERACOES = [
    "plantio",
    "corte",
    "carregamento",
    "transporte",
]
