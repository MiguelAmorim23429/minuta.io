from conftest import make_docx

from minuta_engine.templates.scan import scan_document


def test_finds_placeholders_in_body_and_header(tmp_path):
    path = make_docx(
        tmp_path / "m.docx",
        [["Vende a ", "{{ comprador_1_nome }}", " pelo preço de {{preco}}."], ["{{ preco }}"]],
        header=["Livro: {{ livro }}"],
    )

    result = scan_document(path)

    by_key = {p.field.key: p for p in result.placeholders}
    assert set(by_key) == {"comprador_1_nome", "preco", "livro"}
    assert by_key["preco"].occurrences == 2
    assert by_key["livro"].parts == ["Cabeçalho"]
    assert by_key["preco"].field.label == "Preço (em algarismos)"
    assert result.issues == []


def test_orders_by_catalog_and_unknown_fields_last(tmp_path):
    path = make_docx(tmp_path / "m.docx", [["{{ campo_novo }} {{ preco }} {{ data_ato_extenso }}"]])

    result = scan_document(path)

    assert [p.field.key for p in result.placeholders] == [
        "data_ato_extenso",
        "preco",
        "campo_novo",
    ]
    unknown = result.placeholders[-1].field
    assert unknown.known is False
    assert unknown.group_label == "Outros campos"


def test_detects_marker_split_across_runs(tmp_path):
    path = make_docx(tmp_path / "m.docx", [["pelo preço de ", "*??????", "*????", " vendem"]])

    result = scan_document(path)

    assert len(result.markers) == 1
    marker = result.markers[0]
    assert marker.length == 10
    assert marker.before == "pelo preço de "
    assert marker.after == " vendem"
    assert marker.convertible is True


def test_reports_invalid_names_and_syntax(tmp_path):
    path = make_docx(
        tmp_path / "m.docx",
        [["{{ Nome Comprador }}"], ["preço {{ preco"], ["{% if x %}"]],
    )

    result = scan_document(path)

    messages = [issue.message for issue in result.issues]
    assert any("Nome de campo inválido" in m for m in messages)
    assert any("Campo incompleto" in m for m in messages)
    assert any("não são suportados" in m for m in messages)
    assert result.error_count == 3


def test_two_question_marks_are_not_a_marker(tmp_path):
    path = make_docx(tmp_path / "m.docx", [["Será?? Sim."]])
    assert scan_document(path).markers == []
