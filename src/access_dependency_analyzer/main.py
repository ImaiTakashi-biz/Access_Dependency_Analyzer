"""アプリケーションエントリポイント。"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import webview

from access_dependency_analyzer.analyzers.analysis_service import AnalysisService
from access_dependency_analyzer.analyzers.merge_service import MergeService
from access_dependency_analyzer.app.api import AnalyzerApi
from access_dependency_analyzer.app.drag_drop import bind_file_drop
from access_dependency_analyzer.core.constants import (
    APP_NAME,
    DEFAULT_OUTPUT_DIR,
    get_assets_dir,
    resolve_output_dir,
)
from access_dependency_analyzer.core.logging_config import setup_logging


def _default_workspace() -> Path:
    return Path.cwd()


def run_gui(workspace_dir: Path) -> None:
    """pywebview GUI を起動する。"""
    html_path = get_assets_dir() / "ui" / "index.html"
    api = AnalyzerApi(workspace_dir)
    window = webview.create_window(
        APP_NAME,
        url=str(html_path),
        js_api=api,
        width=1080,
        height=760,
        min_size=(900, 640),
    )

    webview.start(bind_file_drop, window, gui="edgechromium")


def run_merge_retry(base_output: Path, retry_output: Path) -> int:
    """再解析結果をメイン出力へ統合する。"""
    service = MergeService()
    result = service.merge_retry_into_base(base_output, retry_output)
    print(f"統合先: {base_output.resolve()}")
    print(f"Accessファイル数: {len(result.source_files)}")
    print(f"テーブル: {len(result.tables)}")
    print(f"リンクテーブル: {len(result.linked_tables)}")
    print(f"クエリ: {len(result.queries)}")
    print(f"VBA: {len(result.vba_modules)}")
    print(f"依存関係: {len(result.dependencies)}")
    if result.warnings:
        print("警告:")
        for message in result.warnings:
            print(f"  - {message}")
    return 0


def run_cli(file_paths: list[str], output_dir: Path) -> int:
    """CLIモードで解析を実行する。"""
    service = AnalysisService()
    result = service.analyze_files(file_paths, output_dir=output_dir)
    print(f"出力先: {output_dir.resolve()}")
    print(f"テーブル: {len(result.tables)}")
    print(f"リンクテーブル: {len(result.linked_tables)}")
    print(f"クエリ: {len(result.queries)}")
    print(f"VBA: {len(result.vba_modules)}")
    print(f"依存関係: {len(result.dependencies)}")
    if result.errors:
        print("エラー:")
        for message in result.errors:
            print(f"  - {message}")
    return 1 if result.errors else 0


def main() -> None:
    """メイン処理。"""
    setup_logging()
    parser = argparse.ArgumentParser(description=APP_NAME)
    parser.add_argument(
        "--files",
        nargs="+",
        help="解析対象の .accdb / .mdb ファイル（CLIモード）",
    )
    parser.add_argument(
        "--output",
        default=DEFAULT_OUTPUT_DIR,
        help=f"出力先ディレクトリ（既定: {DEFAULT_OUTPUT_DIR}）",
    )
    parser.add_argument(
        "--merge-retry",
        action="store_true",
        help="再解析結果（output/retry_analysis）をメイン出力へ統合する",
    )
    parser.add_argument(
        "--retry-output",
        default="output/retry_analysis",
        help="再解析 CSV の入力ディレクトリ（--merge-retry 時）",
    )
    args = parser.parse_args()
    workspace_dir = _default_workspace()

    if args.merge_retry:
        exit_code = run_merge_retry(
            workspace_dir / args.output,
            workspace_dir / args.retry_output,
        )
        sys.exit(exit_code)

    if args.files:
        exit_code = run_cli(args.files, workspace_dir / args.output)
        sys.exit(exit_code)

    run_gui(workspace_dir)


if __name__ == "__main__":
    main()
