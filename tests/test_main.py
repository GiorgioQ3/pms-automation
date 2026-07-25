from unittest.mock import MagicMock, patch
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
         patch.object(orchestrator.openfda_scraper, 'fetch_events', return_value=mock_fda_data):

        result_file = orchestrator.run(search_term="Software", competitors=["Siemens"])
        assert result_file.endswith(".xlsx")


def test_orchestrator_failsafe_empty_sources(orchestrator):
    with patch.object(orchestrator.min_salute_scraper, 'fetch_data', return_value=[]), \
         patch.object(orchestrator.openfda_scraper, 'fetch_events', return_value=[]):

        result_file = orchestrator.run(search_term="Inesistente", competitors=[])
        assert result_file.endswith(".xlsx")


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
    assert orchestrator.config["search_keyword"] == "Software"


def test_parse_arguments(monkeypatch):
    test_args = ["main.py", "-k", "AI_Device", "-o", "Custom_Output.xlsx", "-comp", "Siemens,GE"]
    monkeypatch.setattr("sys.argv", test_args)
    args = parse_arguments()
    assert args.keyword == "AI_Device"
    assert args.output == "Custom_Output.xlsx"
    assert args.competitors == "Siemens,GE"
