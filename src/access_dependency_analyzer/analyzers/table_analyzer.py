"""テーブル解析。"""

from __future__ import annotations

from access_dependency_analyzer.core.models import TableInfo
from access_dependency_analyzer.readers.access_reader import RawTableDef


def analyze_tables(access_file: str, raw_tables: list[RawTableDef]) -> list[TableInfo]:
    """生テーブル定義を TableInfo に変換する。"""
    results: list[TableInfo] = []
    for raw in raw_tables:
        is_linked = bool(raw.connect.strip() or raw.source_table_name.strip())
        results.append(
            TableInfo(
                access_file=access_file,
                table_name=raw.name,
                is_linked=is_linked,
                record_count=raw.record_count,
                primary_key=raw.primary_key,
                fields=raw.fields,
            )
        )
    return results
