"""
Script di Validazione Live (Ground Truth Verification) per pms-automation.
Esegue una ricerca reale sulla keyword SaMD 'DICOM viewer' su tutte le 8 fonti
utilizzando SourceQueryFormatter e stampa i risultati con URL diretti per la verifica manuale.
"""

import sys
import os
import logging
from pathlib import Path
from datetime import datetime, timedelta

# Forza l'encoding UTF-8 per sys.stdout su Windows terminal
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# Garantisce il caricamento dei moduli dal percorso radice del progetto
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.query_formatter import SourceQueryFormatter

from scrapers.ministero_salute import MinisteroSaluteScraper
from scrapers.openfda_maude import OpenFDAMaudeScraper
from scrapers.fda_recalls import FDARecallsScraper
from scrapers.fda_safety_communications import FDASafetyCommunicationsScraper
from scrapers.fda_letters import FDALettersScraper
from scrapers.nvd_cybersecurity import NVDCybersecurityScraper
from scrapers.bfarm import BfArMScraper
from scrapers.mhra import MHRAScraper

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


def run_live_validation(keyword: str = "DICOM viewer"):
    formatter = SourceQueryFormatter()
    today = datetime.today()
    start_date = (today - timedelta(days=730)).strftime("%Y-%m-%d")  # Ultimi 2 anni
    end_date = today.strftime("%Y-%m-%d")

    scrapers = [
        ("Minister of Health", MinisteroSaluteScraper()),
        ("MAUDE", OpenFDAMaudeScraper()),
        ("MD Recalls (FDA)", FDARecallsScraper()),
        ("Safety Communication (FDA)", FDASafetyCommunicationsScraper()),
        ("Letters to Health Care Providers (FDA)", FDALettersScraper()),
        ("National Vulnerability Database (NVD)", NVDCybersecurityScraper()),
        ("BfArM", BfArMScraper()),
        ("MHRA", MHRAScraper()),
    ]

    print("\n=======================================================")
    print(f"[TEST] LIVE GROUND TRUTH VALIDATION - KEYWORD: '{keyword}'")
    print(f"[PERIOD] Periodo di Ricerca: da {start_date} a {end_date}")
    print("=======================================================\n")

    summary_results = {}

    for source_name, scraper in scrapers:
        fmt_kw, fmt_start, fmt_end = formatter.get_formatted_params(
            source_name=source_name,
            keyword=keyword,
            start_date=start_date,
            end_date=end_date
        )

        print(f"[SOURCE] Interrogazione {source_name}...")
        print(f"   [Query Formattata -> Keyword: '{fmt_kw}', Start: '{fmt_start}', End: '{fmt_end}']")

        try:
            records = scraper.search(keyword, start_date, end_date)
            count = len(records)
            summary_results[source_name] = count

            print(f"   [OK] Record Trovati: {count}")
            if count > 0:
                print("   [URL] Primi 2 URL di Riscontro Estratti:")
                for rec in records[:2]:
                    print(f"      - [{rec.get('id', 'N/A')}] {rec.get('title', '')[:80]}...")
                    print(f"        URL: {rec.get('url', 'N/A')}")
        except Exception as e:
            print(f"   [ERROR] Errore durante lo scraping: {e}")
            summary_results[source_name] = "ERRORE"

        print("-" * 60)

    print("\n[SUMMARY] RIEPILOGO FINALE CONFRONTO FONTI:")
    for src, cnt in summary_results.items():
        print(f"  * {src}: {cnt} record")
    print("\n=======================================================\n")


if __name__ == "__main__":
    run_live_validation("DICOM viewer")
