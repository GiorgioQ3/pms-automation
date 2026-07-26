from core.keyword_parser import KeywordParser


def test_keyword_parser_single():
    res = KeywordParser.parse("mammography")
    assert res == ["mammography"]


def test_keyword_parser_comma_separated():
    res = KeywordParser.parse("mammography, web based viewer, PACS")
    assert res == ["mammography", "web based viewer", "PACS"]


def test_keyword_parser_quotes_and_spaces():
    res = KeywordParser.parse('"mammography", \'web based viewer\' , PACS')
    assert res == ["mammography", "web based viewer", "PACS"]


def test_keyword_parser_duplicates():
    res = KeywordParser.parse("mammography, Mammography, PACS, pacs")
    assert res == ["mammography", "PACS"]


def test_keyword_parser_empty():
    assert KeywordParser.parse("") == []
    assert KeywordParser.parse("   ") == []
