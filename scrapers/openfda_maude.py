import logging
from typing import Dict, List, Any, Optional
import requests
from core.date_normalizer import normalizza_data as normalize_date

logger = logging.getLogger(__name__)


class OpenFDAMaudeScraper:
    """Connettore Failsafe per l'API openFDA Medical Device Adverse Events (MAUDE)."""

    BASE_URL = "https://api.fda.gov/device/event.json"

    def __init__(self, timeout: int = 10):
        self.timeout = timeout

    def fetch_events(
        self, search_term: str, limit: int = 10
    ) -> List[Dict[str, Any]]:
        query = f'device.brand_name:"{search_term}"'
        params = {"search": query, "limit": limit}

        try:
            response = requests.get(
                self.BASE_URL, params=params, timeout=self.timeout
            )

            if response.status_code != 200:
                logger.warning(
                    f"[openFDA] Risposta non corretta dalla fonte API (HTTP {response.status_code})."
                )
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
            logger.error(
                f"[openFDA] Errore imprevisto durante il recupero dei dati: {e}"
            )
            return []

    def _parse_record(self, item: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        try:
            report_number = item.get(
                "report_number", item.get("mdr_report_key", "N/A")
            )

            raw_date = item.get("date_received") or item.get("date_of_event") or ""
            if len(raw_date) == 8 and raw_date.isdigit():
                raw_date = f"{raw_date[:4]}-{raw_date[4:6]}-{raw_date[6:]}"

            date_pub = normalize_date(raw_date)

            devices = item.get("device", [])
            brand_name = "N/A"
            manufacturer = "N/A"

            if devices and isinstance(devices, list):
                first_dev = devices[0]
                brand_name = first_dev.get(
                    "brand_name", first_dev.get("generic_name", "N/A")
                )
                manufacturer = first_dev.get(
                    "manufacturer_d_name",
                    item.get("manufacturer_g1_name", "N/A"),
                )

            mdr_text = item.get("mdr_text", [])
            desc = "N/A"
            if mdr_text and isinstance(mdr_text, list):
                texts = [
                    t.get("text", "")
                    for t in mdr_text
                    if isinstance(t, dict) and t.get("text")
                ]
                if texts:
                    desc = " | ".join(texts)

            event_type = item.get("event_type", "Adverse Event")

            mdr_key = item.get("mdr_report_key", "")
            url_fonte = (
                f"https://accessdata.fda.gov/scripts/cdrh/cfdocs/cfmaude/detail.cfm?mdrfoi__id={mdr_key}"
                if mdr_key
                else "https://www.accessdata.fda.gov/scripts/cdrh/cfdocs/cfmaude/search.cfm"
            )

            return {
                "fonte": "openFDA MAUDE",
                "id_segnalazione": str(report_number),
                "data_pubblicazione": date_pub,
                "fabbricante": str(manufacturer).strip(),
                "dispositivo": str(brand_name).strip(),
                "descrizione_evento": str(desc).strip(),
                "tipologia": str(event_type).strip(),
                "url_fonte": url_fonte,
            }

        except Exception as e:
            logger.warning(
                f"[openFDA] Errore durante il parsing del record: {e}"
            )
            return None
