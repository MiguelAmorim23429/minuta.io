"""Conversão de ``.docx`` para PDF com o Microsoft Word instalado (automação COM).

Usa uma instância própria e invisível do Word (``DispatchEx``), para não interferir com
documentos que a utilizadora tenha abertos. O resultado é igual ao "Guardar como PDF" do Word.
"""

import sys
from pathlib import Path

WD_EXPORT_FORMAT_PDF = 17
WD_DO_NOT_SAVE_CHANGES = 0
WD_ALERTS_NONE = 0


class PdfExportError(Exception):
    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


def export_pdf(docx_path: Path, pdf_path: Path) -> None:
    if sys.platform != "win32":
        raise PdfExportError("A exportação para PDF requer o Microsoft Word no Windows.")

    import pythoncom
    import pywintypes
    import win32com.client

    pythoncom.CoInitialize()
    word = None
    document = None
    try:
        word = win32com.client.DispatchEx("Word.Application")
        word.Visible = False
        word.DisplayAlerts = WD_ALERTS_NONE
        document = word.Documents.Open(
            str(docx_path),
            ConfirmConversions=False,
            ReadOnly=True,
            AddToRecentFiles=False,
            Visible=False,
        )
        document.ExportAsFixedFormat(
            OutputFileName=str(pdf_path),
            ExportFormat=WD_EXPORT_FORMAT_PDF,
            OpenAfterExport=False,
        )
    except pywintypes.com_error as exc:
        raise PdfExportError(
            "Não foi possível criar o PDF com o Microsoft Word. O documento Word foi gerado."
        ) from exc
    finally:
        if document is not None:
            try:
                document.Close(SaveChanges=WD_DO_NOT_SAVE_CHANGES)
            except pywintypes.com_error:
                pass
        if word is not None:
            try:
                word.Quit()
            except pywintypes.com_error:
                pass
        pythoncom.CoUninitialize()
