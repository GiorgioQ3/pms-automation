from unittest.mock import MagicMock, patch
import pytest
from scrapers.nvd_cybersecurity import NVDCybersecurityScraper


@pytest.fixture
def nvd_scraper():
    return NVDCybersecurityScraper(timeout=5)


def test_fetch_vulnerabilities_success(nvd_scraper):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "vulnerabilities": [
            {
                "cve": {
                    "id": "CVE-2024-9999",
                    "published": "2024-02-10T10:00:00.000",
                    "descriptions": [
                        {"lang": "en", "value": "Vulnerability in PACS DICOM viewer component."}
                    ]
                }
            }
        ]
    }

    with patch("requests.get", return_value=mock_response):
        records = nvd_scraper.fetch_vulnerabilities("dicom")
        assert len(records) == 1
        record = records[0]
        assert record["fonte"] == "NIST NVD (Cybersecurity CVE)"
        assert record["id_segnalazione"] == "CVE-2024-9999"
        assert "CVE-2024-9999" in record["dispositivo"]
        assert "Vulnerability in PACS" in record["descrizione_evento"]


def test_fetch_vulnerabilities_http_error(nvd_scraper):
    mock_response = MagicMock()
    mock_response.status_code = 403

    with patch("requests.get", return_value=mock_response):
        records = nvd_scraper.fetch_vulnerabilities("dicom")
        assert records == []


def test_fetch_vulnerabilities_exception(nvd_scraper):
    with patch("requests.get", side_effect=Exception("Connection error")):
        records = nvd_scraper.fetch_vulnerabilities("dicom")
        assert records == []
