"""Logs técnicos do motor.

Regra: os logs só contêm nomes de métodos, códigos de erro, contagens e tempos.
Nunca registar valores de campos, nomes de ficheiros, caminhos, excertos de texto nem
mensagens de exceções (podem conter dados pessoais) — apenas o tipo da exceção.
"""

import logging
from logging.handlers import RotatingFileHandler

from minuta_engine.paths import logs_dir

_LOGGER_NAME = "minuta_engine"


def get_logger() -> logging.Logger:
    logger = logging.getLogger(_LOGGER_NAME)
    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)
    logger.propagate = False
    try:
        directory = logs_dir()
        directory.mkdir(parents=True, exist_ok=True)
        handler: logging.Handler = RotatingFileHandler(
            directory / "engine.log", maxBytes=1_000_000, backupCount=3, encoding="utf-8"
        )
    except OSError:
        # Sem pasta de logs disponível: o motor continua a funcionar sem registar.
        handler = logging.NullHandler()
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    logger.addHandler(handler)
    return logger
