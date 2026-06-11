"""リンクテーブル接続文字列の解析。"""

from __future__ import annotations

import re
from pathlib import Path


DB_PATH_KEYS = (
    "database",
    "dbq",
    "data source",
    "dsn",
)


def normalize_access_path(path_text: str) -> str:
    """Accessファイルパスを正規化する。"""
    cleaned = path_text.strip().strip('"').strip("'")
    if not cleaned:
        return ""
    return str(Path(cleaned).resolve())


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
                return normalize_access_path(candidate)
    return ""


def extract_target_table(connection_string: str, source_table_name: str) -> str:
    """リンク先テーブル名を取得する。"""
    if source_table_name:
        return source_table_name.strip()

    match = re.search(r"TABLE\s*=\s*([^;]+)", connection_string, re.IGNORECASE)
    if match:
        return match.group(1).strip().strip("[]")
    return ""
