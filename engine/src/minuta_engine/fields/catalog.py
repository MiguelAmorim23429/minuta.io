"""Leitura do catálogo de campos (``catalog.yaml``)."""

import re
from functools import lru_cache
from importlib import resources

import yaml

from minuta_engine.models.templates import FieldGroup, FieldSpec, FieldType

OTHER_GROUP_ID = "outros"
OTHER_GROUP_LABEL = "Outros campos"

FIELD_NAME_RE = re.compile(r"^[a-z][a-z0-9_]*$")


@lru_cache(maxsize=1)
def load_catalog() -> tuple[FieldGroup, ...]:
    raw = yaml.safe_load(
        resources.files(__package__).joinpath("catalog.yaml").read_text(encoding="utf-8")
    )
    groups: list[FieldGroup] = []
    order = 0
    for group in raw["groups"]:
        fields: list[FieldSpec] = []
        for field in group["fields"]:
            fields.append(
                FieldSpec(
                    key=field["key"],
                    label=field["label"],
                    type=FieldType(field.get("type", "text")),
                    group_id=group["id"],
                    group_label=group["label"],
                    known=True,
                    order=order,
                )
            )
            order += 1
        groups.append(FieldGroup(id=group["id"], label=group["label"], fields=fields))
    return tuple(groups)


@lru_cache(maxsize=1)
def _by_key() -> dict[str, FieldSpec]:
    return {field.key: field for group in load_catalog() for field in group.fields}


def field_spec(key: str, fallback_order: int = 10_000) -> FieldSpec:
    """Especificação de um campo; campos fora do catálogo ficam no grupo "Outros campos"."""
    known = _by_key().get(key)
    if known is not None:
        return known
    return FieldSpec(
        key=key,
        label=key.replace("_", " ").capitalize(),
        type=FieldType.TEXT,
        group_id=OTHER_GROUP_ID,
        group_label=OTHER_GROUP_LABEL,
        known=False,
        order=fallback_order,
    )


def is_valid_field_name(name: str) -> bool:
    return bool(FIELD_NAME_RE.fullmatch(name))
