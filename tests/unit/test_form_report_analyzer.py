"""フォーム・レポート解析のテスト。"""

from __future__ import annotations

from access_dependency_analyzer.analyzers.form_report_analyzer import _split_record_source


def test_split_record_source_table_name() -> None:
    tables, queries = _split_record_source("t_受注")
    assert tables == ["t_受注"]
    assert queries == []


def test_split_record_source_query_name_with_space() -> None:
    tables, queries = _split_record_source("Q_セット予定表 抽出")
    assert tables == []
    assert queries == ["Q_セット予定表 抽出"]


def test_split_record_source_select_sql() -> None:
    sql = (
        "SELECT t_受注.品番, t_製品マスタ.品名 "
        "FROM t_受注 INNER JOIN t_製品マスタ ON t_受注.品番 = t_製品マスタ.品番"
    )
    tables, queries = _split_record_source(sql)
    assert "t_受注" in tables
    assert "t_製品マスタ" in tables
    assert queries == []
