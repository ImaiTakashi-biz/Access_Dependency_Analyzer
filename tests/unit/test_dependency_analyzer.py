"""依存関係解析のテスト。"""

from access_dependency_analyzer.analyzers.dependency_analyzer import (
    analyze_dependency_graph,
    build_dependencies,
)
from access_dependency_analyzer.core.models import LinkedTableInfo


def test_build_dependencies_and_graph_classification() -> None:
    master = r"C:\data\製品マスタ.accdb"
    middle = r"C:\data\不具合情報.accdb"
    downstream = r"C:\data\不具合情報検索.accdb"

    linked_tables = [
        LinkedTableInfo(
            access_file=middle,
            table_name="T_製品リンク",
            source_access=middle,
            target_access=master,
            target_table="T_製品",
            connection_string=f"DATABASE={master};",
        ),
        LinkedTableInfo(
            access_file=downstream,
            table_name="T_不具合リンク",
            source_access=downstream,
            target_access=middle,
            target_table="T_不具合",
            connection_string=f"DATABASE={middle};",
        ),
    ]

    source_files = [master, middle, downstream]
    dependencies = build_dependencies(source_files, linked_tables)
    graph = analyze_dependency_graph(source_files, dependencies)

    assert len(dependencies) == 2
    assert any(path.endswith("製品マスタ.accdb") for path in graph.upstream_files)
    assert any(path.endswith("不具合情報検索.accdb") for path in graph.downstream_files)
    assert graph.chains
