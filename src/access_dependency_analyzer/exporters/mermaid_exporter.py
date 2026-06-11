"""Mermaid依存関係図エクスポート。"""

from __future__ import annotations

from pathlib import Path

from access_dependency_analyzer.analyzers.dependency_analyzer import DependencyGraph
from access_dependency_analyzer.core.models import AccessFileDependency


def _node_id(path_text: str) -> str:
    stem = Path(path_text).stem
    sanitized = "".join(char if char.isalnum() else "_" for char in stem)
    return sanitized or "unknown"


def build_mermaid_content(dependencies: list[AccessFileDependency]) -> str:
    """Mermaidグラフ定義を生成する。"""
    lines = ["graph TD"]
    seen_edges: set[tuple[str, str]] = set()

    for dependency in dependencies:
        source_id = _node_id(dependency.source_file)
        target_id = _node_id(dependency.target_file)
        source_label = Path(dependency.source_file).stem
        target_label = Path(dependency.target_file).stem

        lines.append(f'    {source_id}["{source_label}"]')
        lines.append(f'    {target_id}["{target_label}"]')

        edge = (source_id, target_id)
        if edge not in seen_edges:
            seen_edges.add(edge)
            lines.append(f"    {source_id} --> {target_id}")

    if len(lines) == 1:
        lines.append('    empty["依存関係なし"]')
    return "\n".join(lines) + "\n"


def export_mermaid(graph: DependencyGraph, output_dir: Path) -> None:
    """Mermaidファイルを出力する。"""
    output_dir.mkdir(parents=True, exist_ok=True)
    content = build_mermaid_content(graph.dependencies)
    (output_dir / "dependency_graph.mmd").write_text(content, encoding="utf-8")
