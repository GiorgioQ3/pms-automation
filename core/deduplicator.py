import json
import logging
import hashlib
from pathlib import Path
from typing import Any, Dict, List, Set, Tuple

logger = logging.getLogger(__name__)


def carica_storico(path_storico: str) -> Set[str]:
    """
    Legge un file JSON e restituisce un set con gli ID/link già visti.
    Se il file non esiste o è corrotto, restituisce un set vuoto senza far crashare il programma (failsafe).
    """
    path = Path(path_storico)
    if not path.exists():
        return set()

    try:
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, list):
                return set(data)
            logger.warning(f"Il file di storico {path_storico} non contiene una lista. Formato inatteso.")
            return set()
    except Exception as e:
        logger.error(f"Errore nella lettura del file di storico {path_storico}: {e}")
        return set()


def salva_storico(path_storico: str, id_visti: Set[str]) -> None:
    """
    Salva il set aggiornato nel file JSON specificato (creando le cartelle padre se non esistono).
    """
    path = Path(path_storico)
    path.parent.mkdir(parents=True, exist_ok=True)

    try:
        with path.open("w", encoding="utf-8") as f:
            json.dump(sorted(list(id_visti)), f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"Errore durante il salvataggio dello storico in {path_storico}: {e}")


def filtra_nuovi(
    risultati: List[Dict[str, Any]],
    path_storico: str,
    chiave_id: str = "link_documento"
) -> List[Dict[str, Any]]:
    storico = carica_storico(path_storico)
    nuovi_risultati = []

    for item in risultati:
        valore_id = item.get(chiave_id)
        if valore_id is not None:
            valore_id_str = str(valore_id)
            if valore_id_str not in storico:
                nuovi_risultati.append(item)
            storico.add(valore_id_str)

    salva_storico(path_storico, storico)
    return nuovi_risultati


class SHA256Deduplicator:
    """Deduplicatore basato su calcolo hash SHA-256."""

    def __init__(self, path_storico: str = "pms_history.json"):
        self.path_storico = path_storico
        self.seen_hashes: Set[str] = carica_storico(path_storico)

    def is_duplicate(self, record: Dict[str, Any]) -> Tuple[bool, str]:
        rec_id = record.get("id_segnalazione") or record.get("id") or record.get("link_documento") or record.get("url_fonte")
        if not rec_id:
            rec_bytes = json.dumps(record, sort_keys=True).encode("utf-8")
            hash_id = hashlib.sha256(rec_bytes).hexdigest()
        else:
            hash_id = hashlib.sha256(str(rec_id).encode("utf-8")).hexdigest()

        if hash_id in self.seen_hashes:
            return True, hash_id
        
        self.seen_hashes.add(hash_id)
        salva_storico(self.path_storico, self.seen_hashes)
        return False, hash_id


class Deduplicator:
    """Gestore deduplicazione basato su SHA-256 e storico."""

    def __init__(self, path_storico: str = "pms_history.json"):
        self.path_storico = path_storico

    def process(self, records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Deduplica la lista di record calcolando un hash SHA-256 e salvandolo nello storico."""
        storico = carica_storico(self.path_storico)
        unique_records = []

        for rec in records:
            rec_id = rec.get("id_segnalazione") or rec.get("id") or rec.get("link_documento") or rec.get("url_fonte")
            if not rec_id:
                rec_bytes = json.dumps(rec, sort_keys=True).encode("utf-8")
                hash_id = hashlib.sha256(rec_bytes).hexdigest()
            else:
                hash_id = hashlib.sha256(str(rec_id).encode("utf-8")).hexdigest()

            if hash_id not in storico:
                unique_records.append(rec)
                storico.add(hash_id)

        salva_storico(self.path_storico, storico)
        return unique_records
