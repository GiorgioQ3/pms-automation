from tools.probe_sources_config import probe_sources_config


def test_probe_sources_config():
    sources = probe_sources_config("config/sources_spec.json")
    assert isinstance(sources, dict)
    assert len(sources) == 8
    assert "MAUDE" in sources
    assert "Minister of Health" in sources
    assert sources["MAUDE"]["date_format"] == "YYYYMMDD"
