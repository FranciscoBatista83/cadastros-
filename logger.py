# logger.py
import logging
from logging.handlers import RotatingFileHandler
import os

def setup_logger():
    """
    Configura o sistema de logs global com rotação de arquivos.
    """
    if not os.path.exists('logs'):
        os.makedirs('logs')

    logger = logging.getLogger('AggerBot')
    logger.setLevel(logging.DEBUG)
    
    # Formato: [data e hora] [nível] [módulo] - mensagem
    log_format = '%(asctime)s [%(levelname)s] [%(module)s] - %(message)s'
    formatter = logging.Formatter(log_format)
    
    # Handler para arquivo com rotação (Máximo 5MB por arquivo, mantém 5 backups)
    file_handler = RotatingFileHandler(
        'logs/bot_debug.log', 
        maxBytes=5*1024*1024, 
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setFormatter(formatter)
    
    # Handler para console
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    
    # Adiciona handlers ao logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

# Inicializa o logger
logger = setup_logger()