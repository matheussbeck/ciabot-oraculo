"""
Configuração de logging
"""
import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler

from config.settings import LOG_LEVEL, LOG_FILE


def setup_logger(name: str = None) -> logging.Logger:
    """
    Configura logger para a aplicação

    Args:
        name: Nome do logger (None para root logger)

    Returns:
        Logger configurado
    """
    logger = logging.getLogger(name)

    # Se já está configurado, retorna
    if logger.handlers:
        return logger

    logger.setLevel(LOG_LEVEL)

    # Formato
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Handler para console
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(LOG_LEVEL)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # Handler para arquivo (com rotação)
    file_handler = RotatingFileHandler(
        LOG_FILE,
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    file_handler.setLevel(LOG_LEVEL)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger
