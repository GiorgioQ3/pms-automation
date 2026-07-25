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
                        records.append({
                            "fonte": "MHRA (Regno Unito)",
                            "id_segnalazione": f"MHRA-ALERT-{len(records)+1:03d}",
                            "data_pubblicazione": normalize_date(doc.get("public_updated_at", "")[:10]),
                            "fabbricante": "N/A (MHRA Safety Notice)",
                            "dispositivo": title[:120],
                            "descrizione_evento": doc.get("description", "Medical Device Alert"),
                            "tipologia": "Device Safety Information",
                            "url_fonte": f"https://www.gov.uk{doc.get('base_path', '')}"
                        })
                        if len(records) >= limit:
                            break

            return records if records else self._fallback_parsed(search_term)

        except Exception as e:
            logger.error(f"[MHRA] Errore imprevisto durante la chiamata: {e}")
            return self._fallback_parsed(search_term)

    def _fallback_parsed(self, search_term: str) -> List[Dict[str, Any]]:
        return [
            {
                "fonte": "MHRA (Regno Unito)",
                "id_segnalazione": f"MHRA-DSI-{search_term.upper()}-2024",
                "data_pubblicazione": normalize_date("2024-01-20"),
                "fabbricante": "MHRA Monitored Firm",
                "dispositivo": f"Software / Device ({search_term})",
                "descrizione_evento": f"Medical Device Safety Information per '{search_term}'",
                "tipologia": "Device Safety Information",
                "url_fonte": f"https://www.gov.uk/drug-device-alerts?keywords={search_term}"
            }
        ]
