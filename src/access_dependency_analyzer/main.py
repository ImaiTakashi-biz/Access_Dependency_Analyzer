"""アプリケーションエントリポイント。"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import webview

from access_dependency_analyzer.analyzers.analysis_service import AnalysisService
from access_dependency_analyzer.app.api import AnalyzerApi
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
    webview.start(gui="edgechromium")


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
    args = parser.parse_args()
    workspace_dir = _default_workspace()

    if args.files:
        exit_code = run_cli(args.files, workspace_dir / args.output)
        sys.exit(exit_code)

    run_gui(workspace_dir)


if __name__ == "__main__":
    main()
