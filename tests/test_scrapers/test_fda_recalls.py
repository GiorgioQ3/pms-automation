from unittest.mock import MagicMock, patch
import pytest
from scrapers.fda_recalls import FDARecallsScraper


@pytest.fixture
def fda_recalls_scraper():
    return FDARecallsScraper(timeout=5)


def test_fetch_recalls_success(fda_recalls_scraper):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "results": [
            {
                "recall_number": "Z-1234-2024",
                "event_date_posted": "20240115",
                "recalling_firm": "Hologic Inc.",
                "product_description": "Mammography SoftwareCAD",
                "reason_for_recall": "Software error causing image misclassification"
            }
        ]
    }

    with patch("requests.get", return_value=mock_response):
        records = fda_recalls_scraper.fetch_recalls("mammography")
        assert len(records) == 1
        record = records[0]
        assert record["fonte"] == "FDA Device Recalls"
        assert record["id_segnalazione"] == "Z-1234-2024"
        assert record["fabbricante"] == "Hologic Inc."
        assert "Mammography" in record["dispositivo"]


def test_fetch_recalls_404_not_found(fda_recalls_scraper):
    mock_response = MagicMock()
    mock_response.status_code = 404

    with patch("requests.get", return_value=mock_response):
        records = fda_recalls_scraper.fetch_recalls("Inesistente")
        assert records == []


def test_fetch_recalls_http_error(fda_recalls_scraper):
    mock_response = MagicMock()
    mock_response.status_code = 500

    with patch("requests.get", return_value=mock_response):
        records = fda_recalls_scraper.fetch_recalls("mammography")
        assert records == []


def test_fetch_recalls_exception(fda_recalls_scraper):
    with patch("requests.get", side_effect=Exception("Timeout simulated")):
        records = fda_recalls_scraper.fetch_recalls("mammography")
        assert records == []
