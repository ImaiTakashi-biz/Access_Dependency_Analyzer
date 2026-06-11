"""AI解析用レポート生成。"""

from __future__ import annotations

from collections import Counter
from pathlib import Path

from access_dependency_analyzer.analyzers.dependency_analyzer import DependencyGraph
from access_dependency_analyzer.core.models import AnalysisResult


def _bullet_list(items: list[str]) -> str:
    if not items:
        return "- （該当なし）\n"
    return "".join(f"- {item}\n" for item in items)


def export_ai_report(
    result: AnalysisResult,
    graph: DependencyGraph,
    output_dir: Path,
) -> None:
    """report_for_ai.md を出力する。"""
    output_dir.mkdir(parents=True, exist_ok=True)

    local_tables = [table for table in result.tables if not table.is_linked]
    linked_tables = [table for table in result.tables if table.is_linked]
    update_queries = [query for query in result.queries if query.is_update]
    select_queries = [query for query in result.queries if query.is_select]

    master_candidates = sorted(
        {
            Path(path).stem
            for path in graph.upstream_files
        }
    )

    migration_notes = [
        "リンクテーブルは PostgreSQL では外部DB参照または統合テーブル化が必要です。",
        "更新系クエリはアプリケーション層またはストアド関数への移行対象です。",
        "VBA内SQLは実行経路の洗い出しと業務ロジック再実装が必要です。",
        "上流マスタを先に移行し、下流システムの参照整合を確認してください。",
    ]
    if result.errors:
        migration_notes.append(
            "一部ファイルの解析に失敗しています。出力が不完全な可能性があります。"
        )
    if result.warnings:
        migration_notes.append(
            "警告が発生しています。linked_tables.csv と relationship.md を再確認してください。"
        )

    lines = [
        "# Access Dependency Analyzer - AI解析用レポート",
        "",
        "## システム概要",
        "",
        f"- 解析対象Accessファイル数: {len(result.source_files)}",
        f"- 実テーブル数: {len(local_tables)}",
        f"- リンクテーブル数: {len(linked_tables)}",
        f"- クエリ数: {len(result.queries)}",
        f"- VBAモジュール数: {len(result.vba_modules)}",
        f"- ファイル間依存数: {len(result.dependencies)}",
        "",
        "## Access一覧",
        "",
        _bullet_list([Path(path).name for path in result.source_files]),
        "## テーブル一覧",
        "",
        _bullet_list(
            [
                f"{Path(table.access_file).name} / {table.table_name}"
                f"（{'リンク' if table.is_linked else '実テーブル'}）"
                for table in result.tables
            ]
        ),
        "## リンクテーブル一覧",
        "",
        _bullet_list(
            [
                f"{Path(linked.access_file).name}.{linked.table_name}"
                f" -> {Path(linked.target_access).name if linked.target_access else '不明'}"
                f".{linked.target_table or '不明'}"
                for linked in result.linked_tables
            ]
        ),
        "## クエリ依存関係",
        "",
        _bullet_list(
            [
                f"{Path(query.access_file).name}.{query.query_name}"
                f" -> {', '.join(query.referenced_tables) or '参照先不明'}"
                for query in result.queries
            ]
        ),
        "## VBA依存関係",
        "",
        _bullet_list(
            [
                f"{Path(module.access_file).name}.{module.module_name}"
                f"（SQL抽出: {len(module.sql_strings)}件 / DoCmd: {len(module.docmd_usages)}件）"
                for module in result.vba_modules
            ]
        ),
        "## データフロー推定",
        "",
    ]

    if graph.chains:
        for chain in graph.chains:
            lines.append(f"- {' -> '.join(chain)}")
    else:
        lines.append("- リンクテーブルに基づく明確なデータフローは検出されませんでした。")

    lines.extend(
        [
            "",
            "## PostgreSQL移行時の注意点",
            "",
            _bullet_list(migration_notes),
            "",
            "## 推奨移行順序（案）",
            "",
            _bullet_list(
                [
                    f"1. 共通マスタ候補: {', '.join(master_candidates) or '（要確認）'}",
                    f"2. 中間システム: {', '.join(Path(p).stem for p in graph.midstream_files) or '（該当なし）'}",
                    f"3. 下流システム: {', '.join(Path(p).stem for p in graph.downstream_files) or '（該当なし）'}",
                ]
            ),
            "",
            "## クエリ種別サマリ",
            "",
            f"- 参照系クエリ: {len(select_queries)}",
            f"- 更新系クエリ: {len(update_queries)}",
            "",
            "## エラー・警告",
            "",
            _bullet_list(result.errors + result.warnings),
            "",
            "## 補足（AIへの指示）",
            "",
            "このレポートを基に、以下を提案してください。",
            "1. PostgreSQLスキーマ設計（マスタ/トランザクション/参照整合）",
            "2. 移行順序と段階的リリース計画",
            "3. 共通マスタ統合方針",
            "4. 上流/下流システムの責務分離",
            "",
        ]
    )

    duplicate_tables = [
        name
        for name, count in Counter(table.table_name for table in local_tables).items()
        if count > 1
    ]
    if duplicate_tables:
        lines.extend(
            [
                "## 共通マスタ設計候補（同名実テーブル）",
                "",
                _bullet_list(duplicate_tables),
                "",
            ]
        )

    (output_dir / "report_for_ai.md").write_text("\n".join(lines), encoding="utf-8")
