"""フォーム・レポート解析。"""

from __future__ import annotations

import re

from access_dependency_analyzer.core.models import FormInfo, ReportInfo
from access_dependency_analyzer.readers.access_reader import RawFormDef, RawReportDef


def _split_record_source(record_source: str) -> tuple[list[str], list[str]]:
    """レコードソースからテーブル名・クエリ名を推定する。"""
    if not record_source or not record_source.strip():
        return [], []

    source = record_source.strip()
    if re.match(r"^\s*SELECT\b", source, re.IGNORECASE):
        return [], []

    if " " in source:
        return [], [source]

    return [source], []


def analyze_forms(access_file: str, raw_forms: list[RawFormDef]) -> list[FormInfo]:
    """フォーム情報を構築する。"""
    results: list[FormInfo] = []
    for raw in raw_forms:
        used_tables, used_queries = _split_record_source(raw.record_source)
        results.append(
            FormInfo(
                access_file=access_file,
                form_name=raw.name,
                record_source=raw.record_source,
                used_tables=used_tables,
                used_queries=used_queries,
            )
        )
    return results


def analyze_reports(access_file: str, raw_reports: list[RawReportDef]) -> list[ReportInfo]:
    """レポート情報を構築する。"""
    results: list[ReportInfo] = []
    for raw in raw_reports:
        used_tables, used_queries = _split_record_source(raw.record_source)
        results.append(
            ReportInfo(
                access_file=access_file,
                report_name=raw.name,
                record_source=raw.record_source,
                used_tables=used_tables,
                used_queries=used_queries,
            )
        )
    return results
