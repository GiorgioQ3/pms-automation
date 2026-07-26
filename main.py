"""
Orchestratore principale PMS Automation.
Integrazione dinamica di SourceQueryFormatter per l'adattamento di date e keyword per le 8 fonti.
Esegue lo scraping multi-fonte, la deduplicazione SHA-256, il tagging NLP,
la Signal Detection (MDR Art. 88) e la generazione del report Excel DPR-385.
"""

import os
import sys
import logging
import json
from typing import Dict, List, Any, Optional
from datetime import datetime, date

from scrapers.ministero_salute import MinisteroSaluteScraper
from scrapers.openfda_maude import OpenFDAMaudeScraper
from scrapers.fda_recalls import FDARecallsScraper
from scrapers.fda_safety_communications import FDASafetyCommunicationsScraper
from scrapers.fda_letters import FDALettersScraper
from scrapers.nvd_cybersecurity import NVDCybersecurityScraper
from scrapers.bfarm import BfArMScraper
from scrapers.mhra import MHRAScraper

from core.keyword_parser import KeywordParser
from core.query_formatter import SourceQueryFormatter
from core.date_normalizer import DateNormalizer
from core.deduplicator import SHA256Deduplicator
from core.nlp_tagger import NLPTagger
from core.signal_detector import SignalDetector
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
    """Orchestratore centrale per la Post-Market Surveillance automatizzata."""

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

        self.query_formatter = SourceQueryFormatter()
        self.date_normalizer = DateNormalizer()
        self.deduplicator = SHA256Deduplicator()
        self.nlp_tagger = NLPTagger(competitors=self.config.get("competitors", []))
        self.signal_detector = SignalDetector(incident_threshold=3)
        self.excel_generator = ExcelGenerator()

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
            except Exception as e:
                logger.error(f"Errore caricamento configurazione: {e}")
                return default_config
        return default_config

    def run_pipeline(
        self,
        keyword_input: str,
        start_date: str = None,
        end_date: str = None,
        custom_output_path: str = None,
        competitors: List[str] = None
    ) -> Dict[str, Any]:
        keywords = KeywordParser.parse(keyword_input)
        if not keywords:
            keywords = ["mammography"]

        search_date = datetime.today().strftime("%Y-%m-%d")
        file_start = start_date if start_date else "ALL"
        file_end = end_date if end_date else search_date

        default_file = f"PMS_Report_DPR-385_Period_{file_start}_to_{file_end}.xlsx"
        excel_filename = custom_output_path or default_file

        logger.info(f"=== INIZIO PIPELINE PMS PER KEYWORDS: {keywords} [Period_{file_start}_to_{file_end}] ===")

        scrapers = [
            ("Minister of Health", self.min_salute_scraper),
            ("MAUDE", self.openfda_scraper),
            ("MD Recalls (FDA)", self.fda_recalls_scraper),
            ("Safety Communication (FDA)", self.fda_safety_comm_scraper),
            ("Letters to Health Care Providers (FDA)", self.fda_letters_scraper),
            ("National Vulnerability Database (NVD)", self.nvd_scraper),
            ("BfArM", self.bfarm_scraper),
            ("MHRA", self.mhra_scraper),
        ]

        keyword_stats: Dict[str, Dict[str, Dict[str, int]]] = {}
        all_selected_records: List[Dict[str, Any]] = []

        comp_list = competitors if competitors is not None else self.config.get("competitors", [])
        if comp_list:
            self.nlp_tagger.competitors = comp_list

        for kw in keywords:
            keyword_stats[kw] = {src_name: {"tot": 0, "dupl": 0, "sel": 0} for src_name, _ in scrapers}

            for src_name, scraper in scrapers:
                try:
                    fmt_kw, fmt_start, fmt_end = self.query_formatter.get_formatted_params(
                        source_name=src_name,
                        keyword=kw,
                        start_date=start_date,
                        end_date=end_date
                    )

                    records = scraper.search(fmt_kw, fmt_start, fmt_end)
                    keyword_stats[kw][src_name]["tot"] = len(records)

                    for rec in records:
                        rec["keyword_matched"] = kw
                        rec["source_name"] = src_name
                        rec["date"] = self.date_normalizer.normalize(rec.get("date") or rec.get("data_pubblicazione"))

                        is_dup, _ = self.deduplicator.is_duplicate(rec)
                        if is_dup:
                            keyword_stats[kw][src_name]["dupl"] += 1
                        else:
                            tagged = self.nlp_tagger.tag_record(rec)
                            all_selected_records.append(tagged)
                            keyword_stats[kw][src_name]["sel"] += 1

                except Exception as e:
                    logger.error(f"Errore nello scraping per keyword '{kw}' su '{src_name}': {e}")

        signal_metrics = self.signal_detector.analyze_signals(all_selected_records)

        self.excel_generator.generate_report(
            keyword_stats=keyword_stats,
            all_records=all_selected_records,
            output_filename=excel_filename,
            keyword_input_str=keyword_input,
            start_date=start_date or "Non specificato",
            end_date=end_date or search_date,
            search_date=search_date
        )

        logger.info(f"Pipeline completata. Record totali unici: {len(all_selected_records)}. File: {excel_filename}")

        return {
            "keywords": keywords,
            "total_selected": len(all_selected_records),
            "keyword_stats": keyword_stats,
            "signal_metrics": signal_metrics,
            "excel_filename": excel_filename,
            "search_date": search_date,
            "records": all_selected_records
        }

    def run(
        self,
        search_term: Optional[str] = None,
        competitors: Optional[List[str]] = None,
        custom_output_path: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> str:
        term = search_term or self.config.get("search_keyword", "mammography")
        s_date = start_date.strftime("%Y-%m-%d") if isinstance(start_date, date) else start_date
        e_date = end_date.strftime("%Y-%m-%d") if isinstance(end_date, date) else end_date

        res = self.run_pipeline(
            keyword_input=term,
            start_date=s_date,
            end_date=e_date,
            competitors=competitors,
            custom_output_path=custom_output_path
        )
        return res["excel_filename"]


def parse_arguments():
    import argparse
    parser = argparse.ArgumentParser(description="PMS Automation Pipeline - DPR-385")
    parser.add_argument("-c", "--config", default="config.json")
    parser.add_argument("-k", "--keyword")
    parser.add_argument("-comp", "--competitors")
    parser.add_argument("-o", "--output")
    return parser.parse_args()


if __name__ == "__main__":
    orchestrator = PMSOrchestrator()
    res = orchestrator.run_pipeline("mammography, DICOM viewer")
    print(f"Pipeline completata. File generato: {res['excel_filename']}")