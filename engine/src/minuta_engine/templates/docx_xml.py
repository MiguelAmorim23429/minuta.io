"""Acesso de baixo nível ao texto de um ``.docx``.

O Word guarda o texto de cada parágrafo (``w:p``) repartido por vários segmentos (``w:t``,
dentro de runs ``w:r``) — basta o corretor ortográfico ou uma edição parcial para um
``?????`` ou ``{{ campo }}`` ficar partido em 2 ou 3 segmentos. Este módulo junta o texto
de cada parágrafo e mantém a correspondência com os segmentos, para que a análise e a
conversão trabalhem sobre o texto contínuo sem perder a formatação de cada run.
"""

from collections.abc import Iterator
from dataclasses import dataclass

from docx.document import Document as DocxDocument
from lxml import etree

W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
W_P = f"{{{W_NS}}}p"
W_T = f"{{{W_NS}}}t"
MC_FALLBACK = "{http://schemas.openxmlformats.org/markup-compatibility/2006}Fallback"
XML_SPACE = "{http://www.w3.org/XML/1998/namespace}space"

_CT = "application/vnd.openxmlformats-officedocument.wordprocessingml."
PART_KINDS = {
    _CT + "document.main+xml": "body",
    _CT + "template.main+xml": "body",
    _CT + "header+xml": "header",
    _CT + "footer+xml": "footer",
    _CT + "footnotes+xml": "footnotes",
    _CT + "endnotes+xml": "endnotes",
}
PART_LABELS = {
    "body": "Corpo do documento",
    "header": "Cabeçalho",
    "footer": "Rodapé",
    "footnotes": "Notas de rodapé",
    "endnotes": "Notas finais",
}
# Partes que o docxtpl preenche e que a conversão de marcadores pode alterar.
RENDERED_KINDS = {"body", "header", "footer"}


@dataclass
class TextPart:
    name: str  # nome interno da parte, ex.: "/word/header1.xml"
    kind: str
    element: etree._Element
    editable: bool  # True quando as alterações ao elemento são gravadas com o documento

    @property
    def label(self) -> str:
        return PART_LABELS[self.kind]


@dataclass
class Paragraph:
    index: int  # a partir de 1, dentro da parte
    segments: list[etree._Element]  # elementos w:t, pela ordem do texto

    @property
    def text(self) -> str:
        return "".join(t.text or "" for t in self.segments)


def text_parts(document: DocxDocument) -> list[TextPart]:
    """Partes do documento com texto (corpo, cabeçalhos, rodapés, notas), por ordem estável."""
    parts: list[TextPart] = []
    for part in document.part.package.iter_parts():
        kind = PART_KINDS.get(part.content_type)
        if kind is None:
            continue
        element = getattr(part, "_element", None)
        editable = element is not None and kind in RENDERED_KINDS
        if element is None:
            element = etree.fromstring(part.blob)
        parts.append(TextPart(str(part.partname), kind, element, editable))
    order = {"body": 0, "header": 1, "footer": 2, "footnotes": 3, "endnotes": 4}
    parts.sort(key=lambda p: (order[p.kind], p.name))
    return parts


def paragraphs(root: etree._Element) -> Iterator[Paragraph]:
    """Parágrafos da parte, ignorando a versão alternativa (``mc:Fallback``) de caixas de texto."""
    index = 0
    for p in root.iter(W_P):
        if _inside_fallback(p):
            continue
        index += 1
        segments = [t for t in p.iter(W_T) if _owning_paragraph(t) is p]
        yield Paragraph(index=index, segments=segments)


def replace_span(paragraph: Paragraph, start: int, end: int, replacement: str) -> None:
    """Substitui ``text[start:end]`` do parágrafo por ``replacement``.

    A substituição fica no primeiro segmento abrangido (mantendo a formatação desse run); o
    resto do intervalo é removido dos segmentos seguintes. Texto fora do intervalo não muda.
    """
    position = 0
    inserted = False
    for segment in paragraph.segments:
        text = segment.text or ""
        seg_start, seg_end = position, position + len(text)
        position = seg_end
        if seg_end <= start or seg_start >= end:
            continue
        cut_from = max(start, seg_start) - seg_start
        cut_to = min(end, seg_end) - seg_start
        segment.text = text[:cut_from] + ("" if inserted else replacement) + text[cut_to:]
        segment.set(XML_SPACE, "preserve")
        inserted = True
    if not inserted:
        raise ValueError("intervalo fora do texto do parágrafo")


def _inside_fallback(element: etree._Element) -> bool:
    return any(ancestor.tag == MC_FALLBACK for ancestor in element.iterancestors())


def _owning_paragraph(element: etree._Element) -> etree._Element | None:
    for ancestor in element.iterancestors():
        if ancestor.tag == W_P:
            return ancestor
        if ancestor.tag == MC_FALLBACK:
            return None
    return None
