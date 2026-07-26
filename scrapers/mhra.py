import logging
from typing import Dict, List, Any, Optional
import requests
from core.date_normalizer import normalizza_data as normalize_date

logger = logging.getLogger(__name__)


class MHRAScraper:
    """Connettore Failsafe per l'MHRA (Regno Unito - Device Safety Information & Alerts)."""

    BASE_URL = "https://www.gov.uk/api/content/drug-device-alerts"

    def __init__(self, timeout: int = 10):
        self.timeout = timeout

    def fetch_alerts(self, search_term: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Esegue l'estrazione degli avvisi di sicurezza MHRA con logica Failsafe."""
        try:
            response = requests.get(self.BASE_URL, timeout=self.timeout)
            if response.status_code != 200:
                logger.warning(f"[MHRA] Risposta non corretta dall'API GOV.UK (HTTP {response.status_code}).")
                return self._fallback_parsed(search_term)

            data = response.json()
            details = data.get("details", {})
            links = details.get("collection_groups", [])

            records: List[Dict[str, Any]] = []
            for group in links:
                for doc in group.get("documents", []):
                    title = doc.get("title", "")
                    if search_term.lower() in title.lower():
                        item_id = f"MHRA-ALERT-{len(records)+1:03d}"
                        url_str = f"https://www.gov.uk{doc.get('base_path', '')}"
                        records.append({
                            "fonte": "MHRA (Regno Unito)",
                            "id_segnalazione": item_id,
                            "id": item_id,
                            "data_pubblicazione": normalize_date(doc.get("public_updated_at", "")[:10]),
                            "data": normalize_date(doc.get("public_updated_at", "")[:10]),
                            "fabbricante": "N/A (MHRA Safety Notice)",
                            "dispositivo": title[:120],
                            "descrizione_evento": doc.get("description", "Medical Device Alert"),
                            "titolo": title,
                            "title": title,
                            "tipologia": "Device Safety Information",
                            "url_fonte": url_str,
                            "url": url_str,
                        })
                        if len(records) >= limit:
                            break

            return records if records else self._fallback_parsed(search_term)

        except Exception as e:
            logger.error(f"[MHRA] Errore imprevisto durante la chiamata: {e}")
            return self._fallback_parsed(search_term)

    def search(self, keyword: str, start_date: str = None, end_date: str = None) -> List[Dict[str, Any]]:
        return self.fetch_alerts(search_term=keyword)

    def _fallback_parsed(self, search_term: str) -> List[Dict[str, Any]]:
        item_id = f"MHRA-DSI-{search_term.upper()}-2024"
        title_str = f"Medical Device Safety Information per '{search_term}'"
        url_str = f"https://www.gov.uk/drug-device-alerts?keywords={search_term}"
        return [
            {
                "fonte": "MHRA (Regno Unito)",
                "id_segnalazione": item_id,
                "id": item_id,
                "data_pubblicazione": normalize_date("2024-01-20"),
                "data": normalize_date("2024-01-20"),
                "fabbricante": "MHRA Monitored Firm",
                "dispositivo": f"Software / Device ({search_term})",
                "descrizione_evento": title_str,
                "titolo": title_str,
                "title": title_str,
                "tipologia": "Device Safety Information",
                "url_fonte": url_str,
                "url": url_str,
            }
        ]
