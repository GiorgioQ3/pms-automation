import logging
from typing import Dict, List, Any, Optional
import requests
from core.date_normalizer import normalizza_data as normalize_date

logger = logging.getLogger(__name__)


class NVDCybersecurityScraper:
    """Connettore Failsafe per il NIST National Vulnerability Database (NVD API v2.0)."""

    BASE_URL = "https://services.nvd.nist.gov/rest/json/cves/2.0"

    def __init__(self, timeout: int = 10):
        self.timeout = timeout

    def fetch_vulnerabilities(self, search_term: str, limit: int = 10) -> List[Dict[str, Any]]:
        params = {"keywordSearch": search_term, "resultsPerPage": limit}

        try:
            response = requests.get(self.BASE_URL, params=params, timeout=self.timeout)
            if response.status_code != 200:
                logger.warning(f"[NVD Cybersecurity] Risposta non corretta dall'API (HTTP {response.status_code}).")
                return []

            data = response.json()
            vulnerabilities = data.get("vulnerabilities", [])

            normalized_records: List[Dict[str, Any]] = []
            for item in vulnerabilities:
                parsed = self._parse_record(item.get("cve", {}))
                if parsed:
                    normalized_records.append(parsed)

            return normalized_records
        except Exception as e:
            logger.error(f"[NVD Cybersecurity] Errore imprevisto durante il recupero dati: {e}")
            return []

    def search(self, keyword: str, start_date: str = None, end_date: str = None) -> List[Dict[str, Any]]:
        return self.fetch_vulnerabilities(search_term=keyword)

    def _parse_record(self, cve: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        try:
            cve_id = cve.get("id", "N/A")
            published = cve.get("published", "")[:10]
            date_pub = normalize_date(published)

            descriptions = cve.get("descriptions", [])
            desc = "N/A"
            for d in descriptions:
                if d.get("lang") == "en":
                    desc = d.get("value", "N/A")
                    break

            url_val = f"https://nvd.nist.gov/vuln/detail/{cve_id}"

            return {
                "fonte": "National Vulnerability Database (NVD)",
                "id_segnalazione": str(cve_id),
                "id": str(cve_id),
                "data_pubblicazione": date_pub,
                "data": date_pub,
                "fabbricante": "N/A (Software Vulnerability)",
                "dispositivo": f"SaMD / Componente Software ({cve_id})",
                "descrizione_evento": str(desc).strip(),
                "titolo": f"Vulnerabilità CVE {cve_id}",
                "title": f"Vulnerabilità CVE {cve_id}",
                "tipologia": "Cybersecurity Vulnerability (MDCG 2019-16)",
                "url_fonte": url_val,
                "url": url_val,
            }
        except Exception as e:
            logger.warning(f"[NVD Cybersecurity] Errore durante il parsing del record: {e}")
            return None
