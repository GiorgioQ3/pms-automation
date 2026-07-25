import pytest
from core.date_normalizer import normalizza_data


def test_normalizza_data_iso():
    assert normalizza_data("2024-05-15") == "15/05/2024"
    assert normalizza_data("2023-12-31") == "31/12/2023"


def test_normalizza_data_italiano():
    assert normalizza_data("15/05/2024") == "15/05/2024"
    assert normalizza_data("01/01/2025") == "01/01/2025"


def test_normalizza_data_americano():
    # MM/DD/YYYY -> 12/25/2024 (25 Dicembre)
    assert normalizza_data("12/25/2024") == "25/12/2024"


def test_normalizza_data_tedesco():
    assert normalizza_data("15.05.2024") == "15/05/2024"
    assert normalizza_data("31.12.2023") == "31/12/2023"


def test_normalizza_data_spazi_bianchi():
    assert normalizza_data("  2024-05-15  ") == "15/05/2024"


def test_normalizza_data_casi_limite_e_invalidi():
    assert normalizza_data("") is None
    assert normalizza_data("   ") is None
    assert normalizza_data(None) is None
    assert normalizza_data("data_non_valida") is None
    assert normalizza_data("31/02/2024") is None  # Data inesistente
    assert normalizza_data("2024/05/15") is None  # Formato con slash invertito rispetto a ISO
    assert normalizza_data(12345) is None
