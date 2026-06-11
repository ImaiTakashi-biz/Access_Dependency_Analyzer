"""Mermaid エクスポートのテスト。"""

from __future__ import annotations

from access_dependency_analyzer.core.models import AccessFileDependency
from access_dependency_analyzer.exporters.mermaid_exporter import build_mermaid_content


def test_build_mermaid_content_uses_unique_node_ids_for_same_stem() -> None:
    dependencies = [
        AccessFileDependency(
            source_file=r"C:\data\foo.accdb",
            target_file=r"D:\apps\foo.accdb",
            link_table="t_link",
            target_table="t_data",
        )
    ]

    content = build_mermaid_content(dependencies)

    node_lines = [line for line in content.splitlines() if "[" in line and "]" in line]
    node_ids = [line.strip().split("[", 1)[0] for line in node_lines]
    assert len(node_ids) == len(set(node_ids))
