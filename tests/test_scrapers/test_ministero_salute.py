"""
Test unitari per lo scraper del Ministero della Salute.
"""

from unittest.mock import MagicMock, patch
import httpx
import pytest

from scrapers.ministero_salute import fetch_ministero_salute


MOCK_HTML_SUCCESS = """
<!DOCTYPE html>
<html>
<body>
    <table>
        <tr><th>Data</th><th>Titolo</th></tr>
        <tr>
            <td>15/10/2023</td>
            <td><a href="/portale/dispositiviMedici/dettaglio.jsp?id=123">Avviso di sicurezza per vulnerabilità Cybersecurity su pacemaker</a></td>
        </tr>
        <tr>
            <td>2023-11-20</td>
            <td><a href="/portale/dispositiviMedici/dettaglio.jsp?id=456">Aggiornamento interfaccia utente display per pompa d'infusione</a></td>
        </tr>
        <tr>
            <td>31.12.2023</td>
            <td><a href="/portale/dispositiviMedici/dettaglio.jsp?id=789">Rischio corruzione dati su software di monitoraggio</a></td>
        </tr>
    </table>
</body>
</html>
"""


@patch("httpx.get")
def test_fetch_ministero_salute_success(mock_get):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.text = MOCK_HTML_SUCCESS
    mock_response.raise_for_status.return_value = None
    mock_get.return_value = mock_response

    risultati = fetch_ministero_salute(limit=10)

    assert len(risultati) == 3

    item1 = risultati[0]
    assert item1["fonte"] == "Ministero della Salute"
    assert item1["data"] == "15/10/2023"
    assert "Cybersecurity" in item1["titolo"]
    assert item1["tag"] == "Cybersecurity"
    assert item1["link_documento"] == "https://www.salute.gov.it/portale/dispositiviMedici/dettaglio.jsp?id=123"
    assert item1["stato_fonte"] == "OK"

    item2 = risultati[1]
    assert item2["data"] == "20/11/2023"
    assert item2["tag"] == "Interfaccia/Grafica"

    item3 = risultati[2]
    assert item3["data"] == "31/12/2023"
    assert item3["tag"] == "Integrità Dati"


@patch("httpx.get")
def test_fetch_ministero_salute_limit(mock_get):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.text = MOCK_HTML_SUCCESS
    mock_response.raise_for_status.return_value = None
    mock_get.return_value = mock_response

    risultati = fetch_ministero_salute(limit=2)
    assert len(risultati) == 2


@patch("httpx.get")
def test_fetch_ministero_salute_http_error(mock_get):
    mock_get.side_effect = httpx.HTTPError("Errore di connessione simulato")

    risultati = fetch_ministero_salute(limit=10)
    assert risultati == []


@patch("httpx.get")
def test_fetch_ministero_salute_timeout(mock_get):
    mock_get.side_effect = httpx.TimeoutException("Timeout della richiesta")

    risultati = fetch_ministero_salute(limit=10)
    assert risultati == []
