"""Markdownレポートエクスポート。"""

from __future__ import annotations

from pathlib import Path

from access_dependency_analyzer.analyzers.dependency_analyzer import DependencyGraph


def _format_file_list(files: list[str]) -> str:
    if not files:
        return "* （該当なし）\n"
    return "".join(f"* {Path(path).name}\n" for path in files)


def export_relationship_markdown(graph: DependencyGraph, output_dir: Path) -> None:
    """relationship.md を出力する。"""
    output_dir.mkdir(parents=True, exist_ok=True)
    lines = ["# システム依存関係", ""]

    if graph.chains:
        for chain in graph.chains:
            lines.append(" → ".join(chain))
            lines.append("")
    else:
        lines.append("（リンクテーブルによるファイル間依存は検出されませんでした）")
        lines.append("")

    lines.extend(
        [
            "---",
            "",
            "# 上流システム",
            "",
            _format_file_list(graph.upstream_files),
            "# 中間システム",
            "",
            _format_file_list(graph.midstream_files),
            "# 下流システム",
            "",
            _format_file_list(graph.downstream_files),
        ]
    )
    (output_dir / "relationship.md").write_text("\n".join(lines), encoding="utf-8")
