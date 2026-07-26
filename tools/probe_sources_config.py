"""
Tools Module: probe_sources_config.py
Script di profilazione e verifica per la mappatura delle 8 fonti regolatorie (config/sources_spec.json).
"""

import json
import logging
import sys
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s - [%(levelname)s] - %(message)s")
logger = logging.getLogger(__name__)


def probe_sources_config(spec_path: str = "config/sources_spec.json") -> dict:
    """Carica e valida il file di specifiche delle fonti regolatorie."""
    path = Path(spec_path)
    if not path.exists():
        logger.error(f"File di specifiche non trovato in {path.resolve()}")
        sys.exit(1)

    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        sources = data.get("sources", {})
        logger.info(f"=== MAPPATURA FONTI REGOLATORIE CARICATA ({len(sources)} fonti) ===")
        
        for name, spec in sources.items():
            logger.info(
                f"[{name}] Paese: {spec.get('country')} | Tipo: {spec.get('type')} | "
                f"Formato Date: {spec.get('date_format')} | Keyword Style: {spec.get('keyword_style')}"
            )

        return sources
    except Exception as e:
        logger.error(f"Errore durante la lettura di {spec_path}: {e}")
        sys.exit(1)


if __name__ == "__main__":
    probe_sources_config()
