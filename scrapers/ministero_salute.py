"""
Modulo connettore/scraper per il Ministero della Salute italiano.
Recupera gli avvisi di sicurezza sui dispositivi medici e normalizza le informazioni.
"""

import logging
from urllib.parse import urljoin
import httpx
from bs4 import BeautifulSoup

from core.date_normalizer import normalizza_data
from core.nlp_tagger import assegna_tag

logger = logging.getLogger(__name__)

BASE_URL = "https://www.salute.gov.it"
AVVISI_URL = "https://www.salute.gov.it/portale/dispositiviMedici/ricercaAvvisiDispositiviMedici.jsp"


def fetch_ministero_salute(limit: int = 10) -> list[dict]:
    """
    Recupera gli avvisi di sicurezza sui dispositivi medici dal portale del Ministero della Salute.

    Restituisce una lista di dizionari con i seguenti campi:
    - fonte: "Ministero della Salute"
    - data: data normalizzata (GG/MM/AAAA) o None
    - titolo: titolo o descrizione sintetica dell'avviso
    - tag: categoria assegnata (es. Cybersecurity, Interfaccia/Grafica, ecc.)
    - link_documento: URL completo dell'avviso/documento
    - stato_fonte: "OK" oppure una stringa descrittiva dell'errore

    In caso di errori HTTP/connessione, gestisce le eccezioni in modo resiliente (failsafe).
    """
    risultati = []

    try:
        response = httpx.get(
            AVVISI_URL,
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"},
            timeout=15,
            follow_redirects=True,
        )
        response.raise_for_status()
    except Exception as exc:
        logger.error("Errore durante la richiesta a Ministero della Salute: %s", exc)
        return risultati

    try:
        soup = BeautifulSoup(response.text, "html.parser")

        # Cerca blocchi item o tabelle contenenti gli avvisi
        items = soup.find_all("tr")
        if not items:
            items = soup.find_all("li")

        for item in items:
            if len(risultati) >= limit:
                break

            link_elem = item.find("a")
            if not link_elem:
                continue

            titolo = link_elem.get_text(strip=True)
            if not titolo:
                continue

            href = link_elem.get("href", "")
            link_documento = urljoin(BASE_URL, href) if href else ""

            # Estrazione data (cerca in span, time, td o classi contenenti 'data')
            data_raw = None
            date_elem = item.find(class_=lambda c: c and "data" in c.lower()) if hasattr(item, "find") else None
            if date_elem:
                data_raw = date_elem.get_text(strip=True)
            else:
                tds = item.find_all("td") if hasattr(item, "find_all") else []
                for td in tds:
                    txt = td.get_text(strip=True)
                    if "/" in txt or "-" in txt or "." in txt:
                        data_raw = txt
                        break

            data_norm = normalizza_data(data_raw)
            tag = assegna_tag(titolo)

            risultati.append({
                "fonte": "Ministero della Salute",
                "data": data_norm,
                "titolo": titolo,
                "tag": tag,
                "link_documento": link_documento,
                "stato_fonte": "OK",
            })

    except Exception as exc:
        logger.error("Errore durante il parsing HTML: %s", exc)

    return risultati


class MinisteroSaluteScraper:
    """Connettore/Scraper per il Ministero della Salute italiano."""

    def __init__(self, timeout: int = 10):
        self.timeout = timeout

    def fetch_data(self, search_term: str = "", limit: int = 10) -> list[dict]:
        """Recupera gli avvisi di sicurezza dal Ministero della Salute."""
        return fetch_ministero_salute(limit=limit)


