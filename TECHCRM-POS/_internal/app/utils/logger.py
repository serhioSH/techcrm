# ============================================================
#  app/utils/logger.py
#  Configuracion del sistema de logs
# ============================================================
import logging
import os
from datetime import datetime
from app.utils.paths import LOGS_PATH


def configurar_logger(nombre: str = "pos") -> logging.Logger:
    """Configura y retorna el logger principal de la aplicacion."""
    logger = logging.getLogger(nombre)
    if logger.handlers:
        return logger  # Ya configurado

    logger.setLevel(logging.DEBUG)

    # Handler de archivo
    fecha = datetime.now().strftime("%Y%m%d")
    log_file = os.path.join(LOGS_PATH, f"pos_{fecha}.log")
    fh = logging.FileHandler(log_file, encoding="utf-8")
    fh.setLevel(logging.DEBUG)

    # Handler de consola
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)

    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(module)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)

    logger.addHandler(fh)
    logger.addHandler(ch)
    return logger
