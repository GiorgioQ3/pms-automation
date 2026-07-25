from unittest.mock import MagicMock, patch
import pytest
from scrapers.bfarm import BfArMScraper


@pytest.fixture
def bfarm_scraper():
    return BfArMScraper(timeout=5)


def test_fetch_notices_success(bfarm_scraper):
    mock_response = MagicMock()
    mock_response.status_code = 200

    with patch("requests.get", return_value=mock_response):
        records = bfarm_scraper.fetch_notices("software")
        assert len(records) > 0
        record = records[0]
        assert record["fonte"] == "BfArM (Germania)"
        assert "BfArM-FSN-" in record["id_segnalazione"]
        assert record["url_fonte"].startswith("https://www.bfarm.de")


def test_fetch_notices_http_error(bfarm_scraper):
    mock_response = MagicMock()
    mock_response.status_code = 500

    with patch("requests.get", return_value=mock_response):
        records = bfarm_scraper.fetch_notices("software")
        assert records == []


def test_fetch_notices_exception(bfarm_scraper):
    with patch("requests.get", side_effect=Exception("Connection timeout")):
        records = bfarm_scraper.fetch_notices("software")
        assert records == []
