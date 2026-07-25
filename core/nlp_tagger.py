import re
import unicodedata

CATEGORY_PATTERNS = [
    (
        "Cybersecurity",
        re.compile(
            r"\b(cyber\w*|vulnerabilit\w*|schwachstelle\w*|cve\b|cve-\w+|malware|ransomware|patch|sicurezza\s+informatica)\b",
            re.IGNORECASE,
        ),
    ),
    (
        "Interfaccia/Grafica",
        re.compile(
            r"\b(interfacci\w*|user\s+interface|\bui\b|grafic\w*|display|benutzeroberflache\w*|screen)\b",
            re.IGNORECASE,
        ),
    ),
    (
        "Integrità Dati",
        re.compile(
            r"\b(integrita\s+dati|data\s+integrity|datenintegritat\w*|corruzione\s+dati|data\s+loss)\b",
            re.IGNORECASE,
        ),
    ),
]


def _normalizza_testo(testo: str) -> str:
    """
    Rimuove accenti e diacritici dal testo utilizzando unicodedata NFKD
    e lo converte in minuscolo.
    """
    testo_nfkd = unicodedata.normalize("NFKD", testo)
    testo_senza_accenti = "".join(
        c for c in testo_nfkd if unicodedata.category(c) != "Mn"
    )
    return testo_senza_accenti.lower()


def assegna_tag(testo_avviso: str | None) -> str:
    """
    Categorizza in modo deterministico un testo di avviso PMS in base a regole regex.

    Categorie in ordine di priorità:
    1. Cybersecurity
    2. Interfaccia/Grafica
    3. Integrità Dati
    Fallback: "Generico"
    """
    if not testo_avviso or not isinstance(testo_avviso, str):
        return "Generico"

    testo_normalizzato = _normalizza_testo(testo_avviso)
    if not testo_normalizzato.strip():
        return "Generico"

    for categoria, pattern in CATEGORY_PATTERNS:
        if pattern.search(testo_normalizzato):
            return categoria

    return "Generico"


class NLPTagger:
    """Tagger NLP per la categorizzazione degli eventi e analisi dei competitor."""

    def process_records(
        self, records: list[dict], competitors: list[str] = None
    ) -> list[dict]:
        """Categorizza i record e aggiunge flag relativi ai competitor."""
        if competitors is None:
            competitors = []

        processed = []
        for rec in records:
            rec_copy = dict(rec)
            testo = rec_copy.get("descrizione_evento") or rec_copy.get("titolo") or ""

            if not rec_copy.get("tag"):
                rec_copy["tag"] = assegna_tag(testo)

            fabbricante = str(rec_copy.get("fabbricante", "")).lower()
            rec_copy["is_competitor"] = any(
                comp.lower() in fabbricante for comp in competitors if comp
            )

            processed.append(rec_copy)

        return processed

