"""Preenchimento de uma minuta com docxtpl.

Regras de segurança:
- todos os campos têm de ter valor (``StrictUndefined``); campos deixados em branco de
  propósito chegam como texto vazio;
- os valores são escapados (``autoescape``), por isso ``&``, ``<`` e aspas são seguros;
- valores com várias linhas são inseridos com quebras de linha do Word.
"""

from pathlib import Path

from docxtpl import DocxTemplate, Listing
from jinja2 import Environment, StrictUndefined, TemplateError, UndefinedError

from minuta_engine.errors import UserError


def render_template(template: Path, values: dict[str, str], destination: Path) -> None:
    document = DocxTemplate(str(template))
    environment = Environment(undefined=StrictUndefined, autoescape=True)
    context = {key: _prepare(value) for key, value in values.items()}
    try:
        document.render(context, jinja_env=environment, autoescape=True)
    except UndefinedError as exc:
        raise UserError("Falta preencher um ou mais campos da minuta.") from exc
    except TemplateError as exc:
        raise UserError(
            "A minuta tem campos mal escritos. Abra-a na biblioteca para ver os problemas."
        ) from exc
    document.save(str(destination))


def _prepare(value: str) -> str | Listing:
    normalized = value.replace("\r\n", "\n").replace("\r", "\n")
    return Listing(normalized) if "\n" in normalized else normalized
