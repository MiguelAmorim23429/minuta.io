"""Análise de uma minuta: campos ``{{ … }}``, marcadores ``???`` e problemas de sintaxe."""

import re
from dataclasses import dataclass, field
from pathlib import Path

from docx import Document
from docx.opc.exceptions import PackageNotFoundError

from minuta_engine.errors import UserError
from minuta_engine.fields.catalog import field_spec, is_valid_field_name
from minuta_engine.models.templates import (
    Issue,
    IssueSeverity,
    Location,
    Marker,
    PlaceholderInfo,
)
from minuta_engine.templates.docx_xml import paragraphs, text_parts

MARKER_RE = re.compile(r"\?{3,}")
PLACEHOLDER_RE = re.compile(r"\{\{(.*?)\}\}")
# Sintaxe Jinja que o docxtpl interpretaria e que não usamos nas minutas.
JINJA_BLOCK_RE = re.compile(r"\{%|%\}|\{#|#\}")
CONTEXT_CHARS = 70


@dataclass
class ScanResult:
    placeholders: list[PlaceholderInfo] = field(default_factory=list)
    markers: list[Marker] = field(default_factory=list)
    issues: list[Issue] = field(default_factory=list)

    @property
    def error_count(self) -> int:
        return sum(1 for issue in self.issues if issue.severity == IssueSeverity.ERROR)


def marker_id(part_name: str, paragraph_index: int, start: int) -> str:
    """Identificador estável de um marcador enquanto a minuta não for alterada."""
    return f"{part_name}#{paragraph_index}#{start}"


def open_docx(path: Path):
    try:
        return Document(str(path))
    except (PackageNotFoundError, KeyError, ValueError) as exc:
        raise UserError("O ficheiro não é um documento Word (.docx) válido.") from exc


def scan_document(path: Path) -> ScanResult:
    document = open_docx(path)
    result = ScanResult()
    stats: dict[str, dict] = {}

    for part in text_parts(document):
        for paragraph in paragraphs(part.element):
            text = paragraph.text
            if not text:
                continue
            location = Location(part=part.label, paragraph=paragraph.index)

            for match in PLACEHOLDER_RE.finditer(text):
                name = match.group(1).strip()
                context = _excerpt(text, match.start(), match.end())
                if not is_valid_field_name(name):
                    result.issues.append(
                        Issue(
                            severity=IssueSeverity.ERROR,
                            message=(
                                f"Nome de campo inválido: “{name}”. Use só letras minúsculas "
                                "sem acentos, algarismos e _ (ex.: comprador_1_nome)."
                            ),
                            location=location,
                            context=context,
                        )
                    )
                    continue
                if not part.editable:
                    result.issues.append(
                        Issue(
                            severity=IssueSeverity.ERROR,
                            message=f"O campo “{name}” está numa parte que não é preenchida "
                            f"({part.label}). Mova-o para o corpo do documento.",
                            location=location,
                            context=context,
                        )
                    )
                    continue
                entry = stats.setdefault(
                    name, {"occurrences": 0, "parts": [], "appearance": len(stats)}
                )
                entry["occurrences"] += 1
                if part.label not in entry["parts"]:
                    entry["parts"].append(part.label)

            leftover = PLACEHOLDER_RE.sub("", text)
            if "{{" in leftover or "}}" in leftover:
                position = max(leftover.find("{{"), leftover.find("}}"))
                result.issues.append(
                    Issue(
                        severity=IssueSeverity.ERROR,
                        message="Campo incompleto: falta abrir ou fechar as chavetas {{ }}.",
                        location=location,
                        context=_excerpt(leftover, position, position + 2),
                    )
                )
            jinja = JINJA_BLOCK_RE.search(text)
            if jinja:
                result.issues.append(
                    Issue(
                        severity=IssueSeverity.ERROR,
                        message="O texto contém {% … %} ou {# … #}, que não são suportados.",
                        location=location,
                        context=_excerpt(text, jinja.start(), jinja.end()),
                    )
                )

            for match in MARKER_RE.finditer(text):
                result.markers.append(
                    Marker(
                        id=marker_id(part.name, paragraph.index, match.start()),
                        location=location,
                        length=match.end() - match.start(),
                        before=text[max(0, match.start() - CONTEXT_CHARS) : match.start()],
                        after=text[match.end() : match.end() + CONTEXT_CHARS],
                        convertible=part.editable,
                    )
                )

    result.placeholders = sorted(
        (
            PlaceholderInfo(
                field=field_spec(name, fallback_order=10_000 + entry["appearance"]),
                occurrences=entry["occurrences"],
                parts=entry["parts"],
            )
            for name, entry in stats.items()
        ),
        key=lambda info: info.field.order,
    )

    if result.markers:
        result.issues.append(
            Issue(
                severity=IssueSeverity.WARNING,
                message=f"Há {len(result.markers)} espaço(s) marcado(s) com ??? por converter "
                "em campos.",
            )
        )
    if not result.placeholders and not result.markers:
        result.issues.append(
            Issue(
                severity=IssueSeverity.WARNING,
                message="A minuta não tem campos {{ … }} nem espaços marcados com ???.",
            )
        )
    return result


def placeholder_names(path: Path) -> list[str]:
    return [info.field.key for info in scan_document(path).placeholders]


def has_unfilled_placeholders(path: Path) -> bool:
    """Verificação final de um documento gerado: não pode restar nenhum ``{{ … }}``."""
    document = open_docx(path)
    for part in text_parts(document):
        if not part.editable:
            continue
        for paragraph in paragraphs(part.element):
            if PLACEHOLDER_RE.search(paragraph.text):
                return True
    return False


def _excerpt(text: str, start: int, end: int) -> str:
    prefix = "…" if start > CONTEXT_CHARS else ""
    suffix = "…" if end + CONTEXT_CHARS < len(text) else ""
    return prefix + text[max(0, start - CONTEXT_CHARS) : end + CONTEXT_CHARS] + suffix
