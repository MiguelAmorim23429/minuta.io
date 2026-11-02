"""Biblioteca de minutas.

Ao importar, a minuta é **copiada** para ``<dados>/minutas/<id>.docx``; o ficheiro original da
utilizadora nunca é alterado. A base de dados guarda apenas nome, hash e datas.
"""

import hashlib
import shutil
import sqlite3
import uuid
import zipfile
from datetime import UTC, datetime
from pathlib import Path

from minuta_engine.db.connection import connect
from minuta_engine.errors import UserError
from minuta_engine.models.templates import TemplateInfo, TemplateStatus
from minuta_engine.paths import data_dir
from minuta_engine.templates.scan import ScanResult, scan_document

MAX_NAME_LENGTH = 120


def minutas_dir() -> Path:
    return data_dir() / "minutas"


def template_file(template_id: str) -> Path:
    return minutas_dir() / f"{uuid.UUID(template_id)}.docx"


def import_template(source: str, name: str | None) -> TemplateInfo:
    source_path = Path(source)
    if source_path.suffix.lower() != ".docx":
        raise UserError(
            "Só são suportados ficheiros .docx. Se a minuta estiver em .doc, abra-a no Word e "
            "guarde-a como .docx."
        )
    if not source_path.is_file():
        raise UserError("O ficheiro escolhido não existe.")
    if not _is_docx(source_path):
        raise UserError("O ficheiro não é um documento Word (.docx) válido.")

    template_id = str(uuid.uuid4())
    destination = template_file(template_id)
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source_path, destination)

    now = _now()
    try:
        with connect() as db:
            db.execute(
                "INSERT INTO templates (id, name, sha256, imported_at, updated_at) "
                "VALUES (?, ?, ?, ?, ?)",
                (
                    template_id,
                    _clean_name(name or source_path.stem),
                    _sha256(destination),
                    now,
                    now,
                ),
            )
    except Exception:
        destination.unlink(missing_ok=True)
        raise
    return describe(template_id)[0]


def list_templates() -> list[TemplateInfo]:
    with connect() as db:
        rows = db.execute("SELECT * FROM templates ORDER BY name COLLATE NOCASE").fetchall()
    return [_info(row, _scan_or_none(row["id"])) for row in rows]


def describe(template_id: str) -> tuple[TemplateInfo, ScanResult]:
    """Informação da minuta e resultado da análise do ficheiro."""
    row = _row(template_id)
    path = template_file(template_id)
    if not path.is_file():
        raise UserError("O ficheiro desta minuta já não existe na biblioteca. Importe-a de novo.")
    scan = scan_document(path)
    return _info(row, scan), scan


def path_for(template_id: str) -> Path:
    """Caminho do ficheiro guardado, validando que a minuta existe."""
    _row(template_id)
    path = template_file(template_id)
    if not path.is_file():
        raise UserError("O ficheiro desta minuta já não existe na biblioteca. Importe-a de novo.")
    return path


def rename(template_id: str, name: str) -> TemplateInfo:
    _row(template_id)
    with connect() as db:
        db.execute(
            "UPDATE templates SET name = ?, updated_at = ? WHERE id = ?",
            (_clean_name(name), _now(), template_id),
        )
    return describe(template_id)[0]


def mark_modified(template_id: str) -> None:
    """Atualiza hash e data depois de a aplicação alterar o ficheiro (ex.: conversão)."""
    with connect() as db:
        db.execute(
            "UPDATE templates SET sha256 = ?, updated_at = ? WHERE id = ?",
            (_sha256(template_file(template_id)), _now(), template_id),
        )


def refresh_if_changed(template_id: str) -> None:
    """Regista a data de alteração se o ficheiro foi editado fora da aplicação (ex.: no Word)."""
    row = _row(template_id)
    path = template_file(template_id)
    if path.is_file() and _sha256(path) != row["sha256"]:
        mark_modified(template_id)


def delete(template_id: str) -> None:
    """Remove a minuta da biblioteca (a cópia interna; o ficheiro original não é tocado)."""
    _row(template_id)
    with connect() as db:
        db.execute("DELETE FROM templates WHERE id = ?", (template_id,))
    template_file(template_id).unlink(missing_ok=True)


def _row(template_id: str) -> sqlite3.Row:
    try:
        uuid.UUID(template_id)
    except ValueError as exc:
        raise UserError("Minuta não encontrada.") from exc
    with connect() as db:
        row = db.execute("SELECT * FROM templates WHERE id = ?", (template_id,)).fetchone()
    if row is None:
        raise UserError("Minuta não encontrada.")
    return row


def _scan_or_none(template_id: str) -> ScanResult | None:
    path = template_file(template_id)
    if not path.is_file():
        return None
    try:
        return scan_document(path)
    except UserError:
        return ScanResult()


def _info(row: sqlite3.Row, scan: ScanResult | None) -> TemplateInfo:
    if scan is None:
        status = TemplateStatus.MISSING
    elif scan.markers or scan.error_count or not scan.placeholders:
        status = TemplateStatus.NEEDS_ATTENTION
    else:
        status = TemplateStatus.READY
    return TemplateInfo(
        id=row["id"],
        name=row["name"],
        imported_at=row["imported_at"],
        updated_at=row["updated_at"],
        status=status,
        placeholder_count=len(scan.placeholders) if scan else 0,
        marker_count=len(scan.markers) if scan else 0,
        error_count=scan.error_count if scan else 0,
    )


def _clean_name(name: str) -> str:
    cleaned = " ".join(name.split())[:MAX_NAME_LENGTH]
    if not cleaned:
        raise UserError("Indique um nome para a minuta.")
    return cleaned


def _is_docx(path: Path) -> bool:
    if not zipfile.is_zipfile(path):
        return False
    with zipfile.ZipFile(path) as archive:
        return "word/document.xml" in archive.namelist()


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _now() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")
