#!/usr/bin/env python3
"""
CIABot Oráculo - Servidor da API REST
Ponto de entrada para a API HTTP
"""
import sys
import logging
from pathlib import Path

# Adiciona diretório raiz ao path
sys.path.insert(0, str(Path(__file__).parent))

from src.utils.logger import setup_logger
from src.api.rest_api import CIABotAPI
from config.settings import AI_PROVIDER
import os


def main():
    """Função principal"""
    # Configura logging
    logger = setup_logger()
    logger.info("="*50)
    logger.info("CIABot Oráculo - API REST")
    logger.info("="*50)

    # API Key (pode ser configurada via env)
    api_key = os.getenv("API_KEY", "ciabot-api-key-change-me")

    if api_key == "ciabot-api-key-change-me":
        logger.warning(
            "⚠️  API Key padrão está sendo usada! "
            "Configure API_KEY no .env para produção"
        )

    # Porta
    port = int(os.getenv("API_PORT", "8000"))
    host = os.getenv("API_HOST", "0.0.0.0")

    try:
        # Cria e inicia API
        api = CIABotAPI(api_key=api_key)

        logger.info(f"Iniciando API em {host}:{port}")
        logger.info(f"Documentação disponível em: http://{host}:{port}/docs")
        logger.info(f"API Key: {api_key}")

        api.run(host=host, port=port)

    except KeyboardInterrupt:
        logger.info("API encerrada pelo usuário")
        sys.exit(0)

    except Exception as e:
        logger.error(f"Erro fatal: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
