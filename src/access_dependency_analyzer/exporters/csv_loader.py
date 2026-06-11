"""CSV から解析結果を読み込む。"""

from __future__ import annotations

import csv
from pathlib import Path

from access_dependency_analyzer.core.models import (
    AnalysisResult,
    FieldInfo,
    FormInfo,
    LinkedTableInfo,
    QueryInfo,
    ReportInfo,
    TableInfo,
    VbaModuleInfo,
)


def _parse_bool(value: str) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes"}


def _parse_optional_int(value: str) -> int | None:
    text = str(value).strip()
    if not text:
        return None
    return int(text)


def _parse_fields(value: str) -> list[FieldInfo]:
    fields: list[FieldInfo] = []
    for item in str(value).split(";"):
        item = item.strip()
        if not item or ":" not in item:
            continue
        name, data_type = item.split(":", 1)
        fields.append(FieldInfo(name=name, data_type=data_type))
    return fields


def _split_list(value: str, separator: str) -> list[str]:
    text = str(value).strip()
    if not text:
        return []
    return [part.strip() for part in text.split(separator) if part.strip()]


def load_analysis_result_from_csv(output_dir: str | Path) -> AnalysisResult:
    """出力済み CSV 群から AnalysisResult を復元する。"""
    base = Path(output_dir)
    result = AnalysisResult()

    tables_path = base / "tables.csv"
    if tables_path.exists():
        with tables_path.open(encoding="utf-8-sig", newline="") as file:
            for row in csv.DictReader(file):
                result.tables.append(
                    TableInfo(
                        access_file=row["access_file"],
                        table_name=row["table_name"],
                        is_linked=_parse_bool(row["is_linked"]),
                        record_count=_parse_optional_int(row.get("record_count", "")),
                        primary_key=row.get("primary_key", ""),
                        fields=_parse_fields(row.get("fields", "")),
                    )
                )

    linked_path = base / "linked_tables.csv"
    if linked_path.exists():
        with linked_path.open(encoding="utf-8-sig", newline="") as file:
            for row in csv.DictReader(file):
                result.linked_tables.append(
                    LinkedTableInfo(
                        access_file=row["access_file"],
                        table_name=row["table_name"],
                        source_access=row["source_access"],
                        target_access=row.get("target_access", ""),
                        target_table=row.get("target_table", ""),
                        connection_string=row.get("connection_string", ""),
                    )
                )

    queries_path = base / "queries.csv"
    if queries_path.exists():
        with queries_path.open(encoding="utf-8-sig", newline="") as file:
            for row in csv.DictReader(file):
                result.queries.append(
                    QueryInfo(
                        access_file=row["access_file"],
                        query_name=row["query_name"],
                        sql=row.get("sql", ""),
                        referenced_tables=_split_list(row.get("referenced_tables", ""), ";"),
                        is_update=_parse_bool(row.get("is_update", "")),
                        is_select=_parse_bool(row.get("is_select", "")),
                    )
                )

    forms_path = base / "forms.csv"
    if forms_path.exists():
        with forms_path.open(encoding="utf-8-sig", newline="") as file:
            for row in csv.DictReader(file):
                result.forms.append(
                    FormInfo(
                        access_file=row["access_file"],
                        form_name=row["form_name"],
                        record_source=row.get("record_source", ""),
                        used_tables=_split_list(row.get("used_tables", ""), ";"),
                        used_queries=_split_list(row.get("used_queries", ""), ";"),
                    )
                )

    reports_path = base / "reports.csv"
    if reports_path.exists():
        with reports_path.open(encoding="utf-8-sig", newline="") as file:
            for row in csv.DictReader(file):
                result.reports.append(
                    ReportInfo(
                        access_file=row["access_file"],
                        report_name=row["report_name"],
                        record_source=row.get("record_source", ""),
                        used_tables=_split_list(row.get("used_tables", ""), ";"),
                        used_queries=_split_list(row.get("used_queries", ""), ";"),
                    )
                )

    vba_path = base / "vba_modules.csv"
    if vba_path.exists():
        with vba_path.open(encoding="utf-8-sig", newline="") as file:
            for row in csv.DictReader(file):
                result.vba_modules.append(
                    VbaModuleInfo(
                        access_file=row["access_file"],
                        module_name=row["module_name"],
                        code=row.get("code", ""),
                        sql_strings=_split_list(row.get("sql_strings", ""), " | "),
                        docmd_usages=_split_list(row.get("docmd_usages", ""), " | "),
                        dao_usages=_split_list(row.get("dao_usages", ""), " | "),
                        adodb_usages=_split_list(row.get("adodb_usages", ""), " | "),
                    )
                )

    result.source_files = _collect_source_files(result)
    return result


def _collect_source_files(result: AnalysisResult) -> list[str]:
    """各成果物に登場する Access ファイルパスを重複なく収集する。"""
    seen: set[str] = set()
    ordered: list[str] = []

    def add_path(path_text: str) -> None:
        if not path_text:
            return
        key = str(Path(path_text)).lower()
        if key in seen:
            return
        seen.add(key)
        ordered.append(path_text)

    for table in result.tables:
        add_path(table.access_file)
    for query in result.queries:
        add_path(query.access_file)
    for form in result.forms:
        add_path(form.access_file)
    for report in result.reports:
        add_path(report.access_file)
    for module in result.vba_modules:
        add_path(module.access_file)

    return sorted(ordered, key=lambda path: Path(path).name.lower())
