"""不完全解析結果のマーカー出力。"""

from __future__ import annotations

from pathlib import Path

from access_dependency_analyzer.core.models import AnalysisResult

INCOMPLETE_FILE_NAME = "_INCOMPLETE.txt"


def export_incomplete_marker(result: AnalysisResult, output_dir: Path) -> bool:
    """解析エラーがある場合に _INCOMPLETE.txt を出力する。"""
    if not result.errors:
        marker = output_dir / INCOMPLETE_FILE_NAME
        if marker.exists():
            marker.unlink()
        return False

    lines = [
        "【警告】この解析結果は不完全です。",
        "",
        "以下のファイルでエラーが発生しました。",
        "移行設計に使用する前に、エラーを解消して再解析してください。",
        "",
    ]
    lines.extend(f"- {message}" for message in result.errors)

    if result.warnings:
        lines.extend(["", "警告:", ""])
        lines.extend(f"- {message}" for message in result.warnings)

    (output_dir / INCOMPLETE_FILE_NAME).write_text("\n".join(lines) + "\n", encoding="utf-8")
    return True
