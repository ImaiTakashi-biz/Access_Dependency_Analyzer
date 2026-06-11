"""CSVエクスポート。"""

from __future__ import annotations

import csv
from pathlib import Path

from access_dependency_analyzer.core.models import AnalysisResult


def _write_csv(path: Path, headers: list[str], rows: list[list[object]]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(headers)
        writer.writerows(rows)


def export_csv_files(result: AnalysisResult, output_dir: Path) -> None:
    """解析結果をCSVファイルとして出力する。"""
    output_dir.mkdir(parents=True, exist_ok=True)

    table_rows = [
        [
            table.access_file,
            table.table_name,
            table.is_linked,
            table.record_count if table.record_count is not None else "",
            table.primary_key,
            ";".join(f"{field.name}:{field.data_type}" for field in table.fields),
        ]
        for table in result.tables
    ]
    _write_csv(
        output_dir / "tables.csv",
        ["access_file", "table_name", "is_linked", "record_count", "primary_key", "fields"],
        table_rows,
    )

    linked_rows = [
        [
            linked.access_file,
            linked.table_name,
            linked.source_access,
            linked.target_access,
            linked.target_table,
            linked.connection_string,
        ]
        for linked in result.linked_tables
    ]
    _write_csv(
        output_dir / "linked_tables.csv",
        [
            "access_file",
            "table_name",
            "source_access",
            "target_access",
            "target_table",
            "connection_string",
        ],
        linked_rows,
    )

    query_rows = [
        [
            query.access_file,
            query.query_name,
            query.sql,
            ";".join(query.referenced_tables),
            query.is_update,
            query.is_select,
        ]
        for query in result.queries
    ]
    _write_csv(
        output_dir / "queries.csv",
        [
            "access_file",
            "query_name",
            "sql",
            "referenced_tables",
            "is_update",
            "is_select",
        ],
        query_rows,
    )

    form_rows = [
        [
            form.access_file,
            form.form_name,
            form.record_source,
            ";".join(form.used_tables),
            ";".join(form.used_queries),
        ]
        for form in result.forms
    ]
    _write_csv(
        output_dir / "forms.csv",
        ["access_file", "form_name", "record_source", "used_tables", "used_queries"],
        form_rows,
    )

    report_rows = [
        [
            report.access_file,
            report.report_name,
            report.record_source,
            ";".join(report.used_tables),
            ";".join(report.used_queries),
        ]
        for report in result.reports
    ]
    _write_csv(
        output_dir / "reports.csv",
        [
            "access_file",
            "report_name",
            "record_source",
            "used_tables",
            "used_queries",
        ],
        report_rows,
    )

    vba_rows = [
        [
            module.access_file,
            module.module_name,
            module.code,
            " | ".join(module.sql_strings),
            " | ".join(module.docmd_usages),
            " | ".join(module.dao_usages),
            " | ".join(module.adodb_usages),
        ]
        for module in result.vba_modules
    ]
    _write_csv(
        output_dir / "vba_modules.csv",
        [
            "access_file",
            "module_name",
            "code",
            "sql_strings",
            "docmd_usages",
            "dao_usages",
            "adodb_usages",
        ],
        vba_rows,
    )
