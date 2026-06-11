"""リンクテーブル解析。"""

from __future__ import annotations

from access_dependency_analyzer.core.models import LinkedTableInfo
from access_dependency_analyzer.readers.access_reader import RawTableDef
from access_dependency_analyzer.utils.connection_parser import (
    extract_database_path,
    extract_target_table,
)


def analyze_linked_tables(
    access_file: str,
    raw_tables: list[RawTableDef],
) -> list[LinkedTableInfo]:
    """リンクテーブル情報を抽出する。"""
    linked_tables: list[LinkedTableInfo] = []

    for raw in raw_tables:
        connect = raw.connect.strip()
        if not connect and not raw.source_table_name.strip():
            continue

        target_access = extract_database_path(connect)
        target_table = extract_target_table(connect, raw.source_table_name)
        linked_tables.append(
            LinkedTableInfo(
                access_file=access_file,
                table_name=raw.name,
                source_access=access_file,
                target_access=target_access,
                target_table=target_table,
                connection_string=connect,
            )
        )
    return linked_tables
