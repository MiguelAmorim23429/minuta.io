"""Testes ponta-a-ponta através do protocolo JSON-RPC (como a interface usa o motor)."""

import json

import pytest
from conftest import docx_text, make_docx

from minuta_engine import tools
from minuta_engine.errors import APP_ERROR
from minuta_engine.main import handle_line
from minuta_engine.templates import library


def rpc(method, **params):
    response = handle_line(
        json.dumps({"jsonrpc": "2.0", "id": 1, "method": method, "params": params})
    )
    return response


def ok(method, **params):
    response = rpc(method, **params)
    assert "result" in response, response
    return response["result"]


@pytest.fixture
def source(tmp_path):
    return make_docx(
        tmp_path / "Compra e venda.docx",
        [["Pelo preço de ", "*?????", "*?????", ", vende a {{ comprador_1_nome }}."]],
    )


def test_import_copies_file_and_keeps_original(source):
    original = source.read_bytes()

    info = ok("templates.import", path=str(source))

    assert info["name"] == "Compra e venda"
    assert info["status"] == "needs_attention"
    assert info["marker_count"] == 1
    assert library.template_file(info["id"]).read_bytes() == original
    assert source.read_bytes() == original
    assert [t["id"] for t in ok("templates.list")] == [info["id"]]


def test_import_rejects_non_docx(tmp_path):
    fake = tmp_path / "minuta.doc"
    fake.write_bytes(b"nao e docx")
    assert rpc("templates.import", path=str(fake))["error"]["code"] == APP_ERROR

    fake_docx = tmp_path / "minuta.docx"
    fake_docx.write_bytes(b"nao e docx")
    assert rpc("templates.import", path=str(fake_docx))["error"]["code"] == APP_ERROR


def test_convert_then_generate(source, tmp_path):
    original = source.read_bytes()
    template_id = ok("templates.import", path=str(source))["id"]
    marker = ok("templates.scan", id=template_id)["markers"][0]

    scan = ok(
        "templates.convert_markers",
        id=template_id,
        assignments=[{"marker_id": marker["id"], "field": "preco"}],
    )
    assert scan["template"]["status"] == "ready"
    assert source.read_bytes() == original  # o original da utilizadora não muda

    fields = ok("templates.fields", id=template_id)
    assert [f["key"] for f in fields] == ["comprador_1_nome", "preco"]

    out = tmp_path / "saida"
    out.mkdir()
    values = {"preco": "€ 100.000,00", "comprador_1_nome": "Ana Teste"}
    first = ok(
        "documents.generate",
        template_id=template_id,
        values=values,
        output_dir=str(out),
        file_name="Escritura Teste",
    )
    second = ok(
        "documents.generate",
        template_id=template_id,
        values=values,
        output_dir=str(out),
        file_name="Escritura Teste.docx",
    )

    assert first["docx_path"].endswith("Escritura Teste.docx")
    assert second["docx_path"].endswith("Escritura Teste (2).docx")
    assert "Pelo preço de € 100.000,00, vende a Ana Teste." in docx_text(
        out / "Escritura Teste.docx"
    )
    assert first["pdf_path"] is None
    assert sorted(p.name for p in out.iterdir()) == [
        "Escritura Teste (2).docx",
        "Escritura Teste.docx",
    ]


def test_generate_requires_every_field(source, tmp_path):
    template_id = ok("templates.import", path=str(source))["id"]
    response = rpc(
        "documents.generate",
        template_id=template_id,
        values={},
        output_dir=str(tmp_path),
        file_name="x",
    )
    assert response["error"]["code"] == APP_ERROR
    assert "Faltam 1" in response["error"]["message"]


def test_generate_refuses_library_folder(source):
    template_id = ok("templates.import", path=str(source))["id"]
    response = rpc(
        "documents.generate",
        template_id=template_id,
        values={"comprador_1_nome": "x"},
        output_dir=str(library.minutas_dir()),
        file_name="x",
    )
    assert response["error"]["code"] == APP_ERROR


def test_open_only_generated_documents(source):
    response = rpc("documents.open", path=str(source))
    assert response["error"]["code"] == APP_ERROR


def test_rename_and_delete(source):
    template_id = ok("templates.import", path=str(source))["id"]

    assert ok("templates.rename", id=template_id, name="  CV   lote  ")["name"] == "CV lote"
    ok("templates.delete", id=template_id)

    assert ok("templates.list") == []
    assert not library.template_file(template_id).exists()
    assert source.exists()


def test_catalog_has_groups():
    groups = ok("fields.catalog")
    assert groups[0]["id"] == "ato"
    assert all(group["fields"] for group in groups)


@pytest.mark.skipif(not tools.word_installed(), reason="Microsoft Word não instalado")
def test_generate_pdf_with_word(tmp_path):
    source = make_docx(tmp_path / "m.docx", [["Preço: {{ preco }}"]])
    template_id = ok("templates.import", path=str(source))["id"]
    out = tmp_path / "saida"
    out.mkdir()

    result = ok(
        "documents.generate",
        template_id=template_id,
        values={"preco": "1"},
        output_dir=str(out),
        file_name="doc",
        pdf=True,
    )

    assert result["pdf_error"] is None
    assert result["pdf_path"].endswith("doc.pdf")
    assert (out / "doc.pdf").read_bytes().startswith(b"%PDF")
