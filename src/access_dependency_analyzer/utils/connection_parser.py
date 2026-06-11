"""リンクテーブル接続文字列の解析。"""

from __future__ import annotations

import re

from access_dependency_analyzer.utils.path_utils import normalize_access_path_str


DB_PATH_KEYS = (
    "database",
    "dbq",
    "data source",
    "dsn",
)


def extract_database_path(connection_string: str) -> str:
    """接続文字列からリンク先Accessファイルパスを抽出する。"""
    if not connection_string:
        return ""

    for part in connection_string.split(";"):
        if "=" not in part:
            continue
        key, value = part.split("=", 1)
        if key.strip().lower() in DB_PATH_KEYS:
            candidate = value.strip()
            if candidate.lower().endswith((".accdb", ".mdb")):
                return normalize_access_path_str(candidate)
    return ""


def extract_target_table(connection_string: str, source_table_name: str) -> str:
    """リンク先テーブル名を取得する。"""
    if source_table_name:
        return source_table_name.strip()

    match = re.search(r"TABLE\s*=\s*([^;]+)", connection_string, re.IGNORECASE)
    if match:
        return match.group(1).strip().strip("[]")
    return ""
