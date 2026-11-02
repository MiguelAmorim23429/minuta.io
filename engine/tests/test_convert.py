import hashlib

import pytest
from conftest import make_docx
from docx import Document

from minuta_engine.errors import UserError
from minuta_engine.templates.convert import convert_markers
from minuta_engine.templates.scan import scan_document


def _sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_converts_split_marker_keeping_text_and_formatting(tmp_path):
    path = make_docx(
        tmp_path / "m.docx",
        [["pelo preço de ", "*??????", "*????", "*??", " vendem à segunda outorgante"]],
    )
    marker = scan_document(path).markers[0]

    assert convert_markers(path, {marker.id: "preco"}) == 1

    paragraph = Document(str(path)).paragraphs[0]
    assert paragraph.text == "pelo preço de {{ preco }} vendem à segunda outorgante"
    placeholder_run = next(run for run in paragraph.runs if "{{" in run.text)
    assert placeholder_run.bold is True
    assert paragraph.runs[0].text == "pelo preço de "
    assert paragraph.runs[0].bold is not True


def test_converts_several_markers_in_same_paragraph(tmp_path):
    path = make_docx(
        tmp_path / "m.docx",
        [["DUC n.º ?????, no valor de € ?????", "??? ; fim"]],
    )
    markers = scan_document(path).markers
    assert len(markers) == 2

    convert_markers(path, {markers[0].id: "duc_imt_numero", markers[1].id: "duc_imt_valor"})

    text = Document(str(path)).paragraphs[0].text
    assert text == "DUC n.º {{ duc_imt_numero }}, no valor de € {{ duc_imt_valor }} ; fim"
    assert scan_document(path).markers == []


def test_partial_conversion_leaves_other_markers(tmp_path):
    path = make_docx(tmp_path / "m.docx", [["a ????? b"], ["c ????? d"]])
    first, second = scan_document(path).markers

    convert_markers(path, {second.id: "matriz_artigo"})

    result = scan_document(path)
    assert [m.id for m in result.markers] == [first.id]
    assert [p.field.key for p in result.placeholders] == ["matriz_artigo"]


def test_stale_marker_id_changes_nothing(tmp_path):
    path = make_docx(tmp_path / "m.docx", [["a ????? b"]])
    before = _sha(path)

    with pytest.raises(UserError):
        convert_markers(path, {"/word/document.xml#1#99": "preco"})

    assert _sha(path) == before


def test_rejects_invalid_field_name(tmp_path):
    path = make_docx(tmp_path / "m.docx", [["a ????? b"]])
    marker = scan_document(path).markers[0]

    with pytest.raises(UserError):
        convert_markers(path, {marker.id: "Preço Final"})
