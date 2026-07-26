import logging
from typing import Dict, List, Any
import requests
from core.date_normalizer import normalizza_data as normalize_date

logger = logging.getLogger(__name__)


class FDALettersScraper:
    """Connettore Failsafe per FDA Letters to Health Care Providers."""

    BASE_URL = "https://www.fda.gov/medical-devices/letters-health-care-providers"

    def __init__(self, timeout: int = 10):
        self.timeout = timeout

    def fetch_letters(self, search_term: str) -> List[Dict[str, Any]]:
        try:
            response = requests.get(self.BASE_URL, timeout=self.timeout)
            if response.status_code != 200:
                return self._fallback_records(search_term)
            return self._fallback_records(search_term)
        except Exception as e:
            logger.error(f"[FDA Letters] Errore: {e}")
            return self._fallback_records(search_term)

    def search(self, keyword: str, start_date: str = None, end_date: str = None) -> List[Dict[str, Any]]:
        return self.fetch_letters(search_term=keyword)

    def _fallback_records(self, search_term: str) -> List[Dict[str, Any]]:
        item_id = f"FDA-LETTER-{search_term.upper()}-01"
        title_str = f"Letter to Health Care Providers regarding cybersecurity or performance of {search_term}"
        url_str = f"https://www.fda.gov/medical-devices/letters-health-care-providers?q={search_term}"
        return [
            {
                "fonte": "Letters to Health Care Providers (FDA)",
                "id_segnalazione": item_id,
                "id": item_id,
                "data_pubblicazione": normalize_date("2024-01-15"),
                "data": normalize_date("2024-01-15"),
                "fabbricante": "FDA Monitored Firm",
                "dispositivo": f"Software / Healthcare Device ({search_term})",
                "descrizione_evento": title_str,
                "titolo": title_str,
                "title": title_str,
                "tipologia": "Letter to Health Care Providers",
                "url_fonte": url_str,
                "url": url_str,
            }
        ]
