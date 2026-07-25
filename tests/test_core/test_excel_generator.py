import pytest
from pathlib import Path
import openpyxl
from core.excel_generator import genera_excel_report


def test_genera_excel_report_dati_validi(tmp_path: Path):
    output_file = tmp_path / "subfolder" / "report_test.xlsx"
    dati = [
        {
            "fonte": "MDR",
            "data": "2026-05-15",
            "titolo": "Regolamento Dispositivi Medici",
            "tag": "dispositivi medici, sicurezza",
            "link_documento": "https://example.com/mdr",
            "stato_fonte": "OK"
        },
        {
            "fonte": "FDA",
            "data": "2026-06-20",
            "titolo": "Guidance Document",
            "tag": "fda, guidanza",
            "link_documento": "https://example.com/fda",
            "stato_fonte": "OK"
        }
    ]

    res_path = genera_excel_report(dati, str(output_file))
    assert Path(res_path).exists()

    wb = openpyxl.load_workbook(output_file)
    assert "Report PMS" in wb.sheetnames
    ws = wb["Report PMS"]

    # Verifica intestazioni (riga 1)
    headers = [cell.value for cell in ws[1]]
    assert headers[:6] == ["fonte", "data", "titolo", "tag", "link_documento", "stato_fonte"]

    # Verifica righe di dati (riga 2 e riga 3)
    assert ws.cell(row=2, column=1).value == "MDR"
    assert ws.cell(row=3, column=1).value == "FDA"

    # Verifica hyperlink
    cell_link = ws.cell(row=2, column=5)
    assert cell_link.value == "https://example.com/mdr"
    assert cell_link.hyperlink is not None
    assert cell_link.hyperlink.target == "https://example.com/mdr"


def test_genera_excel_report_dati_vuoti(tmp_path: Path):
    output_file = tmp_path / "report_vuoto.xlsx"
    dati = []

    res_path = genera_excel_report(dati, str(output_file))
    assert Path(res_path).exists()

    wb = openpyxl.load_workbook(output_file)
    ws = wb.active

    # Deve contenere solo la riga delle intestazioni
    headers = [cell.value for cell in ws[1]]
    assert headers == ["fonte", "data", "titolo", "tag", "link_documento", "stato_fonte"]
    assert ws.max_row == 1


def test_genera_excel_report_campi_extra(tmp_path: Path):
    output_file = tmp_path / "report_extra.xlsx"
    dati = [
        {
            "fonte": "EMA",
            "data": "2026-01-10",
            "titolo": "Report EMA",
            "tag": "ema",
            "link_documento": "https://example.com/ema",
            "stato_fonte": "OK",
            "campo_extra": "Valore Extra"
        }
    ]

    genera_excel_report(dati, str(output_file))
    wb = openpyxl.load_workbook(output_file)
    ws = wb.active

    headers = [cell.value for cell in ws[1]]
    assert "campo_extra" in headers
    assert ws.cell(row=2, column=headers.index("campo_extra") + 1).value == "Valore Extra"
