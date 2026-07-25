import logging
from pathlib import Path
from typing import Any, Dict, List
import pandas as pd
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.utils import get_column_letter

logger = logging.getLogger(__name__)

DEFAULT_COLUMNS = ["fonte", "data", "titolo", "tag", "link_documento", "stato_fonte"]


def genera_excel_report(
    dati: List[Dict[str, Any]],
    output_path: str = "output/report_pms.xlsx"
) -> str:
    """
    Genera un file Excel formattato a partire da una lista di dizionari.
    - Gestisce cartelle mancanti
    - Formatta intestazioni (grassetto, sfondo, filtro automatico)
    - Converte link_documento in collegamenti ipertestuali cliccabili
    - Ridimensiona automaticamente le colonne
    """
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    # Creazione del DataFrame
    if dati:
        df = pd.DataFrame(dati)
        # Assicuriamoci che tutti i campi di default siano presenti
        for col in DEFAULT_COLUMNS:
            if col not in df.columns:
                df[col] = ""
        # Riordiniamo mantenendo i campi di default per primi
        altri_campi = [c for c in df.columns if c not in DEFAULT_COLUMNS]
        df = df[DEFAULT_COLUMNS + altri_campi]
    else:
        df = pd.DataFrame(columns=DEFAULT_COLUMNS)

    # Creazione della cartella di lavoro openpyxl
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Report PMS"

    headers = list(df.columns)
    ws.append(headers)

    # Stili per l'intestazione
    header_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
    header_fill = PatternFill(start_color="1F4E79", end_color="1F4E79", fill_type="solid") # Blu Scuro / Elegante
    header_alignment = Alignment(horizontal="center", vertical="center")

    for col_num, header in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col_num)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = header_alignment

    # Scrittura dei dati e formattazione link
    link_font = Font(name="Calibri", size=11, color="0000FF", underline="single")

    for row_idx, row_data in enumerate(df.to_dict(orient="records"), start=2):
        for col_idx, header in enumerate(headers, start=1):
            valore = row_data.get(header, "")
            val_str = str(valore) if valore is not None else ""
            cell = ws.cell(row=row_idx, column=col_idx)

            if header == "link_documento" and val_str.startswith(("http://", "https://")):
                cell.value = val_str
                cell.hyperlink = val_str
                cell.font = link_font
            else:
                cell.value = valore

    # Attivazione filtro automatico
    if headers:
        max_col_letter = get_column_letter(len(headers))
        max_row = max(1, len(df) + 1)
        ws.auto_filter.ref = f"A1:{max_col_letter}{max_row}"

    # Auto-fit larghezza colonne
    for col in ws.columns:
        max_len = 0
        col_letter = get_column_letter(col[0].column)
        for cell in col:
            val_str = str(cell.value or "")
            if len(val_str) > max_len:
                max_len = len(val_str)
        
        # Limita larghezza massima a 60 per leggibilità
        adjusted_width = max(max_len + 4, 12)
        if adjusted_width > 60:
            adjusted_width = 60
        ws.column_dimensions[col_letter].width = adjusted_width

    wb.save(path)
    logger.info(f"Report Excel generato con successo in {path.resolve()}")
    return str(path)
