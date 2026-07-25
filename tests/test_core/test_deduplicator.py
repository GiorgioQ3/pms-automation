import json
import pytest
from pathlib import Path
from core.deduplicator import carica_storico, salva_storico, filtra_nuovi


def test_carica_storico_file_inesistente(tmp_path: Path):
    path = tmp_path / "inesistente.json"
    res = carica_storico(str(path))
    assert res == set()


def test_carica_storico_file_corrotto(tmp_path: Path):
    path = tmp_path / "corrotto.json"
    path.write_text("{questo non e' un json valido", encoding="utf-8")
    res = carica_storico(str(path))
    assert res == set()


def test_carica_storico_formato_non_lista(tmp_path: Path):
    path = tmp_path / "oggetto.json"
    path.write_text('{"key": "value"}', encoding="utf-8")
    res = carica_storico(str(path))
    assert res == set()


def test_salva_e_carica_storico(tmp_path: Path):
    path = tmp_path / "subfolder" / "storico.json"
    id_set = {"id1", "id2", "id3"}
    
    salva_storico(str(path), id_set)
    assert path.exists()

    caricato = carica_storico(str(path))
    assert caricato == id_set


def test_filtra_nuovi(tmp_path: Path):
    path = tmp_path / "storico.json"

    # Primo batch: 2 elementi
    batch1 = [
        {"link_documento": "http://example.com/1", "title": "Doc 1"},
        {"link_documento": "http://example.com/2", "title": "Doc 2"}
    ]

    nuovi1 = filtra_nuovi(batch1, str(path), chiave_id="link_documento")
    assert len(nuovi1) == 2
    assert nuovi1 == batch1

    # Verifica che lo storico contenga entrambi i link
    storico_attuale = carica_storico(str(path))
    assert storico_attuale == {"http://example.com/1", "http://example.com/2"}

    # Secondo batch: 1 duplicato, 1 nuovo
    batch2 = [
        {"link_documento": "http://example.com/2", "title": "Doc 2"},
        {"link_documento": "http://example.com/3", "title": "Doc 3"}
    ]

    nuovi2 = filtra_nuovi(batch2, str(path), chiave_id="link_documento")
    assert len(nuovi2) == 1
    assert nuovi2[0]["link_documento"] == "http://example.com/3"

    # Verifica lo storico finale
    storico_finale = carica_storico(str(path))
    assert storico_finale == {
        "http://example.com/1",
        "http://example.com/2",
        "http://example.com/3"
    }


def test_filtra_nuovi_chiave_personalizzata(tmp_path: Path):
    path = tmp_path / "storico_custom.json"

    batch = [
        {"id": "doc_100", "title": "Doc 100"},
        {"id": "doc_101", "title": "Doc 101"}
    ]

    nuovi = filtra_nuovi(batch, str(path), chiave_id="id")
    assert len(nuovi) == 2
    assert carica_storico(str(path)) == {"doc_100", "doc_101"}
