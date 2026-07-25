import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Set

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
    """
    - Carica lo storico dal file JSON.
    - Filtra la lista risultati mantenendo SOLO gli elementi la cui chiave_id NON è presente nello storico.
    - Aggiorna lo storico aggiungendo le chiavi di TUTTI i risultati analizzati in questa esecuzione.
    - Salva lo storico aggiornato nel file JSON.
    - Restituisce la lista dei soli elementi nuovi.
    """
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
