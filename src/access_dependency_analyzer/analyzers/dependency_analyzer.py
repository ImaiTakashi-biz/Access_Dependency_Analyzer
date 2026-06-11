"""Accessファイル間の依存関係解析。"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

from access_dependency_analyzer.core.models import AccessFileDependency, LinkedTableInfo


@dataclass
class DependencyGraph:
    """依存関係グラフと分類結果。"""

    dependencies: list[AccessFileDependency]
    upstream_files: list[str]
    midstream_files: list[str]
    downstream_files: list[str]
    chains: list[list[str]]


def _normalize_key(path_text: str) -> str:
    if not path_text:
        return ""
    return str(Path(path_text).resolve()).lower()


def _display_name(path_text: str) -> str:
    if not path_text:
        return "（不明）"
    return Path(path_text).stem


def build_dependencies(
    source_files: list[str],
    linked_tables: list[LinkedTableInfo],
) -> list[AccessFileDependency]:
    """リンクテーブルからファイル間依存を構築する。"""
    dependencies: list[AccessFileDependency] = []
    known_files = {_normalize_key(path): path for path in source_files}

    for linked in linked_tables:
        source_key = _normalize_key(linked.source_access)
        target_key = _normalize_key(linked.target_access)
        if not target_key:
            continue
        if target_key not in known_files:
            known_files[target_key] = linked.target_access

        # データフローはリンク先（提供元）からリンク元（利用側）へ向かう
        dependencies.append(
            AccessFileDependency(
                source_file=known_files.get(target_key, linked.target_access),
                target_file=known_files.get(source_key, linked.source_access),
                link_table=linked.table_name,
                target_table=linked.target_table,
            )
        )
    return dependencies


def analyze_dependency_graph(
    source_files: list[str],
    dependencies: list[AccessFileDependency],
) -> DependencyGraph:
    """依存関係グラフを分類する。"""
    file_map = {_normalize_key(path): path for path in source_files}
    outgoing: dict[str, set[str]] = defaultdict(set)
    incoming: dict[str, set[str]] = defaultdict(set)

    for dep in dependencies:
        source_key = _normalize_key(dep.source_file)
        target_key = _normalize_key(dep.target_file)
        if not source_key or not target_key:
            continue
        file_map.setdefault(source_key, dep.source_file)
        file_map.setdefault(target_key, dep.target_file)
        outgoing[source_key].add(target_key)
        incoming[target_key].add(source_key)

    all_keys = set(file_map.keys())
    upstream = sorted(
        file_map[key]
        for key in all_keys
        if not incoming.get(key) and outgoing.get(key)
    )
    downstream = sorted(
        file_map[key]
        for key in all_keys
        if incoming.get(key) and not outgoing.get(key)
    )
    midstream = sorted(
        file_map[key]
        for key in all_keys
        if incoming.get(key) and outgoing.get(key)
    )

    chains = _build_dependency_chains(file_map, outgoing, upstream, downstream)
    return DependencyGraph(
        dependencies=dependencies,
        upstream_files=upstream,
        midstream_files=midstream,
        downstream_files=downstream,
        chains=chains,
    )


def _build_dependency_chains(
    file_map: dict[str, str],
    outgoing: dict[str, set[str]],
    upstream: list[str],
    downstream: list[str],
) -> list[list[str]]:
    """上流から下流へのチェーンを構築する。"""
    start_keys = [_normalize_key(path) for path in upstream]
    if not start_keys:
        start_keys = list(file_map.keys())

    chains: list[list[str]] = []
    visited_paths: set[tuple[str, ...]] = set()

    def walk(current_key: str, path: list[str]) -> None:
        current_name = _display_name(file_map.get(current_key, current_key))
        next_path = path + [current_name]
        children = sorted(outgoing.get(current_key, set()))

        if not children:
            path_key = tuple(next_path)
            if path_key not in visited_paths:
                visited_paths.add(path_key)
                chains.append(next_path)
            return

        for child in children:
            if child in {_normalize_key(name) for name in path}:
                continue
            walk(child, next_path)

    for start_key in start_keys:
        walk(start_key, [])

    if not chains and downstream:
        chains.append([_display_name(path) for path in downstream])

    unique_chains: list[list[str]] = []
    seen: set[tuple[str, ...]] = set()
    for chain in sorted(chains, key=lambda item: (-len(item), item)):
        key = tuple(chain)
        if key not in seen:
            seen.add(key)
            unique_chains.append(chain)
    return unique_chains
