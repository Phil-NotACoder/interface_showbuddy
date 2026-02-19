import logging
import os

_configured = False

def _configure_root_logger():
    global _configured
    if _configured:
        return
    level_name = os.getenv('LOG_LEVEL', 'INFO').upper()
    level = getattr(logging, level_name, logging.INFO)
    fmt = '%(asctime)s | %(levelname)s | %(name)s | %(message)s'
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter(fmt))
    root = logging.getLogger()
    root.setLevel(level)
    root.addHandler(handler)
    _configured = True

def get_logger(name: str) -> logging.Logger:
    _configure_root_logger()
    return logging.getLogger(name)