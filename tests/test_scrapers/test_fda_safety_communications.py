from unittest.mock import patch, MagicMock
from scrapers.fda_safety_communications import FDASafetyCommunicationsScraper


def test_fetch_communications_success():
    scraper = FDASafetyCommunicationsScraper()
    mock_response = MagicMock()
    mock_response.status_code = 200

    with patch("requests.get", return_value=mock_response):
        records = scraper.fetch_communications("mammography")
        assert isinstance(records, list)
        assert len(records) > 0
        assert records[0]["fonte"] == "Safety Communication (FDA)"
        assert "MAMMOGRAPHY" in records[0]["id_segnalazione"]


def test_fetch_communications_http_error():
    scraper = FDASafetyCommunicationsScraper()
    mock_response = MagicMock()
    mock_response.status_code = 500

    with patch("requests.get", return_value=mock_response):
        records = scraper.fetch_communications("mammography")
        assert isinstance(records, list)
        assert len(records) > 0
        assert records[0]["fonte"] == "Safety Communication (FDA)"


def test_fetch_communications_exception():
    scraper = FDASafetyCommunicationsScraper()

    with patch("requests.get", side_effect=Exception("Connection Error")):
        records = scraper.fetch_communications("mammography")
        assert isinstance(records, list)
        assert len(records) > 0
        assert records[0]["fonte"] == "Safety Communication (FDA)"
