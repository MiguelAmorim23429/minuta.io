"""Modelos do domínio "sistema": ping e diagnóstico do ambiente."""

from enum import StrEnum

from pydantic import BaseModel


class PingResult(BaseModel):
    pong: bool
    version: str


class CheckStatus(StrEnum):
    OK = "ok"
    WARNING = "warning"
    ERROR = "error"


class Check(BaseModel):
    """Resultado de uma verificação do ambiente, pronto a mostrar ao utilizador."""

    id: str
    label: str
    status: CheckStatus
    detail: str


class Diagnostics(BaseModel):
    engine_version: str
    python_version: str
    checks: list[Check]
