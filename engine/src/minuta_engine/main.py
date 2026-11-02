"""Ciclo JSON-RPC 2.0 sobre stdin/stdout.

Protocolo: uma mensagem JSON por linha, em UTF-8. Cada pedido tem ``id``, ``method`` e
``params`` (objeto). O ciclo termina quando o stdin fecha, o que acontece automaticamente
se a aplicação Tauri terminar.
"""

import json
import sys
import time
from collections.abc import Callable
from typing import Any, TextIO

from pydantic import BaseModel, ValidationError

from minuta_engine.errors import (
    APP_ERROR,
    INTERNAL_ERROR,
    INVALID_PARAMS,
    INVALID_REQUEST,
    METHOD_NOT_FOUND,
    PARSE_ERROR,
    RpcError,
    UserError,
)
from minuta_engine.logging import get_logger
from minuta_engine.rpc import documents, system, templates

Handler = Callable[[dict[str, Any]], Any]

METHODS: dict[str, Handler] = {
    "system.ping": system.ping,
    "system.diagnostics": system.diagnostics,
    "fields.catalog": templates.catalog,
    "templates.list": templates.list_templates,
    "templates.import": templates.import_template,
    "templates.rename": templates.rename_template,
    "templates.delete": templates.delete_template,
    "templates.scan": templates.scan_template,
    "templates.open": templates.open_template,
    "templates.convert_markers": templates.convert_markers,
    "templates.fields": templates.template_fields,
    "documents.generate": documents.generate,
    "documents.open": documents.open_document,
    "documents.reveal": documents.reveal_document,
}

__all__ = [
    "INTERNAL_ERROR",
    "INVALID_PARAMS",
    "INVALID_REQUEST",
    "METHOD_NOT_FOUND",
    "PARSE_ERROR",
    "handle_line",
    "serve",
]


def _error(request_id: Any, code: int, message: str) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "id": request_id, "error": {"code": code, "message": message}}


def _to_json(value: Any) -> Any:
    if isinstance(value, BaseModel):
        return value.model_dump(mode="json")
    if isinstance(value, list | tuple):
        return [_to_json(item) for item in value]
    return value


def handle_line(line: str) -> dict[str, Any] | None:
    """Processa uma linha do protocolo e devolve a resposta (ou ``None`` para notificações)."""
    log = get_logger()
    try:
        # Alguns emissores (ex.: PowerShell) acrescentam um BOM UTF-8 no início.
        message = json.loads(line.lstrip("﻿"))
    except json.JSONDecodeError:
        log.warning("rpc parse_error")
        return _error(None, PARSE_ERROR, "Mensagem inválida.")

    if not isinstance(message, dict) or not isinstance(message.get("method"), str):
        return _error(None, INVALID_REQUEST, "Pedido inválido.")

    request_id = message.get("id")
    method = message["method"]
    params = message.get("params") or {}
    if not isinstance(params, dict):
        return _error(request_id, INVALID_PARAMS, "Os parâmetros têm de ser um objeto.")

    handler = METHODS.get(method)
    if handler is None:
        log.warning("rpc method_not_found method=%s", method)
        return _error(request_id, METHOD_NOT_FOUND, f"Método desconhecido: {method}")

    started = time.perf_counter()
    try:
        result = _to_json(handler(params))
    except RpcError as exc:
        log.info("rpc error method=%s code=%s", method, exc.code)
        return _error(request_id, exc.code, exc.message)
    except UserError as exc:
        log.info("rpc user_error method=%s", method)
        return _error(request_id, APP_ERROR, exc.message)
    except ValidationError:
        log.info("rpc invalid_params method=%s", method)
        return _error(request_id, INVALID_PARAMS, "Parâmetros inválidos.")
    except Exception as exc:  # noqa: BLE001 — o motor nunca deve terminar por um pedido.
        log.error("rpc internal_error method=%s type=%s", method, type(exc).__name__)
        return _error(request_id, INTERNAL_ERROR, "Erro interno do motor.")

    elapsed_ms = (time.perf_counter() - started) * 1000
    log.info("rpc ok method=%s ms=%.0f", method, elapsed_ms)

    if request_id is None:
        return None
    return {"jsonrpc": "2.0", "id": request_id, "result": result}


def serve(stdin: TextIO | None = None, stdout: TextIO | None = None) -> None:
    """Lê pedidos do stdin até ao fim do ficheiro e escreve as respostas no stdout."""
    if stdin is None:
        sys.stdin.reconfigure(encoding="utf-8")
        stdin = sys.stdin
    if stdout is None:
        sys.stdout.reconfigure(encoding="utf-8")
        stdout = sys.stdout
        # Qualquer print() acidental vai para o stderr e não corrompe o protocolo.
        sys.stdout = sys.stderr

    log = get_logger()
    log.info("engine start")
    for line in stdin:
        if not line.strip():
            continue
        response = handle_line(line)
        if response is not None:
            stdout.write(json.dumps(response, ensure_ascii=False) + "\n")
            stdout.flush()
    log.info("engine stop")
