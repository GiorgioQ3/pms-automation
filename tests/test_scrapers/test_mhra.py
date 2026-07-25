from unittest.mock import MagicMock, patch
import pytest
from scrapers.mhra import MHRAScraper


@pytest.fixture
def mhra_scraper():
    return MHRAScraper(timeout=5)


def test_fetch_alerts_success_matching_doc(mhra_scraper):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "details": {
            "collection_groups": [
                {
                    "documents": [
                        {
                            "title": "Mammography Software Alert 2024",
                            "public_updated_at": "2024-01-10T12:00:00Z",
                            "description": "Safety notice for mammography software",
                            "base_path": "/drug-device-alerts/mammography-software-2024"
                        }
                    ]
                }
            ]
        }
    }

    with patch("requests.get", return_value=mock_response):
        records = mhra_scraper.fetch_alerts("mammography")
        assert len(records) == 1
        record = records[0]
        assert record["fonte"] == "MHRA (Regno Unito)"
        assert "MHRA-ALERT-" in record["id_segnalazione"]
        assert "Mammography" in record["dispositivo"]


def test_fetch_alerts_fallback_on_no_match(mhra_scraper):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"details": {"collection_groups": []}}

    with patch("requests.get", return_value=mock_response):
        records = mhra_scraper.fetch_alerts("screening")
        assert len(records) == 1
        assert records[0]["fonte"] == "MHRA (Regno Unito)"


def test_fetch_alerts_http_error(mhra_scraper):
    mock_response = MagicMock()
    mock_response.status_code = 404

    with patch("requests.get", return_value=mock_response):
        records = mhra_scraper.fetch_alerts("screening")
        assert len(records) == 1  # Returns fallback
        assert records[0]["fonte"] == "MHRA (Regno Unito)"
