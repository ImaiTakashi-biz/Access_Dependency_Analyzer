"""クエリ解析。"""

from __future__ import annotations

from access_dependency_analyzer.core.models import QueryInfo
from access_dependency_analyzer.readers.access_reader import RawQueryDef
from access_dependency_analyzer.utils.sql_parser import (
    classify_query,
    extract_referenced_tables,
)


def analyze_queries(access_file: str, raw_queries: list[RawQueryDef]) -> list[QueryInfo]:
    """クエリ情報を構築する。"""
    results: list[QueryInfo] = []
    for raw in raw_queries:
        is_update, is_select = classify_query(raw.sql)
        results.append(
            QueryInfo(
                access_file=access_file,
                query_name=raw.name,
                sql=raw.sql,
                referenced_tables=extract_referenced_tables(raw.sql),
                is_update=is_update,
                is_select=is_select,
            )
        )
    return results
