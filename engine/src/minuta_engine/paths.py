"""Localização das pastas de dados da aplicação."""

import os
from pathlib import Path

APP_DIR_NAME = "minuta.io"


def data_dir() -> Path:
    """Pasta de dados local do utilizador (``%LOCALAPPDATA%\\minuta.io``).

    Pode ser substituída com ``MINUTA_DATA_DIR`` (usado nos testes).
    """
    override = os.environ.get("MINUTA_DATA_DIR")
    if override:
        return Path(override)
    base = os.environ.get("LOCALAPPDATA") or str(Path.home() / ".local" / "share")
    return Path(base) / APP_DIR_NAME


def logs_dir() -> Path:
    return data_dir() / "logs"


def tessdata_dir() -> Path:
    """Pasta com os modelos de idioma do Tesseract usados pela aplicação."""
    return data_dir() / "tessdata"
