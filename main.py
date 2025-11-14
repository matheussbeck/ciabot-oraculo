#!/usr/bin/env python3
"""
CIABot Oráculo - Sistema de Inteligência Agrícola
Ponto de entrada principal
"""
import sys
import logging
from pathlib import Path

# Adiciona diretório raiz ao path
sys.path.insert(0, str(Path(__file__).parent))

from src.utils.logger import setup_logger
from src.bot.telegram_bot import TelegramBot


def main():
    """Função principal"""
    # Configura logging
    logger = setup_logger()
    logger.info("="*50)
    logger.info("CIABot Oráculo - Iniciando sistema")
    logger.info("="*50)

    try:
        # Inicializa e executa bot
        bot = TelegramBot()
        bot.run()

    except KeyboardInterrupt:
        logger.info("Bot encerrado pelo usuário")
        sys.exit(0)

    except Exception as e:
        logger.error(f"Erro fatal: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
