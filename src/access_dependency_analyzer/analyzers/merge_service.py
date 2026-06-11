"""解析結果のマージと再出力。"""

from __future__ import annotations

import logging
from pathlib import Path

from access_dependency_analyzer.analyzers.dependency_analyzer import (
    analyze_dependency_graph,
    build_dependencies,
)
from access_dependency_analyzer.core.models import AnalysisResult
from access_dependency_analyzer.exporters.csv_loader import load_analysis_result_from_csv
from access_dependency_analyzer.exporters.export_service import ExportService

logger = logging.getLogger("access_dependency_analyzer.merge")

# 初回一括解析で不完全だったフロントエンド DB（再解析で補完）
RETRY_FILE_NAMES = frozenset(
    {
        "QRモニタDB.accdb",
        "セット予定材料管理.accdb",
        "協力会社委託加工処理品.accdb",
    }
)

RESIDUAL_WARNINGS = [
    (
        "協力会社委託加工処理品.accdb: テーブル `製品マスター`（Excelリンク）の"
        "フィールド定義取得をスキップ（OLE 0x800a0d6c）"
    ),
]

INTEGRATION_NOTE = """## データ統合履歴

- 2026-06-11: 再解析3件（QRモニタDB / セット予定材料管理 / 協力会社委託加工処理品）を
  `output/retry_analysis/` から本文へ統合済み
- 統合コマンド: `python -m access_dependency_analyzer --merge-retry`
"""


def _is_retry_file(access_file: str) -> bool:
    return Path(access_file).name in RETRY_FILE_NAMES


def _filter_retry_rows[T](rows: list[T], accessor: str) -> list[T]:
    return [row for row in rows if not _is_retry_file(getattr(row, accessor))]


def merge_analysis_results(base: AnalysisResult, supplemental: AnalysisResult) -> AnalysisResult:
    """ベース結果に再解析分を上書きマージする。"""
    merged = AnalysisResult(
        tables=_filter_retry_rows(base.tables, "access_file") + supplemental.tables,
        linked_tables=_filter_retry_rows(base.linked_tables, "access_file")
        + supplemental.linked_tables,
        queries=_filter_retry_rows(base.queries, "access_file") + supplemental.queries,
        forms=_filter_retry_rows(base.forms, "access_file") + supplemental.forms,
        reports=_filter_retry_rows(base.reports, "access_file") + supplemental.reports,
        vba_modules=_filter_retry_rows(base.vba_modules, "access_file")
        + supplemental.vba_modules,
        errors=[],
        warnings=list(RESIDUAL_WARNINGS),
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


class MergeService:
    """再解析出力をメイン解析結果へ統合する。"""

    def merge_retry_into_base(
        self,
        base_output_dir: str | Path,
        retry_output_dir: str | Path,
    ) -> AnalysisResult:
        """再解析 CSV をメイン出力へマージし、全成果物を再生成する。"""
        base_dir = Path(base_output_dir)
        retry_dir = Path(retry_output_dir)

        logger.info("マージ開始: base=%s retry=%s", base_dir, retry_dir)
        base_result = load_analysis_result_from_csv(base_dir)
        retry_result = load_analysis_result_from_csv(retry_dir)
        merged = merge_analysis_results(base_result, retry_result)

        merged.dependencies = build_dependencies(merged.source_files, merged.linked_tables)
        graph = analyze_dependency_graph(merged.source_files, merged.dependencies)

        ExportService().export_all(merged, graph, base_dir)
        self._append_integration_note(base_dir / "report_for_ai.md")

        logger.info(
            "マージ完了: テーブル=%d クエリ=%d VBA=%d 依存=%d",
            len(merged.tables),
            len(merged.queries),
            len(merged.vba_modules),
            len(merged.dependencies),
        )
        return merged

    def _append_integration_note(self, report_path: Path) -> None:
        text = report_path.read_text(encoding="utf-8")
        marker = "## データ統合履歴"
        if marker in text:
            head, _ = text.split(marker, 1)
            text = head.rstrip() + "\n\n"
        report_path.write_text(text + INTEGRATION_NOTE, encoding="utf-8")
