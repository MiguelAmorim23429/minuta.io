import io
import json

import pytest

from minuta_engine import __version__, tools
from minuta_engine.main import (
    INVALID_PARAMS,
    INVALID_REQUEST,
    METHOD_NOT_FOUND,
    PARSE_ERROR,
    handle_line,
    serve,
)


@pytest.fixture(autouse=True)
def _isolated_data_dir(tmp_path, monkeypatch):
    monkeypatch.setenv("MINUTA_DATA_DIR", str(tmp_path))


def _request(method: str, params: object = None, request_id: object = 1) -> str:
    message = {"jsonrpc": "2.0", "id": request_id, "method": method}
    if params is not None:
        message["params"] = params
    return json.dumps(message)


def test_ping():
    response = handle_line(_request("system.ping"))
    assert response == {
        "jsonrpc": "2.0",
        "id": 1,
        "result": {"pong": True, "version": __version__},
    }


def test_parse_error():
    response = handle_line("{isto não é json")
    assert response["error"]["code"] == PARSE_ERROR


def test_invalid_request():
    response = handle_line(json.dumps({"id": 1}))
    assert response["error"]["code"] == INVALID_REQUEST


def test_unknown_method():
    response = handle_line(_request("nao.existe"))
    assert response["id"] == 1
    assert response["error"]["code"] == METHOD_NOT_FOUND


def test_params_must_be_object():
    response = handle_line(_request("system.ping", params=[1, 2]))
    assert response["error"]["code"] == INVALID_PARAMS


def test_notification_has_no_response():
    assert handle_line(_request("system.ping", request_id=None)) is None


def test_diagnostics_without_tools(monkeypatch):
    monkeypatch.setattr(tools, "find_tesseract", lambda: None)
    monkeypatch.setattr(tools, "word_installed", lambda: False)

    result = handle_line(_request("system.diagnostics"))["result"]

    statuses = {check["id"]: check["status"] for check in result["checks"]}
    assert statuses == {"tesseract": "error", "word": "warning"}
    assert result["engine_version"] == __version__


def test_diagnostics_detects_missing_portuguese(monkeypatch, tmp_path):
    fake = tmp_path / "tesseract.exe"
    fake.write_text("")
    monkeypatch.setattr(tools, "find_tesseract", lambda: fake)
    monkeypatch.setattr(tools, "tesseract_version", lambda _exe: "tesseract v5")
    monkeypatch.setattr(tools, "tesseract_languages", lambda _exe: ["eng", "osd"])
    monkeypatch.setattr(tools, "word_installed", lambda: True)

    result = handle_line(_request("system.diagnostics"))["result"]

    statuses = {check["id"]: check["status"] for check in result["checks"]}
    assert statuses == {"tesseract": "ok", "tesseract_por": "error", "word": "ok"}


def test_serve_processes_lines_until_eof():
    stdin = io.StringIO(
        _request("system.ping", request_id=1) + "\n\n" + _request("x", request_id=2)
    )
    stdout = io.StringIO()

    serve(stdin=stdin, stdout=stdout)

    responses = [json.loads(line) for line in stdout.getvalue().splitlines()]
    assert [r["id"] for r in responses] == [1, 2]
    assert "result" in responses[0]
    assert responses[1]["error"]["code"] == METHOD_NOT_FOUND
