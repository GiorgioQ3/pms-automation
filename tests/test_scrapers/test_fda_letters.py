from unittest.mock import patch, MagicMock
from scrapers.fda_letters import FDALettersScraper


def test_fetch_letters_success():
    scraper = FDALettersScraper()
    mock_response = MagicMock()
    mock_response.status_code = 200

    with patch("requests.get", return_value=mock_response):
        records = scraper.fetch_letters("mammography")
        assert isinstance(records, list)
        assert len(records) > 0
        assert records[0]["fonte"] == "Letters to Health Care Providers (FDA)"
        assert "MAMMOGRAPHY" in records[0]["id_segnalazione"]


def test_fetch_letters_http_error():
    scraper = FDALettersScraper()
    mock_response = MagicMock()
    mock_response.status_code = 404

    with patch("requests.get", return_value=mock_response):
        records = scraper.fetch_letters("mammography")
        assert isinstance(records, list)
        assert len(records) > 0
        assert records[0]["fonte"] == "Letters to Health Care Providers (FDA)"


def test_fetch_letters_exception():
    scraper = FDALettersScraper()

    with patch("requests.get", side_effect=Exception("Timeout Error")):
        records = scraper.fetch_letters("mammography")
        assert isinstance(records, list)
        assert len(records) > 0
        assert records[0]["fonte"] == "Letters to Health Care Providers (FDA)"
