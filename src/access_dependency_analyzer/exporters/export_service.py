"""エクスポート統合サービス。"""

from __future__ import annotations

from pathlib import Path

from access_dependency_analyzer.analyzers.dependency_analyzer import DependencyGraph
from access_dependency_analyzer.exporters.ai_report_exporter import export_ai_report
from access_dependency_analyzer.exporters.csv_exporter import export_csv_files
from access_dependency_analyzer.exporters.html_exporter import export_html
from access_dependency_analyzer.exporters.markdown_exporter import export_relationship_markdown
from access_dependency_analyzer.exporters.mermaid_exporter import export_mermaid
from access_dependency_analyzer.core.models import AnalysisResult


class ExportService:
    """解析結果の一括エクスポート。"""

    def export_all(
        self,
        result: AnalysisResult,
        graph: DependencyGraph,
        output_dir: str | Path,
    ) -> Path:
        """全出力ファイルを生成する。"""
        target_dir = Path(output_dir)
        target_dir.mkdir(parents=True, exist_ok=True)

        export_csv_files(result, target_dir)
        export_relationship_markdown(graph, target_dir)
        export_mermaid(graph, target_dir)
        export_html(result, target_dir)
        export_ai_report(result, graph, target_dir)
        return target_dir
