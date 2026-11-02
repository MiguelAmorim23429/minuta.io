"""Métodos ``templates.*`` e ``fields.*``: biblioteca, análise, conversão e campos."""

import os
import sys
from typing import Any

from minuta_engine.fields.catalog import load_catalog
from minuta_engine.models.templates import (
    ConvertParams,
    FieldGroup,
    FieldSpec,
    ImportParams,
    RenameParams,
    TemplateIdParams,
    TemplateInfo,
    TemplateScan,
)
from minuta_engine.templates import convert, library


def catalog(_params: dict[str, Any]) -> list[FieldGroup]:
    return list(load_catalog())


def list_templates(_params: dict[str, Any]) -> list[TemplateInfo]:
    return library.list_templates()


def import_template(params: dict[str, Any]) -> TemplateInfo:
    p = ImportParams.model_validate(params)
    return library.import_template(p.path, p.name)


def rename_template(params: dict[str, Any]) -> TemplateInfo:
    p = RenameParams.model_validate(params)
    return library.rename(p.id, p.name)


def delete_template(params: dict[str, Any]) -> dict[str, bool]:
    p = TemplateIdParams.model_validate(params)
    library.delete(p.id)
    return {"deleted": True}


def scan_template(params: dict[str, Any]) -> TemplateScan:
    p = TemplateIdParams.model_validate(params)
    return _scan(p.id)


def convert_markers(params: dict[str, Any]) -> TemplateScan:
    p = ConvertParams.model_validate(params)
    path = library.path_for(p.id)
    convert.convert_markers(path, {a.marker_id: a.field for a in p.assignments})
    library.mark_modified(p.id)
    return _scan(p.id)


def open_template(params: dict[str, Any]) -> dict[str, bool]:
    """Abre a cópia da minuta guardada na biblioteca no Word, para edição.

    Depois de gravar no Word, a interface volta a pedir a análise (``templates.scan``).
    """
    p = TemplateIdParams.model_validate(params)
    path = library.path_for(p.id)
    if sys.platform == "win32":
        os.startfile(path)  # noqa: S606 — ficheiro interno da biblioteca
    return {"opened": True}


def template_fields(params: dict[str, Any]) -> list[FieldSpec]:
    """Campos a preencher na minuta, pela ordem do catálogo (os desconhecidos no fim)."""
    p = TemplateIdParams.model_validate(params)
    _info, scan = library.describe(p.id)
    return [placeholder.field for placeholder in scan.placeholders]


def _scan(template_id: str) -> TemplateScan:
    library.refresh_if_changed(template_id)
    info, scan = library.describe(template_id)
    return TemplateScan(
        template=info,
        placeholders=scan.placeholders,
        markers=scan.markers,
        issues=scan.issues,
    )
