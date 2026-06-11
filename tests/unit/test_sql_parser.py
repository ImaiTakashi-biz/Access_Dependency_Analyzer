"""SQL解析のテスト。"""

from access_dependency_analyzer.utils.sql_parser import (
    classify_query,
    extract_referenced_tables,
    extract_sql_strings_from_vba,
)


def test_classify_select_query() -> None:
    is_update, is_select = classify_query("SELECT * FROM T_製品")
    assert is_update is False
    assert is_select is True


def test_classify_update_query() -> None:
    is_update, is_select = classify_query("UPDATE T_製品 SET name='A'")
    assert is_update is True
    assert is_select is False


def test_extract_referenced_tables() -> None:
    sql = "SELECT a.* FROM T_製品 AS a INNER JOIN T_顧客 ON a.id = T_顧客.id"
    tables = extract_referenced_tables(sql)
    assert "T_製品" in tables
    assert "T_顧客" in tables


def test_extract_sql_strings_from_vba() -> None:
    code = '''
    Dim sql As String
    sql = "SELECT * FROM T_不具合 WHERE status = 'OPEN'"
    '''
    sql_strings = extract_sql_strings_from_vba(code)
    assert len(sql_strings) >= 1
    assert "T_不具合" in sql_strings[0]
