"""
Signal Detector Module (MDR UE 2017/745 Art. 88 & MDCG 2019-16).
Analizza i record unici arricchiti per rilevare segnali di rischio e trend.
"""

import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)


class SignalDetector:
    """Rilevatore di segnali di sicurezza e anomalie di trend."""

    def __init__(self, incident_threshold: int = 3):
        self.incident_threshold = incident_threshold

    def analyze_signals(self, records: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analizza i record estratti e restituisce metriche di segnale.
        """
        high_severity = 0
        categories_count = {}

        for rec in records:
            tag = rec.get("tag", "Generico")
            categories_count[tag] = categories_count.get(tag, 0) + 1

            tipologia = str(rec.get("tipologia", "")).lower()
            fonte = str(rec.get("fonte", "")).lower()
            if "cybersecurity" in tipologia or "vulnerability" in fonte or tag == "Cybersecurity":
                high_severity += 1

        total_records = len(records)
        if high_severity >= self.incident_threshold or total_records > 10:
            overall_risk = "ALTO"
        elif high_severity > 0 or total_records > 0:
            overall_risk = "MEDIO"
        else:
            overall_risk = "BASSO"

        return {
            "total_incidents": total_records,
            "high_severity_incidents": high_severity,
            "overall_risk_level": overall_risk,
            "categories_breakdown": categories_count
        }
