from unittest.mock import MagicMock, patch
import httpx
import pytest
from core.health_check import controlla_con_retry


@patch("core.health_check.httpx.get")
def test_successo_immediato(mock_get):
    mock_get.return_value = MagicMock(status_code=200)

    risultato = controlla_con_retry("https://example.com", tentativi=3, attesa_secondi=1)

    assert risultato is True
    assert mock_get.call_count == 1
    mock_get.assert_called_once_with("https://example.com", timeout=30)


@patch("core.health_check.time.sleep")
@patch("core.health_check.httpx.get")
def test_successo_dopo_retry(mock_get, mock_sleep):
    mock_get.side_effect = [
        httpx.RequestError("Connessione fallita", request=None),
        MagicMock(status_code=200),
    ]

    risultato = controlla_con_retry("https://example.com", tentativi=3, attesa_secondi=2)

    assert risultato is True
    assert mock_get.call_count == 2
    mock_sleep.assert_called_once_with(2)


@patch("core.health_check.time.sleep")
@patch("core.health_check.httpx.get")
def test_status_code_404_restituisce_true(mock_get, mock_sleep):
    mock_get.return_value = MagicMock(status_code=404)

    risultato = controlla_con_retry("https://example.com", tentativi=3, attesa_secondi=1)

    assert risultato is True
    assert mock_get.call_count == 1
    mock_sleep.assert_not_called()


@patch("core.health_check.time.sleep")
@patch("core.health_check.httpx.get")
def test_server_error_500_retry_e_fallimento(mock_get, mock_sleep):
    mock_get.return_value = MagicMock(status_code=500)

    risultato = controlla_con_retry("https://example.com", tentativi=3, attesa_secondi=1)

    assert risultato is False
    assert mock_get.call_count == 3
    assert mock_sleep.call_count == 2


@patch("core.health_check.time.sleep")
@patch("core.health_check.httpx.get")
def test_esaurimento_tentativi_con_eccezioni(mock_get, mock_sleep):
    mock_get.side_effect = httpx.RequestError("Errore continuo", request=None)

    risultato = controlla_con_retry("https://example.com", tentativi=3, attesa_secondi=1)

    assert risultato is False
    assert mock_get.call_count == 3
    assert mock_sleep.call_count == 2


def test_url_invalidi():
    assert controlla_con_retry("") is False
    assert controlla_con_retry("   ") is False
    assert controlla_con_retry(None) is False
    assert controlla_con_retry(12345) is False
