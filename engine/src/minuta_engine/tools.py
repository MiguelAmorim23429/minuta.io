"""Localização das ferramentas externas usadas pelo motor (Tesseract, Microsoft Word)."""

import os
import shutil
import subprocess
import sys
from pathlib import Path

from minuta_engine.paths import tessdata_dir

_DEFAULT_TESSERACT = Path(r"C:\Program Files\Tesseract-OCR\tesseract.exe")

# Evita abrir uma janela de consola ao executar ferramentas a partir da aplicação.
_NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)


def find_tesseract() -> Path | None:
    """Caminho do executável do Tesseract.

    Ordem: variável ``MINUTA_TESSERACT``, instalação por defeito, ``PATH``.
    """
    override = os.environ.get("MINUTA_TESSERACT")
    if override:
        path = Path(override)
        return path if path.is_file() else None
    if _DEFAULT_TESSERACT.is_file():
        return _DEFAULT_TESSERACT
    found = shutil.which("tesseract")
    return Path(found) if found else None


def tesseract_version(executable: Path) -> str | None:
    try:
        completed = subprocess.run(
            [str(executable), "--version"],
            capture_output=True,
            text=True,
            timeout=15,
            creationflags=_NO_WINDOW,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    output = (completed.stdout or completed.stderr).strip().splitlines()
    return output[0] if output else None


def tesseract_languages(executable: Path) -> list[str]:
    """Idiomas disponíveis na pasta de modelos da aplicação."""
    try:
        completed = subprocess.run(
            [str(executable), "--tessdata-dir", str(tessdata_dir()), "--list-langs"],
            capture_output=True,
            text=True,
            timeout=15,
            creationflags=_NO_WINDOW,
        )
    except (OSError, subprocess.TimeoutExpired):
        return []
    lines = completed.stdout.strip().splitlines()
    # A primeira linha é o cabeçalho "List of available languages ...".
    return [line.strip() for line in lines[1:] if line.strip()]


def word_installed() -> bool:
    """Indica se o Microsoft Word está registado para automação (necessário para PDF)."""
    if sys.platform != "win32":
        return False
    import winreg

    try:
        with winreg.OpenKey(winreg.HKEY_CLASSES_ROOT, r"Word.Application\CurVer"):
            return True
    except OSError:
        return False
