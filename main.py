import argparse
import json
import logging
import os
import sys
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

# Configurazione Logging per Audit Trail
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
        """Carica la configurazione da JSON con logica Failsafe."""
        default_config = {
            "search_keyword": "mammography",
            "competitors": [],
            "output_excel_path": "PMS_Report_Output.xlsx",
            "timeout_seconds": 10
        }
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    logger.info(f"Configurazione caricata con successo da '{path}'.")
                    return data
            except Exception as e:
                logger.warning(f"Impossibile leggere '{path}': {e}. Uso configurazione di fallback.")
                return default_config
        else:
            logger.info(f"File '{path}' non trovato. Uso configurazione di default.")
            return default_config

    def run(
        self,
        search_term: Optional[str] = None,
        competitors: Optional[List[str]] = None,
        custom_output_path: Optional[str] = None
    ) -> str:
        """Esegue la pipeline PMS usando i parametri forniti o quelli di configurazione."""
        term = search_term or self.config.get("search_keyword", "mammography")
        comp_list = competitors if competitors is not None else self.config.get("competitors", [])
        output_file = custom_output_path or self.output_excel_path

        if custom_output_path:
            self.excel_generator.file_path = custom_output_path

        logger.info(f"=== INIZIO PIPELINE PMS PER: '{term}' ===")
        all_raw_records: List[Dict[str, Any]] = []

        # 1. Ministero della Salute IT
        logger.info("[1/6] Interrogazione Ministero della Salute IT...")
        try:
            it_records = self.min_salute_scraper.fetch_data(term)
            logger.info(f"-> Estratti {len(it_records)} record da Ministero Salute.")
            all_raw_records.extend(it_records)
        except Exception as e:
            logger.error(f"-> Errore connettore Ministero Salute: {e}")

        # 2. openFDA MAUDE
        logger.info("[2/6] Interrogazione openFDA MAUDE API...")
        try:
            fda_records = self.openfda_scraper.fetch_events(term)
            logger.info(f"-> Estratti {len(fda_records)} record da openFDA.")
            all_raw_records.extend(fda_records)
        except Exception as e:
            logger.error(f"-> Errore connettore openFDA: {e}")

        # 3. openFDA Recalls
        logger.info("[3/6] Interrogazione openFDA Device Recalls...")
        try:
            recall_records = self.fda_recalls_scraper.fetch_recalls(term)
            logger.info(f"-> Estratti {len(recall_records)} record da FDA Recalls.")
            all_raw_records.extend(recall_records)
        except Exception as e:
            logger.error(f"-> Errore connettore FDA Recalls: {e}")

        # 4. NIST NVD Cybersecurity
        logger.info("[4/6] Interrogazione NIST NVD Cybersecurity (MDCG 2019-16)...")
        try:
            nvd_records = self.nvd_scraper.fetch_vulnerabilities(term)
            logger.info(f"-> Estratti {len(nvd_records)} record da NIST NVD.")
            all_raw_records.extend(nvd_records)
        except Exception as e:
            logger.error(f"-> Errore connettore NVD Cybersecurity: {e}")

        # 5. BfArM Germania
        logger.info("[5/6] Interrogazione BfArM (Germania)...")
        try:
            bfarm_records = self.bfarm_scraper.fetch_notices(term)
            logger.info(f"-> Estratti {len(bfarm_records)} record da BfArM.")
            all_raw_records.extend(bfarm_records)
        except Exception as e:
            logger.error(f"-> Errore connettore BfArM: {e}")

        # 6. MHRA Regno Unito
        logger.info("[6/6] Interrogazione MHRA (Regno Unito)...")
        try:
            mhra_records = self.mhra_scraper.fetch_alerts(term)
            logger.info(f"-> Estratti {len(mhra_records)} record da MHRA.")
            all_raw_records.extend(mhra_records)
        except Exception as e:
            logger.error(f"-> Errore connettore MHRA: {e}")

        logger.info(f"Totale record grezzi raccolti: {len(all_raw_records)}")

        # Deduplicazione SHA-256
        logger.info("Avvio deduplicazione SHA-256...")
        unique_records = self.deduplicator.process(all_raw_records)
        logger.info(f"-> Record unici dopo deduplicazione: {len(unique_records)}")

        # Tagging NLP e Verifica Competitors
        logger.info("Esecuzione Tagging NLP e verifica Competitors...")
        tagged_records = self.nlp_tagger.process_records(unique_records, competitors=comp_list)

        # Generazione Report Excel Audit-Ready
        logger.info("Generazione Report Excel Audit-Ready...")
        final_file = self.excel_generator.generate(tagged_records, target_device=term)
        logger.info(f"=== PIPELINE COMPLETATA! Report salvato in: {final_file} ===")

        return final_file


def parse_arguments():
    """Parser dei comandi da riga di comando (CLI)."""
    parser = argparse.ArgumentParser(
        description="PMS Automation Pipeline - Software locale per sorveglianza post-market (MDR UE 2017/745)"
    )
    parser.add_argument("-c", "--config", default="config.json", help="Path del file config JSON (default: config.json)")
    parser.add_argument("-k", "--keyword", help="Parola chiave per la ricerca (sovrascrive il file config)")
    parser.add_argument("-comp", "--competitors", help="Lista competitor separati da virgola (es. Siemens,Philips)")
    parser.add_argument("-o", "--output", help="Path file Excel di output (sovrascrive il file config)")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_arguments()
    
    comp_list = [c.strip() for c in args.competitors.split(",")] if args.competitors else None

    orchestrator = PMSOrchestrator(config_path=args.config)
    orchestrator.run(
        search_term=args.keyword,
        competitors=comp_list,
        custom_output_path=args.output
    )