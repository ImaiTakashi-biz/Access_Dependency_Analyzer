"""解析結果のマージと再出力。"""

from __future__ import annotations

import logging
from datetime import date
from pathlib import Path

from access_dependency_analyzer.analyzers.dependency_analyzer import (
    analyze_dependency_graph,
    build_dependencies,
)
from access_dependency_analyzer.core.models import AnalysisResult
from access_dependency_analyzer.exporters.csv_loader import load_analysis_result_from_csv
from access_dependency_analyzer.exporters.export_service import ExportService

logger = logging.getLogger("access_dependency_analyzer.merge")


def collect_file_names_from_result(result: AnalysisResult) -> frozenset[str]:
    """解析結果に含まれる Access ファイル名（拡張子付き）を収集する。"""
    names: set[str] = set()

    def add_path(path_text: str) -> None:
        if not path_text:
            return
        name = Path(path_text.replace("/", "\\")).name
        if name:
            names.add(name)

    for path in result.source_files:
        add_path(path)
    for table in result.tables:
        add_path(table.access_file)
    for linked in result.linked_tables:
        add_path(linked.access_file)
    for query in result.queries:
        add_path(query.access_file)
    for form in result.forms:
        add_path(form.access_file)
    for report in result.reports:
        add_path(report.access_file)
    for module in result.vba_modules:
        add_path(module.access_file)

    return frozenset(names)


def _should_replace(access_file: str, replace_file_names: frozenset[str]) -> bool:
    return Path(access_file).name in replace_file_names


def _filter_rows[T](rows: list[T], accessor: str, replace_file_names: frozenset[str]) -> list[T]:
    return [
        row
        for row in rows
        if not _should_replace(getattr(row, accessor), replace_file_names)
    ]


def merge_analysis_results(
    base: AnalysisResult,
    supplemental: AnalysisResult,
    replace_file_names: frozenset[str] | None = None,
    extra_warnings: list[str] | None = None,
) -> AnalysisResult:
    """ベース結果に再解析分を上書きマージする。"""
    targets = replace_file_names or collect_file_names_from_result(supplemental)
    warnings = list(extra_warnings or supplemental.warnings or [])

    merged = AnalysisResult(
        tables=_filter_rows(base.tables, "access_file", targets) + supplemental.tables,
        linked_tables=_filter_rows(base.linked_tables, "access_file", targets)
        + supplemental.linked_tables,
        queries=_filter_rows(base.queries, "access_file", targets) + supplemental.queries,
        forms=_filter_rows(base.forms, "access_file", targets) + supplemental.forms,
        reports=_filter_rows(base.reports, "access_file", targets) + supplemental.reports,
        vba_modules=_filter_rows(base.vba_modules, "access_file", targets)
        + supplemental.vba_modules,
        errors=[],
        warnings=warnings,
    )
    merged.source_files = _collect_source_files(merged, base.source_files, supplemental.source_files)
    return merged


def _collect_source_files(
    merged: AnalysisResult,
    base_files: list[str],
    supplemental_files: list[str],
) -> list[str]:
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

    for path in base_files:
        add_path(path)
    for path in supplemental_files:
        add_path(path)
    for table in merged.tables:
        add_path(table.access_file)

    return sorted(ordered, key=lambda path: Path(path).name.lower())


def build_integration_note(replaced_file_names: frozenset[str]) -> str:
    """データ統合履歴セクションの Markdown を生成する。"""
    names = ", ".join(sorted(replaced_file_names))
    today = date.today().isoformat()
    return f"""## データ統合履歴

- {today}: 再解析分を統合（対象: {names}）
- 統合コマンド: `python -m access_dependency_analyzer --merge-retry`
"""


class MergeService:
    """再解析出力をメイン解析結果へ統合する。"""

    def merge_retry_into_base(
        self,
        base_output_dir: str | Path,
        retry_output_dir: str | Path,
        replace_file_names: frozenset[str] | None = None,
        extra_warnings: list[str] | None = None,
    ) -> AnalysisResult:
        """再解析 CSV をメイン出力へマージし、全成果物を再生成する。"""
        base_dir = Path(base_output_dir)
        retry_dir = Path(retry_output_dir)

        if not base_dir.is_dir():
            raise FileNotFoundError(f"統合先ディレクトリが見つかりません: {base_dir}")
        if not retry_dir.is_dir():
            raise FileNotFoundError(f"再解析ディレクトリが見つかりません: {retry_dir}")

        logger.info("マージ開始: base=%s retry=%s", base_dir, retry_dir)
        base_result = load_analysis_result_from_csv(base_dir)
        retry_result = load_analysis_result_from_csv(retry_dir)

        targets = replace_file_names or collect_file_names_from_result(retry_result)
        if not targets:
            raise ValueError("上書き対象の Access ファイルが特定できませんでした。")

        merged = merge_analysis_results(
            base_result,
            retry_result,
            replace_file_names=targets,
            extra_warnings=extra_warnings,
        )

        merged.dependencies = build_dependencies(merged.source_files, merged.linked_tables)
        graph = analyze_dependency_graph(merged.source_files, merged.dependencies)

        ExportService().export_all(merged, graph, base_dir)
        self._append_integration_note(base_dir / "report_for_ai.md", targets)

        logger.info(
            "マージ完了: 対象=%d テーブル=%d クエリ=%d VBA=%d 依存=%d",
            len(targets),
            len(merged.tables),
            len(merged.queries),
            len(merged.vba_modules),
            len(merged.dependencies),
        )
        return merged

    def _append_integration_note(
        self,
        report_path: Path,
        replaced_file_names: frozenset[str],
    ) -> None:
        text = report_path.read_text(encoding="utf-8")
        marker = "## データ統合履歴"
        if marker in text:
            head, _ = text.split(marker, 1)
            text = head.rstrip() + "\n\n"
        report_path.write_text(
            text + build_integration_note(replaced_file_names),
            encoding="utf-8",
        )
