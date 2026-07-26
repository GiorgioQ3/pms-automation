from unittest.mock import MagicMock, patch
from datetime import date
import pytest
from main import PMSOrchestrator, parse_arguments


@pytest.fixture
def orchestrator(tmp_path):
    config_file = tmp_path / "test_config.json"
    output_file = tmp_path / "test_pms_output.xlsx"
    config_file.write_text(
        f'{{"search_keyword": "Software", "competitors": ["Siemens"], "output_excel_path": "{output_file.as_posix()}"}}',
        encoding="utf-8"
    )
    return PMSOrchestrator(config_path=str(config_file))


def test_orchestrator_pipeline_success(orchestrator):
    mock_it_data = [
        {
            "fonte": "Ministero della Salute IT",
            "id_segnalazione": "IT-001",
            "data_pubblicazione": "10/01/2024",
            "fabbricante": "ACME Med",
            "dispositivo": "Software AI",
            "descrizione_evento": "Malfunzionamento modulo CAD",
            "tipologia": "Avviso di Sicurezza",
            "url_fonte": "https://example.com/1"
        }
    ]

    mock_fda_data = [
        {
            "fonte": "openFDA MAUDE",
            "id_segnalazione": "FDA-001",
            "data_pubblicazione": "15/01/2024",
            "fabbricante": "Siemens Healthineers",
            "dispositivo": "CAD Diagnostic Software",
            "descrizione_evento": "Software crash during scan",
            "tipologia": "Malfunction",
            "url_fonte": "https://example.com/2"
        }
    ]

    with patch.object(orchestrator.min_salute_scraper, 'fetch_data', return_value=mock_it_data), \
         patch.object(orchestrator.openfda_scraper, 'fetch_events', return_value=mock_fda_data), \
         patch.object(orchestrator.fda_recalls_scraper, 'fetch_recalls', return_value=[]), \
         patch.object(orchestrator.fda_safety_comm_scraper, 'fetch_communications', return_value=[]), \
         patch.object(orchestrator.fda_letters_scraper, 'fetch_letters', return_value=[]), \
         patch.object(orchestrator.nvd_scraper, 'fetch_vulnerabilities', return_value=[]), \
         patch.object(orchestrator.bfarm_scraper, 'fetch_notices', return_value=[]), \
         patch.object(orchestrator.mhra_scraper, 'fetch_alerts', return_value=[]):

        result_file = orchestrator.run(search_term="Software", competitors=["Siemens"])
        assert result_file.endswith(".xlsx")


def test_orchestrator_run_pipeline_multi_keyword(orchestrator):
    with patch.object(orchestrator.min_salute_scraper, 'fetch_data', return_value=[]), \
         patch.object(orchestrator.openfda_scraper, 'fetch_events', return_value=[]), \
         patch.object(orchestrator.fda_recalls_scraper, 'fetch_recalls', return_value=[]), \
         patch.object(orchestrator.fda_safety_comm_scraper, 'fetch_communications', return_value=[]), \
         patch.object(orchestrator.fda_letters_scraper, 'fetch_letters', return_value=[]), \
         patch.object(orchestrator.nvd_scraper, 'fetch_vulnerabilities', return_value=[]), \
         patch.object(orchestrator.bfarm_scraper, 'fetch_notices', return_value=[]), \
         patch.object(orchestrator.mhra_scraper, 'fetch_alerts', return_value=[]):

        res = orchestrator.run_pipeline(
            keyword_input="mammography, web based viewer",
            start_date="2024-01-01",
            end_date="2024-12-31"
        )
        assert res["excel_filename"] == "PMS_Report_DPR-385_Period_2024-01-01_to_2024-12-31.xlsx"
        assert res["keywords"] == ["mammography", "web based viewer"]
        assert "keyword_stats" in res


def test_orchestrator_failsafe_empty_sources(orchestrator):
    with patch.object(orchestrator.min_salute_scraper, 'fetch_data', return_value=[]), \
         patch.object(orchestrator.openfda_scraper, 'fetch_events', return_value=[]), \
         patch.object(orchestrator.fda_recalls_scraper, 'fetch_recalls', return_value=[]), \
         patch.object(orchestrator.fda_safety_comm_scraper, 'fetch_communications', return_value=[]), \
         patch.object(orchestrator.fda_letters_scraper, 'fetch_letters', return_value=[]), \
         patch.object(orchestrator.nvd_scraper, 'fetch_vulnerabilities', return_value=[]), \
         patch.object(orchestrator.bfarm_scraper, 'fetch_notices', return_value=[]), \
         patch.object(orchestrator.mhra_scraper, 'fetch_alerts', return_value=[]):

        result_file = orchestrator.run(search_term="Inesistente", competitors=[])
        assert result_file.endswith(".xlsx")


def test_orchestrator_date_range_naming(orchestrator):
    with patch.object(orchestrator.min_salute_scraper, 'fetch_data', return_value=[]), \
         patch.object(orchestrator.openfda_scraper, 'fetch_events', return_value=[]), \
         patch.object(orchestrator.fda_recalls_scraper, 'fetch_recalls', return_value=[]), \
         patch.object(orchestrator.fda_safety_comm_scraper, 'fetch_communications', return_value=[]), \
         patch.object(orchestrator.fda_letters_scraper, 'fetch_letters', return_value=[]), \
         patch.object(orchestrator.nvd_scraper, 'fetch_vulnerabilities', return_value=[]), \
         patch.object(orchestrator.bfarm_scraper, 'fetch_notices', return_value=[]), \
         patch.object(orchestrator.mhra_scraper, 'fetch_alerts', return_value=[]):

        result_file = orchestrator.run(
            search_term="Software",
            start_date=date(2024, 1, 1),
            end_date=date(2024, 12, 31)
        )
        assert "PMS_Report_DPR-385_Period_2024-01-01_to_2024-12-31.xlsx" in result_file


def test_orchestrator_config_loading(tmp_path):
    config_file = tmp_path / "test_config.json"
    config_file.write_text('{"search_keyword": "TestCAD", "competitors": ["CompA"]}', encoding="utf-8")
    
    orchestrator = PMSOrchestrator(config_path=str(config_file))
    assert orchestrator.config["search_keyword"] == "TestCAD"
    assert orchestrator.config["competitors"] == ["CompA"]


def test_orchestrator_config_loading_corrupted(tmp_path):
    config_file = tmp_path / "corrupted_config.json"
    config_file.write_text("invalid json {", encoding="utf-8")
    
    orchestrator = PMSOrchestrator(config_path=str(config_file))
    assert orchestrator.config["search_keyword"] == "mammography"


def test_parse_arguments(monkeypatch):
    test_args = ["main.py", "-k", "AI_Device", "-o", "Custom_Output.xlsx", "-comp", "Siemens,GE"]
    monkeypatch.setattr("sys.argv", test_args)
    args = parse_arguments()
    assert args.keyword == "AI_Device"
    assert args.output == "Custom_Output.xlsx"
    assert args.competitors == "Siemens,GE"
