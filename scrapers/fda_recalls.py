import logging
from typing import Dict, List, Any, Optional
import requests
from core.date_normalizer import normalizza_data as normalize_date

logger = logging.getLogger(__name__)


class FDARecallsScraper:
    """Connettore Failsafe per l'API openFDA Medical Device Recalls & Safety Communications."""

    BASE_URL = "https://api.fda.gov/device/recall.json"

    def __init__(self, timeout: int = 10):
        self.timeout = timeout

    def fetch_recalls(self, search_term: str, limit: int = 10) -> List[Dict[str, Any]]:
        query = f'product_description:"{search_term}"'
        params = {"search": query, "limit": limit}

        try:
            response = requests.get(self.BASE_URL, params=params, timeout=self.timeout)

            # openFDA restituisce HTTP 404 quando non ci sono match
            if response.status_code == 404:
                logger.info(f"[FDA Recalls] Nessun record trovato (HTTP 404) per keyword '{search_term}'.")
                return []

            if response.status_code != 200:
                logger.warning(f"[FDA Recalls] Risposta non corretta dall'API (HTTP {response.status_code}).")
                return []

            data = response.json()
            results = data.get("results", [])

            normalized_records: List[Dict[str, Any]] = []
            for item in results:
                parsed = self._parse_record(item)
                if parsed:
                    normalized_records.append(parsed)

            return normalized_records
        except Exception as e:
            logger.error(f"[FDA Recalls] Errore imprevisto durante il recupero dati: {e}")
            return []

    def search(self, keyword: str, start_date: str = None, end_date: str = None) -> List[Dict[str, Any]]:
        return self.fetch_recalls(search_term=keyword)

    def _parse_record(self, item: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        try:
            recall_num = item.get("recall_number", "N/A")
            raw_date = item.get("event_date_posted", item.get("initiation_date", ""))
            if len(raw_date) == 8 and raw_date.isdigit():
                raw_date = f"{raw_date[:4]}-{raw_date[4:6]}-{raw_date[6:]}"
            
            date_pub = normalize_date(raw_date)
            manufacturer = item.get("recalling_firm", "N/A")
            product = item.get("product_description", "N/A")
            reason = item.get("reason_for_recall", "N/A")
            url = f"https://www.accessdata.fda.gov/scripts/cdrh/cfdocs/cfres/res.cfm?id={recall_num}"

            return {
                "fonte": "FDA Device Recalls",
                "id_segnalazione": str(recall_num),
                "id": str(recall_num),
                "data_pubblicazione": date_pub,
                "data": date_pub,
                "fabbricante": str(manufacturer).strip(),
                "dispositivo": str(product)[:150].strip(),
                "descrizione_evento": str(reason).strip(),
                "titolo": str(product)[:150].strip(),
                "title": str(product)[:150].strip(),
                "tipologia": f"Medical Device Recall (Class {item.get('event_date_posted', '')})",
                "url_fonte": url,
                "url": url,
            }
        except Exception as e:
            logger.warning(f"[FDA Recalls] Errore durante il parsing del record: {e}")
            return None
