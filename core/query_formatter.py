"""
Source Query Formatter Module.
Formatta keyword e range temporali in base alle specifiche di ciascuna delle 8 fonti (config/sources_spec.json).
"""

import json
import logging
from datetime import datetime
from typing import Tuple, Dict, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class SourceQueryFormatter:
    """Formatter per l'adattamento delle query e delle date secondo le specifiche delle fonti."""

    def __init__(self, spec_path: str = "config/sources_spec.json"):
        self.spec_path = spec_path
        self.specs = self._load_specs(spec_path)

    def _load_specs(self, path: str) -> Dict[str, Any]:
        p = Path(path)
        if p.exists():
            try:
                with open(p, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    return data.get("sources", {})
            except Exception as e:
                logger.warning(f"Impossibile caricare {path}: {e}")
        return {}

    def format_date(self, date_str: str, target_format: str) -> str:
        """Converte una data ISO (YYYY-MM-DD) nel formato di destinazione specificato."""
        if not date_str:
            return ""

        try:
            dt = datetime.strptime(date_str[:10], "%Y-%m-%d")
        except ValueError:
            return date_str

        if target_format == "DD/MM/YYYY":
            return dt.strftime("%d/%m/%Y")
        elif target_format == "YYYYMMDD":
            return dt.strftime("%Y%m%d")
        elif target_format == "DD.MM.YYYY":
            return dt.strftime("%d.%m.%Y")
        elif target_format == "YYYY-MM-DDTHH:mm:ss.000":
            return dt.strftime("%Y-%m-%dT00:00:00.000")
        else:
            return dt.strftime("%Y-%m-%d")

    def format_keyword(self, keyword: str, style: str) -> str:
        """Formatta la keyword in base allo stile richiesto dalla fonte."""
        if not keyword:
            return ""

        kw = keyword.strip()
        if style == "quoted_field_query":
            return f'"{kw}"'
        elif style == "url_encoded":
            import urllib.parse
            return urllib.parse.quote(kw)
        else:
            return kw

    def get_formatted_params(
        self,
        source_name: str,
        keyword: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Tuple[str, str, str]:
        """Restituisce la tupla (fmt_keyword, fmt_start_date, fmt_end_date) per la fonte indicata."""
        spec = self.specs.get(source_name, {})
        kw_style = spec.get("keyword_style", "plain_text")
        date_fmt = spec.get("date_format", "YYYY-MM-DD")

        fmt_kw = self.format_keyword(keyword, kw_style)
        fmt_start = self.format_date(start_date, date_fmt) if start_date else ""
        fmt_end = self.format_date(end_date, date_fmt) if end_date else ""

        return fmt_kw, fmt_start, fmt_end
