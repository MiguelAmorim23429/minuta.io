"""Métodos ``system.*``: verificação de que o motor responde e diagnóstico do ambiente."""

import platform
from typing import Any

from minuta_engine import __version__, tools
from minuta_engine.models.system import Check, CheckStatus, Diagnostics, PingResult


def ping(_params: dict[str, Any]) -> PingResult:
    return PingResult(pong=True, version=__version__)


def diagnostics(_params: dict[str, Any]) -> Diagnostics:
    return Diagnostics(
        engine_version=__version__,
        python_version=platform.python_version(),
        checks=[*_ocr_checks(), _word_check()],
    )


def _ocr_checks() -> list[Check]:
    executable = tools.find_tesseract()
    if executable is None:
        return [
            Check(
                id="tesseract",
                label="Tesseract OCR",
                status=CheckStatus.ERROR,
                detail="Não encontrado. Sem ele não é possível ler documentos digitalizados.",
            )
        ]

    version = tools.tesseract_version(executable) or "versão desconhecida"
    languages = tools.tesseract_languages(executable)
    has_portuguese = "por" in languages
    return [
        Check(id="tesseract", label="Tesseract OCR", status=CheckStatus.OK, detail=version),
        Check(
            id="tesseract_por",
            label="OCR em português",
            status=CheckStatus.OK if has_portuguese else CheckStatus.ERROR,
            detail=(
                "Modelo de português disponível."
                if has_portuguese
                else "Falta o modelo de português (por.traineddata) na pasta de dados."
            ),
        ),
    ]


def _word_check() -> Check:
    if tools.word_installed():
        return Check(
            id="word",
            label="Microsoft Word",
            status=CheckStatus.OK,
            detail="Disponível para exportar PDF.",
        )
    return Check(
        id="word",
        label="Microsoft Word",
        status=CheckStatus.WARNING,
        detail="Não encontrado. A exportação para PDF não estará disponível.",
    )
