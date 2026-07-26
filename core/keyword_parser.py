"""
Keyword Parser Module.
Estrae le keyword singole da una stringa di input separando i termini in base alla virgola.
"""

from typing import List


class KeywordParser:
    """Parser per la gestione delle keyword separate da virgola."""

    @staticmethod
    def parse(keyword_input: str) -> List[str]:
        """
        Parsa la stringa di input dividendola ogni volta che trova una virgola.
        Pulisce gli spazi e rimuove eventuali virgolette esterne da ogni keyword.
        
        Esempi:
        - "mammography, web based viewer" -> ['mammography', 'web based viewer']
        - '"mammography", "web based viewer"' -> ['mammography', 'web based viewer']
        - "PACS, ECG, mammography" -> ['PACS', 'ECG', 'mammography']
        """
        if not keyword_input or not keyword_input.strip():
            return []

        raw_parts = keyword_input.split(",")
        keywords = []
        seen = set()

        for part in raw_parts:
            cleaned = part.strip().strip('"').strip("'").strip()
            if cleaned and cleaned.lower() not in seen:
                seen.add(cleaned.lower())
                keywords.append(cleaned)

        return keywords
