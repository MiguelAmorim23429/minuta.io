"""Métodos ``documents.*``: gerar o documento preenchido, exportar PDF e abri-lo."""

import os
import re
import subprocess
import sys
import uuid
from pathlib import Path
from typing import Any

from minuta_engine.errors import UserError
from minuta_engine.export.pdf import PdfExportError, export_pdf
from minuta_engine.models.templates import GenerateParams, GenerateResult, PathParams
from minuta_engine.templates import library
from minuta_engine.templates.render import render_template
from minuta_engine.templates.scan import has_unfilled_placeholders, placeholder_names

MAX_FILE_NAME = 150
_INVALID_FILE_CHARS = re.compile(r'[<>:"/\\|?*\x00-\x1f]')

# Documentos gerados nesta sessão: só estes podem ser abertos a pedido da interface.
_generated: set[str] = set()


def generate(params: dict[str, Any]) -> GenerateResult:
    p = GenerateParams.model_validate(params)
    template = library.path_for(p.template_id)

    names = placeholder_names(template)
    missing = [name for name in names if name not in p.values]
    if missing:
        raise UserError(f"Faltam {len(missing)} campo(s) por preencher ou marcar como em branco.")
    values = {name: p.values[name] for name in names}

    output_dir = Path(p.output_dir)
    if not output_dir.is_dir():
        raise UserError("A pasta de destino não existe.")
    if _is_within(output_dir, library.minutas_dir()):
        raise UserError("Escolha uma pasta de destino fora da biblioteca de minutas.")

    docx_path = _unique_path(output_dir, _clean_file_name(p.file_name), ".docx")
    temporary = output_dir / f".~minuta-{uuid.uuid4().hex}.docx"
    try:
        render_template(template, values, temporary)
        if has_unfilled_placeholders(temporary):
            raise UserError("O documento gerado ainda tem campos por preencher.")
        os.replace(temporary, docx_path)
    finally:
        temporary.unlink(missing_ok=True)
    _remember(docx_path)

    result = GenerateResult(docx_path=str(docx_path))
    if p.pdf:
        pdf_path = _unique_path(output_dir, docx_path.stem, ".pdf")
        try:
            export_pdf(docx_path, pdf_path)
        except PdfExportError as exc:
            result.pdf_error = exc.message
        else:
            _remember(pdf_path)
            result.pdf_path = str(pdf_path)
    return result


def open_document(params: dict[str, Any]) -> dict[str, bool]:
    """Abre um documento gerado com a aplicação predefinida (Word, leitor de PDF)."""
    path = _generated_path(PathParams.model_validate(params).path)
    if sys.platform == "win32":
        os.startfile(path)  # noqa: S606 — caminho validado: só documentos gerados nesta sessão
    return {"opened": True}


def reveal_document(params: dict[str, Any]) -> dict[str, bool]:
    """Abre o Explorador do Windows com o documento gerado selecionado."""
    path = _generated_path(PathParams.model_validate(params).path)
    if sys.platform == "win32":
        subprocess.Popen(["explorer", f"/select,{path}"])  # noqa: S603, S607
    return {"opened": True}


def _clean_file_name(name: str) -> str:
    cleaned = _INVALID_FILE_CHARS.sub("", name).strip().rstrip(". ")
    if cleaned.lower().endswith(".docx"):
        cleaned = cleaned[: -len(".docx")].rstrip(". ")
    cleaned = cleaned[:MAX_FILE_NAME]
    if not cleaned:
        raise UserError("Indique um nome para o ficheiro.")
    return cleaned


def _unique_path(directory: Path, stem: str, suffix: str) -> Path:
    candidate = directory / f"{stem}{suffix}"
    counter = 2
    while candidate.exists():
        candidate = directory / f"{stem} ({counter}){suffix}"
        counter += 1
    return candidate


def _is_within(path: Path, parent: Path) -> bool:
    try:
        path.resolve().relative_to(parent.resolve())
    except ValueError:
        return False
    return True


def _key(path: Path) -> str:
    return os.path.normcase(str(path.resolve()))


def _remember(path: Path) -> None:
    _generated.add(_key(path))


def _generated_path(raw: str) -> Path:
    path = Path(raw)
    if _key(path) not in _generated or not path.is_file():
        raise UserError("Só é possível abrir documentos gerados nesta sessão.")
    return path
