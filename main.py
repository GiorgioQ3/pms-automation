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
from scrapers.fda_safety_communications import FDASafetyCommunicationsScraper
from scrapers.fda_letters import FDALettersScraper
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
    def __init__(self, config_path: str = "config.json"):
        self.config_path = config_path
        self.config = self._load_config(config_path)
        self.output_excel_path = self.config.get("output_excel_path", "PMS_Report_DPR-385_All_Time.xlsx")
        self.timeout = self.config.get("timeout_seconds", 10)
        
        self.min_salute_scraper = MinisteroSaluteScraper(timeout=self.timeout)
        self.openfda_scraper = OpenFDAMaudeScraper(timeout=self.timeout)
        self.fda_recalls_scraper = FDARecallsScraper(timeout=self.timeout)
        self.fda_safety_comm_scraper = FDASafetyCommunicationsScraper(timeout=self.timeout)
        self.fda_letters_scraper = FDALettersScraper(timeout=self.timeout)
        self.nvd_scraper = NVDCybersecurityScraper(timeout=self.timeout)
        self.bfarm_scraper = BfArMScraper(timeout=self.timeout)
        self.mhra_scraper = MHRAScraper(timeout=self.timeout)
        
        self.deduplicator = Deduplicator()
        self.nlp_tagger = NLPTagger()

    def _load_config(self, path: str) -> Dict[str, Any]:
        default_config = {
            "search_keyword": "mammography",
            "competitors": [],
            "timeout_seconds": 10
        }
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
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
                if start_date and dt < start_date: continue
                if end_date and dt > end_date: continue
                filtered.append(r)
            except Exception:
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

        # Generazione nome file dinamico con periodo temporale
        if start_date and end_date:
            period_str = f"from {start_date.strftime('%d-%m-%Y')} to {end_date.strftime('%d-%m-%Y')}"
            default_file = f"PMS_Report_DPR-385_{start_date.strftime('%Y-%m-%d')}_to_{end_date.strftime('%Y-%m-%d')}.xlsx"
        elif start_date:
            period_str = f"from {start_date.strftime('%d-%m-%Y')}"
            default_file = f"PMS_Report_DPR-385_from_{start_date.strftime('%Y-%m-%d')}.xlsx"
        else:
            period_str = "All Available Data"
            default_file = self.output_excel_path if hasattr(self, "output_excel_path") and self.output_excel_path else "PMS_Report_DPR-385_All_Time.xlsx"

        output_file = custom_output_path or default_file

        logger.info(f"=== INIZIO PIPELINE PMS (8 FONTI) PER: '{term}' [{period_str}] ===")
        all_raw_records: List[Dict[str, Any]] = []

        scrapers_calls = [
            ("Ministero Salute", lambda: self.min_salute_scraper.fetch_data(term)),
            ("openFDA MAUDE", lambda: self.openfda_scraper.fetch_events(term)),
            ("FDA Recalls", lambda: self.fda_recalls_scraper.fetch_recalls(term)),
            ("FDA Safety Comm", lambda: self.fda_safety_comm_scraper.fetch_communications(term)),
            ("FDA Letters", lambda: self.fda_letters_scraper.fetch_letters(term)),
            ("NVD Cybersecurity", lambda: self.nvd_scraper.fetch_vulnerabilities(term)),
            ("BfArM", lambda: self.bfarm_scraper.fetch_notices(term)),
            ("MHRA", lambda: self.mhra_scraper.fetch_alerts(term)),
        ]

        for name, call in scrapers_calls:
            try:
                all_raw_records.extend(call())
            except Exception as e:
                logger.error(f"Errore {name}: {e}")

        if start_date or end_date:
            all_raw_records = self._filter_by_date_range(all_raw_records, start_date, end_date)

        unique_records = self.deduplicator.process(all_raw_records)
        tagged_records = self.nlp_tagger.process_records(unique_records, competitors=comp_list)
        
        excel_gen = ExcelGenerator(file_path=output_file)
        final_file = excel_gen.generate(
            records=tagged_records,
            target_device=term,
            search_period=period_str,
            keywords_list=[term]
        )
        
        logger.info(f"=== PIPELINE COMPLETATA! Report salvato in: {final_file} ===")
        return final_file


def parse_arguments():
    parser = argparse.ArgumentParser(description="PMS Automation Pipeline - DPR-385")
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