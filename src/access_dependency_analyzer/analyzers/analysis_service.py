"""解析オーケストレーション。"""

from __future__ import annotations

import logging
from pathlib import Path

from access_dependency_analyzer.analyzers.dependency_analyzer import (
    analyze_dependency_graph,
    build_dependencies,
)
from access_dependency_analyzer.analyzers.form_report_analyzer import (
    analyze_forms,
    analyze_reports,
)
from access_dependency_analyzer.analyzers.link_analyzer import analyze_linked_tables
from access_dependency_analyzer.analyzers.query_analyzer import analyze_queries
from access_dependency_analyzer.analyzers.table_analyzer import analyze_tables
from access_dependency_analyzer.analyzers.vba_analyzer import analyze_vba_modules
from access_dependency_analyzer.exporters.export_service import ExportService
from access_dependency_analyzer.core.constants import SUPPORTED_EXTENSIONS
from access_dependency_analyzer.core.models import AnalysisResult
from access_dependency_analyzer.readers.access_reader import AccessReader
from access_dependency_analyzer.readers.vba_reader import read_vba_modules

logger = logging.getLogger("access_dependency_analyzer.analyzers")


class AnalysisService:
    """Accessファイル群を解析するサービス。"""

    def analyze_files(
        self,
        file_paths: list[str | Path],
        output_dir: str | Path | None = None,
    ) -> AnalysisResult:
        """複数Accessファイルを解析し、結果を出力する。"""
        normalized_paths = self._normalize_input_paths(file_paths)
        result = AnalysisResult(source_files=[str(path) for path in normalized_paths])

        for file_path in normalized_paths:
            self._analyze_single_file(file_path, result)

        result.dependencies = build_dependencies(result.source_files, result.linked_tables)
        graph = analyze_dependency_graph(result.source_files, result.dependencies)

        export_dir = Path(output_dir) if output_dir else result.output_dir
        ExportService().export_all(result, graph, export_dir)
        logger.info("解析結果を出力しました: %s", export_dir.resolve())
        return result

    def _normalize_input_paths(self, file_paths: list[str | Path]) -> list[Path]:
        paths: list[Path] = []
        for file_path in file_paths:
            path = Path(file_path).resolve()
            if path.suffix.lower() not in SUPPORTED_EXTENSIONS:
                raise ValueError(f"未対応のファイル形式です: {path}")
            paths.append(path)

        unique_paths: list[Path] = []
        seen: set[str] = set()
        for path in paths:
            key = str(path).lower()
            if key not in seen:
                seen.add(key)
                unique_paths.append(path)
        return unique_paths

    def _analyze_single_file(self, file_path: Path, result: AnalysisResult) -> None:
        access_file = str(file_path)
        logger.info("解析開始: %s", access_file)

        try:
            with AccessReader(file_path) as reader:
                raw_tables = reader.read_tables()
                result.tables.extend(analyze_tables(access_file, raw_tables))
                result.linked_tables.extend(
                    analyze_linked_tables(access_file, raw_tables)
                )
                result.queries.extend(
                    analyze_queries(access_file, reader.read_queries())
                )
                result.forms.extend(analyze_forms(access_file, reader.read_forms()))
                result.reports.extend(
                    analyze_reports(access_file, reader.read_reports())
                )

                if reader.backend == "pyodbc" and result.linked_tables:
                    result.warnings.append(
                        f"{file_path.name}: pyodbcモードではリンク接続文字列が取得できない場合があります。"
                        " ACE + DAO 環境での再解析を推奨します。"
                    )
        except Exception as error:
            message = f"{file_path.name}: {error}"
            logger.error("解析エラー: %s", message)
            result.errors.append(message)

        try:
            raw_vba = read_vba_modules(file_path)
            result.vba_modules.extend(analyze_vba_modules(access_file, raw_vba))
        except Exception as error:
            message = f"{file_path.name} VBA解析: {error}"
            logger.warning(message)
            result.warnings.append(message)
