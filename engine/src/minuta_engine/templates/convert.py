"""Conversão de marcadores ``???`` em campos ``{{ nome }}``.

Só é alterado o marcador; o texto à volta, a formatação e a estrutura ficam iguais. O campo
herda a formatação do primeiro run onde o marcador começava.
"""

import os
from pathlib import Path

from minuta_engine.errors import UserError
from minuta_engine.fields.catalog import is_valid_field_name
from minuta_engine.templates.docx_xml import paragraphs, replace_span, text_parts
from minuta_engine.templates.scan import MARKER_RE, marker_id, open_docx


def convert_markers(path: Path, assignments: dict[str, str]) -> int:
    """Substitui cada marcador indicado (``marker_id → nome do campo``) e grava o ficheiro.

    Devolve o número de marcadores convertidos. Se algum marcador já não existir (a minuta
    mudou desde a análise), nada é gravado.
    """
    for name in assignments.values():
        if not is_valid_field_name(name):
            raise UserError(
                f"Nome de campo inválido: “{name}”. Use só letras minúsculas sem acentos, "
                "algarismos e _."
            )

    document = open_docx(path)
    converted: set[str] = set()
    for part in text_parts(document):
        if not part.editable:
            continue
        for paragraph in paragraphs(part.element):
            spans = [(m.start(), m.end()) for m in MARKER_RE.finditer(paragraph.text)]
            # Do fim para o início, para os índices dos marcadores anteriores não mudarem.
            for start, end in reversed(spans):
                identifier = marker_id(part.name, paragraph.index, start)
                name = assignments.get(identifier)
                if name is None:
                    continue
                replace_span(paragraph, start, end, "{{ " + name + " }}")
                converted.add(identifier)

    if converted != set(assignments):
        raise UserError("A minuta mudou desde a última análise. Volte a abri-la e tente de novo.")

    temporary = path.with_name(path.stem + ".tmp.docx")
    try:
        document.save(str(temporary))
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)
    return len(converted)
