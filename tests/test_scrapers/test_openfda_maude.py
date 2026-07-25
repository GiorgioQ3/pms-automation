from unittest.mock import MagicMock, patch
import pytest
from scrapers.openfda_maude import OpenFDAMaudeScraper


@pytest.fixture
def scraper():
    return OpenFDAMaudeScraper()


def test_fetch_events_success(scraper):
    mock_response_data = {
        "results": [
            {
                "report_number": "FDA-2023-001",
                "mdr_report_key": "123456",
                "date_received": "20231025",
                "event_type": "Malfunction",
                "device": [
                    {
                        "brand_name": "Software CAD Diagnostic",
                        "manufacturer_d_name": "MedTech Solutions Inc",
                    }
                ],
                "mdr_text": [
                    {"text": "The software crashed during image processing."}
                ],
            }
        ]
    }

    with patch("scrapers.openfda_maude.requests.get") as mock_get:
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = mock_response_data
        mock_get.return_value = mock_resp

        results = scraper.fetch_events("Software CAD Diagnostic")

        assert len(results) == 1
        item = results[0]
        assert item["fonte"] == "openFDA MAUDE"
        assert item["id_segnalazione"] == "FDA-2023-001"
        assert item["data_pubblicazione"] == "25/10/2023"
        assert item["dispositivo"] == "Software CAD Diagnostic"
        assert item["fabbricante"] == "MedTech Solutions Inc"
        assert (
            item["descrizione_evento"]
            == "The software crashed during image processing."
        )
        assert item["tipologia"] == "Malfunction"


def test_fetch_events_http_error(scraper):
    with patch("scrapers.openfda_maude.requests.get") as mock_get:
        mock_resp = MagicMock()
        mock_resp.status_code = 500
        mock_get.return_value = mock_resp

        results = scraper.fetch_events("Software CAD Diagnostic")
        assert results == []


def test_fetch_events_exception(scraper):
    with patch(
        "scrapers.openfda_maude.requests.get",
        side_effect=Exception("Timeout di rete simulato"),
    ):
        results = scraper.fetch_events("Software CAD Diagnostic")
        assert results == []
