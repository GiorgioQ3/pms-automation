import argparse
import json
import logging
import os
import sys
from datetime import datetime, date
from typing import List, Dict, Any, Optional

from scrapers.ministero_salute import MinisteroSaluteScraper
from scrapers.openfda_maude import OpenFDAMaudeScraper
from scrapers.fda_recalls import FDARecallsScraper
from scrapers.nvd_cybersecurity import NVDCybersecurityScraper
from scrapers.bfarm import BfArMScraper
from scrapers.mhra import MHRAScraper
from core.deduplicator import Deduplicator
from core.nlp_tagger import NLPTagger
from core.excel_generator import ExcelGenerator

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - [%(levelname)s] - %(name)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("pms_execution.log", encoding="utf-8")
    ]
)
logger = logging.getLogger("PMSPipeline")


class PMSOrchestrator:
    """Orchestratore della Pipeline di Post-Market Surveillance (PMS)."""

    def __init__(self, config_path: str = "config.json"):
        self.config_path = config_path
        self.config = self._load_config(config_path)
        
        self.output_excel_path = self.config.get("output_excel_path", "PMS_Report_MDR_2017_745.xlsx")
        self.timeout = self.config.get("timeout_seconds", 10)
        
        self.min_salute_scraper = MinisteroSaluteScraper(timeout=self.timeout)
        self.openfda_scraper = OpenFDAMaudeScraper(timeout=self.timeout)
        self.fda_recalls_scraper = FDARecallsScraper(timeout=self.timeout)
        self.nvd_scraper = NVDCybersecurityScraper(timeout=self.timeout)
        self.bfarm_scraper = BfArMScraper(timeout=self.timeout)
        self.mhra_scraper = MHRAScraper(timeout=self.timeout)
        
        self.deduplicator = Deduplicator()
        self.nlp_tagger = NLPTagger()
        self.excel_generator = ExcelGenerator(file_path=self.output_excel_path)

    def _load_config(self, path: str) -> Dict[str, Any]:
        default_config = {
            "search_keyword": "mammography",
            "competitors": [],
            "output_excel_path": "PMS_Report_Output.xlsx",
            "timeout_seconds": 10
        }
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Impossibile leggere '{path}': {e}. Uso fallback.")
                return default_config
        return default_config

    def _filter_by_date_range(self, records: List[Dict[str, Any]], start_date: Optional[date], end_date: Optional[date]) -> List[Dict[str, Any]]:
        if not start_date and not end_date:
            return records

        filtered = []
        for r in records:
            d_str = r.get("data_pubblicazione", "")
            try:
                dt = datetime.strptime(d_str, "%d/%m/%Y").date()
                if start_date and dt < start_date:
                    continue
                if end_date and dt > end_date:
                    continue
                filtered.append(r)
            except Exception:
                # In caso di data non valida o sconosciuta, mantieni il record in ottica Failsafe
                filtered.append(r)
        return filtered

    def run(
        self,
        search_term: Optional[str] = None,
        competitors: Optional[List[str]] = None,
        custom_output_path: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> str:
        term = search_term or self.config.get("search_keyword", "mammography")
        comp_list = competitors if competitors is not None else self.config.get("competitors", [])
        output_file = custom_output_path or self.output_excel_path

        if custom_output_path:
            self.excel_generator.file_path = custom_output_path

        logger.info(f"=== INIZIO PIPELINE PMS PER: '{term}' ===")
        all_raw_records: List[Dict[str, Any]] = []

        # 1. Ministero della Salute IT
        try:
            all_raw_records.extend(self.min_salute_scraper.fetch_data(term))
        except Exception as e:
            logger.error(f"Errore Ministero Salute: {e}")

        # 2. openFDA MAUDE
        try:
            all_raw_records.extend(self.openfda_scraper.fetch_events(term))
        except Exception as e:
            logger.error(f"Errore openFDA MAUDE: {e}")

        # 3. openFDA Recalls
        try:
            all_raw_records.extend(self.fda_recalls_scraper.fetch_recalls(term))
        except Exception as e:
            logger.error(f"Errore FDA Recalls: {e}")

        # 4. NIST NVD Cybersecurity
        try:
            all_raw_records.extend(self.nvd_scraper.fetch_vulnerabilities(term))
        except Exception as e:
            logger.error(f"Errore NVD Cybersecurity: {e}")

        # 5. BfArM
        try:
            all_raw_records.extend(self.bfarm_scraper.fetch_notices(term))
        except Exception as e:
            logger.error(f"Errore BfArM: {e}")

        # 6. MHRA
        try:
            all_raw_records.extend(self.mhra_scraper.fetch_alerts(term))
        except Exception as e:
            logger.error(f"Errore MHRA: {e}")

        logger.info(f"Totale record grezzi raccolti: {len(all_raw_records)}")

        # Filtraggio temporale opzionale
        if start_date or end_date:
            all_raw_records = self._filter_by_date_range(all_raw_records, start_date, end_date)
            logger.info(f"Record rimanenti dopo filtro data ({start_date} - {end_date}): {len(all_raw_records)}")

        # Deduplicazione SHA-256
        unique_records = self.deduplicator.process(all_raw_records)

        # Tagging NLP
        tagged_records = self.nlp_tagger.process_records(unique_records, competitors=comp_list)

        # Generazione Report Excel
        final_file = self.excel_generator.generate(tagged_records, target_device=term)
        logger.info(f"=== PIPELINE COMPLETATA! Report salvato in: {final_file} ===")

        return final_file


def parse_arguments():
    parser = argparse.ArgumentParser(description="PMS Automation Pipeline")
    parser.add_argument("-c", "--config", default="config.json")
    parser.add_argument("-k", "--keyword")
    parser.add_argument("-comp", "--competitors")
    parser.add_argument("-o", "--output")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_arguments()
    comp_list = [c.strip() for c in args.competitors.split(",")] if args.competitors else None
    orchestrator = PMSOrchestrator(config_path=args.config)
    orchestrator.run(search_term=args.keyword, competitors=comp_list, custom_output_path=args.output)