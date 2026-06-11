"""解析結果マージのテスト。"""

from __future__ import annotations

from access_dependency_analyzer.analyzers.merge_service import (
    collect_file_names_from_result,
    merge_analysis_results,
)
from access_dependency_analyzer.core.models import (
    AnalysisResult,
    QueryInfo,
    TableInfo,
)


def test_merge_analysis_results_replaces_retry_files() -> None:
    base = AnalysisResult(
        source_files=[r"C:\data\QRモニタDB.accdb", r"C:\data\現品票DB.accdb"],
        tables=[
            TableInfo(
                access_file=r"C:\data\QRモニタDB.accdb",
                table_name="old_table",
                is_linked=False,
                record_count=1,
                primary_key="ID",
            ),
            TableInfo(
                access_file=r"C:\data\現品票DB.accdb",
                table_name="t_現品票履歴",
                is_linked=False,
                record_count=10,
                primary_key="ID",
            ),
        ],
        queries=[
            QueryInfo(
                access_file=r"C:\data\QRモニタDB.accdb",
                query_name="old_query",
                sql="SELECT 1",
            )
        ],
    )
    supplemental = AnalysisResult(
        source_files=[r"\\server\share\QRモニタDB.accdb"],
        tables=[
            TableInfo(
                access_file=r"\\server\share\QRモニタDB.accdb",
                table_name="t_QR履歴",
                is_linked=True,
                record_count=100,
                primary_key="ID",
            )
        ],
        queries=[
            QueryInfo(
                access_file=r"\\server\share\QRモニタDB.accdb",
                query_name="Q_履歴",
                sql="SELECT * FROM t_QR履歴",
                is_select=True,
            )
        ],
    )

    merged = merge_analysis_results(
        base,
        supplemental,
        replace_file_names=frozenset({"QRモニタDB.accdb"}),
    )

    table_names = {table.table_name for table in merged.tables}
    assert "old_table" not in table_names
    assert "t_QR履歴" in table_names
    assert "t_現品票履歴" in table_names
    assert merged.queries[0].query_name == "Q_履歴"
    assert merged.errors == []


def test_collect_file_names_from_result() -> None:
    result = AnalysisResult(
        source_files=[r"C:\data\foo.accdb"],
        tables=[
            TableInfo(
                access_file=r"\\server\share\bar.accdb",
                table_name="t_1",
                is_linked=False,
                record_count=1,
                primary_key="",
            )
        ],
    )
    names = collect_file_names_from_result(result)
    assert names == frozenset({"foo.accdb", "bar.accdb"})
