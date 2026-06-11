"""SQL文字列の簡易解析。"""

from __future__ import annotations

import re


UPDATE_KEYWORDS = (
    "INSERT",
    "UPDATE",
    "DELETE",
    "MERGE",
    "CREATE",
    "ALTER",
    "DROP",
    "TRUNCATE",
)

SELECT_KEYWORDS = ("SELECT", "WITH")


def classify_query(sql: str) -> tuple[bool, bool]:
    """更新系・参照系クエリを判定する。"""
    if not sql or not sql.strip():
        return False, False

    normalized = re.sub(r"\s+", " ", sql.strip().upper())
    first_token = normalized.split(" ", 1)[0] if normalized else ""

    is_update = first_token in UPDATE_KEYWORDS
    is_select = first_token in SELECT_KEYWORDS or (
        not is_update and "SELECT" in normalized
    )
    return is_update, is_select


def extract_referenced_tables(sql: str) -> list[str]:
    """SQLから参照テーブル名を抽出する（簡易版）。"""
    if not sql:
        return []

    tables: set[str] = set()
    patterns = (
        r"\bFROM\s+\[?([A-Za-z_][\w]*)\]?",
        r"\bJOIN\s+\[?([A-Za-z_][\w]*)\]?",
        r"\bINTO\s+\[?([A-Za-z_][\w]*)\]?",
        r"\bUPDATE\s+\[?([A-Za-z_][\w]*)\]?",
    )
    for pattern in patterns:
        for match in re.finditer(pattern, sql, re.IGNORECASE):
            name = match.group(1)
            if name.upper() not in {"SELECT", "WHERE", "SET", "VALUES"}:
                tables.add(name)
    return sorted(tables)


def extract_sql_strings_from_vba(code: str) -> list[str]:
    """VBAコードからSQL文字列を抽出する。"""
    if not code:
        return []

    patterns = (
        r'"(?:[^"\\]|\\.)*"',
        r"'(?:[^'\\]|\\.)*'",
    )
    sql_keywords = ("SELECT", "INSERT", "UPDATE", "DELETE", "FROM", "INTO")
    results: list[str] = []

    for pattern in patterns:
        for match in re.finditer(pattern, code, re.IGNORECASE | re.DOTALL):
            text = match.group(0)[1:-1]
            upper = text.upper()
            if any(keyword in upper for keyword in sql_keywords):
                if len(text) >= 10:
                    results.append(text)

    return results


def extract_api_usages(code: str, api_name: str) -> list[str]:
    """VBAコード内のAPI利用箇所を抽出する。"""
    if not code:
        return []

    pattern = rf"\b{re.escape(api_name)}\b[^'\n\r]*"
    return [line.strip() for line in re.findall(pattern, code, re.IGNORECASE)]
