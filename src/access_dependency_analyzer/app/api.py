"""pywebview API ブリッジ。"""

from __future__ import annotations

import logging
import tkinter as tk
from pathlib import Path
from tkinter import filedialog

from access_dependency_analyzer.analyzers.analysis_service import AnalysisService
from access_dependency_analyzer.core.constants import resolve_output_dir

logger = logging.getLogger("access_dependency_analyzer.app.api")


class AnalyzerApi:
    """フロントエンドから呼び出される Python API。"""

    def __init__(self, workspace_dir: str | Path) -> None:
        self.workspace_dir = Path(workspace_dir).resolve()

    def choose_files(self) -> list[str]:
        """ファイル選択ダイアログを表示する。"""
        root = tk.Tk()
        root.withdraw()
        root.attributes("-topmost", True)
        try:
            paths = filedialog.askopenfilenames(
                title="Accessファイルを選択",
                filetypes=[
                    ("Access Database", "*.accdb *.mdb"),
                    ("ACCDB", "*.accdb"),
                    ("MDB", "*.mdb"),
                ],
            )
        finally:
            root.destroy()
        return [str(path) for path in paths]

    def analyze_files(self, file_paths: list[str]) -> dict[str, object]:
        """選択ファイルを解析する。"""
        if not file_paths:
            return {"success": False, "message": "解析対象ファイルがありません。"}

        output_dir = resolve_output_dir(self.workspace_dir)
        service = AnalysisService()

        try:
            result = service.analyze_files(file_paths, output_dir=output_dir)
        except Exception as error:
            logger.error("解析処理で例外が発生しました", exc_info=True)
            return {"success": False, "message": f"解析に失敗しました: {error}"}

        summary_lines = [
            "解析が完了しました。",
            f"出力先: {output_dir}",
            f"テーブル: {len(result.tables)} 件",
            f"リンクテーブル: {len(result.linked_tables)} 件",
            f"クエリ: {len(result.queries)} 件",
            f"VBAモジュール: {len(result.vba_modules)} 件",
            f"依存関係: {len(result.dependencies)} 件",
        ]
        if result.errors:
            summary_lines.append("")
            summary_lines.append("エラー:")
            summary_lines.extend(f"- {message}" for message in result.errors)
        if result.warnings:
            summary_lines.append("")
            summary_lines.append("警告:")
            summary_lines.extend(f"- {message}" for message in result.warnings)

        return {
            "success": len(result.errors) == 0,
            "message": "\n".join(summary_lines),
            "output_dir": str(output_dir),
        }
