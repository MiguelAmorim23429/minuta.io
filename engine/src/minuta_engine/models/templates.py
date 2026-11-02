"""Modelos do domínio "minutas": biblioteca, análise, campos e geração."""

from enum import StrEnum

from pydantic import BaseModel, Field


class FieldType(StrEnum):
    TEXT = "text"
    MULTILINE = "multiline"
    NIF = "nif"
    MONEY = "money"
    DATE = "date"


class FieldSpec(BaseModel):
    key: str
    label: str
    type: FieldType
    group_id: str
    group_label: str
    known: bool  # False quando o placeholder não consta do catálogo
    order: int


class FieldGroup(BaseModel):
    id: str
    label: str
    fields: list[FieldSpec]


class TemplateStatus(StrEnum):
    READY = "ready"  # pronta a preencher
    NEEDS_ATTENTION = "needs_attention"  # tem marcadores por converter ou erros
    MISSING = "missing"  # o ficheiro guardado desapareceu


class TemplateInfo(BaseModel):
    id: str
    name: str
    imported_at: str
    updated_at: str
    status: TemplateStatus
    placeholder_count: int
    marker_count: int
    error_count: int


class IssueSeverity(StrEnum):
    ERROR = "error"
    WARNING = "warning"


class Location(BaseModel):
    part: str  # "Corpo do documento", "Cabeçalho", …
    paragraph: int  # índice do parágrafo dentro da parte (a partir de 1)


class Issue(BaseModel):
    severity: IssueSeverity
    message: str
    location: Location | None = None
    context: str = ""


class PlaceholderInfo(BaseModel):
    field: FieldSpec
    occurrences: int
    parts: list[str]


class Marker(BaseModel):
    """Sequência de ``???`` que marca um espaço a preencher e pode ser convertida num campo."""

    id: str
    location: Location
    length: int
    before: str  # texto do parágrafo antes do marcador (excerto)
    after: str  # texto do parágrafo depois do marcador (excerto)
    convertible: bool  # False em partes que a aplicação não altera (ex.: notas de rodapé)


class TemplateScan(BaseModel):
    template: TemplateInfo
    placeholders: list[PlaceholderInfo]
    markers: list[Marker]
    issues: list[Issue]


class GenerateResult(BaseModel):
    docx_path: str
    pdf_path: str | None = None
    pdf_error: str | None = None


# Parâmetros dos métodos RPC ---------------------------------------------------------------


class TemplateIdParams(BaseModel):
    id: str


class ImportParams(BaseModel):
    path: str
    name: str | None = None


class RenameParams(BaseModel):
    id: str
    name: str


class MarkerAssignment(BaseModel):
    marker_id: str
    field: str


class ConvertParams(BaseModel):
    id: str
    assignments: list[MarkerAssignment] = Field(min_length=1)


class GenerateParams(BaseModel):
    template_id: str
    values: dict[str, str]
    output_dir: str
    file_name: str
    pdf: bool = False


class PathParams(BaseModel):
    path: str
