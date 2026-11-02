"""Utilitários de teste. Todas as minutas são sintéticas e criadas nos próprios testes."""

from pathlib import Path

import pytest
from docx import Document
from docx.shared import Pt


@pytest.fixture(autouse=True)
def isolated_data_dir(tmp_path, monkeypatch) -> Path:
    data = tmp_path / "dados"
    monkeypatch.setenv("MINUTA_DATA_DIR", str(data))
    return data


def make_docx(path: Path, paragraphs: list[list[str]], header: list[str] | None = None) -> Path:
    """Cria um .docx; cada parágrafo é uma lista de runs (simula texto partido pelo Word).

    Runs que começam por ``*`` ficam a negrito (o ``*`` é removido).
    """
    document = Document()
    for runs in paragraphs:
        paragraph = document.add_paragraph()
        for text in runs:
            bold = text.startswith("*")
            run = paragraph.add_run(text[1:] if bold else text)
            run.bold = bold
            run.font.size = Pt(14)
    if header:
        section_header = document.sections[0].header
        section_header.paragraphs[0].text = header[0]
        for text in header[1:]:
            section_header.add_paragraph(text)
    document.save(str(path))
    return path


def docx_text(path: Path) -> str:
    document = Document(str(path))
    body = "\n".join(p.text for p in document.paragraphs)
    header = "\n".join(p.text for p in document.sections[0].header.paragraphs)
    return body + "\n--header--\n" + header
