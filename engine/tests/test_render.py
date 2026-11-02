import hashlib

import pytest
from conftest import docx_text, make_docx
from docx import Document

from minuta_engine.errors import UserError
from minuta_engine.templates.render import render_template


def test_fills_body_and_header_without_touching_template(tmp_path):
    template = make_docx(
        tmp_path / "m.docx",
        [["Vende a ", "*{{ comprador_1_nome }}", ", NIF {{ comprador_1_nif }}."]],
        header=["Livro: {{ livro }}"],
    )
    before = hashlib.sha256(template.read_bytes()).hexdigest()
    output = tmp_path / "out.docx"

    render_template(
        template,
        {"comprador_1_nome": "Ana Teste", "comprador_1_nif": "123456789", "livro": "12"},
        output,
    )

    text = docx_text(output)
    assert "Vende a Ana Teste, NIF 123456789." in text
    assert "Livro: 12" in text
    assert hashlib.sha256(template.read_bytes()).hexdigest() == before
    bold_run = next(r for r in Document(str(output)).paragraphs[0].runs if "Ana" in r.text)
    assert bold_run.bold is True


def test_escapes_special_characters(tmp_path):
    template = make_docx(tmp_path / "m.docx", [["Mediadora: {{ mediadora }}"]])
    output = tmp_path / "out.docx"

    render_template(template, {"mediadora": 'A & B <Lda> "X"'}, output)

    assert 'Mediadora: A & B <Lda> "X"' in docx_text(output)


def test_multiline_value_becomes_line_breaks(tmp_path):
    template = make_docx(tmp_path / "m.docx", [["Morada: {{ comprador_1_morada }}"]])
    output = tmp_path / "out.docx"

    render_template(template, {"comprador_1_morada": "Rua A, 1\r\n4490-000 Póvoa"}, output)

    paragraph = Document(str(output)).paragraphs[0]
    assert "Rua A, 1" in paragraph.text and "4490-000 Póvoa" in paragraph.text
    assert paragraph._p.xml.count("<w:br/>") == 1


def test_missing_value_is_an_error(tmp_path):
    template = make_docx(tmp_path / "m.docx", [["{{ preco }} {{ preco_extenso }}"]])

    with pytest.raises(UserError):
        render_template(template, {"preco": "1"}, tmp_path / "out.docx")


def test_blank_value_is_allowed(tmp_path):
    template = make_docx(tmp_path / "m.docx", [["Cônjuge: {{ comprador_1_conjuge }}."]])
    output = tmp_path / "out.docx"

    render_template(template, {"comprador_1_conjuge": ""}, output)

    assert "Cônjuge: ." in docx_text(output)
