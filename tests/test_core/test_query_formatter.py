from core.query_formatter import SourceQueryFormatter


def test_source_query_formatter():
    formatter = SourceQueryFormatter("config/sources_spec.json")

    # Test date formatting
    assert formatter.format_date("2024-01-15", "DD/MM/YYYY") == "15/01/2024"
    assert formatter.format_date("2024-01-15", "YYYYMMDD") == "20240115"
    assert formatter.format_date("2024-01-15", "DD.MM.YYYY") == "15.01.2024"

    # Test keyword formatting
    assert formatter.format_keyword("DICOM viewer", "quoted_field_query") == '"DICOM viewer"'
    assert formatter.format_keyword("DICOM viewer", "plain_text") == "DICOM viewer"

    # Test source params
    kw, start, end = formatter.get_formatted_params("MAUDE", "DICOM viewer", "2024-01-01", "2024-12-31")
    assert kw == '"DICOM viewer"'
    assert start == "20240101"
    assert end == "20241231"
