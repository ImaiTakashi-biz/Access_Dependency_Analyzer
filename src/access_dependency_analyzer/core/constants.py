"""アプリケーション定数。"""

from __future__ import annotations

from pathlib import Path

APP_NAME = "Access Dependency Analyzer"
DEFAULT_OUTPUT_DIR = "output/analysis"
SUPPORTED_EXTENSIONS = frozenset({".accdb", ".mdb"})


def get_project_root() -> Path:
    """プロジェクトルートディレクトリを返す。"""
    return Path(__file__).resolve().parents[3]


def get_assets_dir() -> Path:
    """静的リソースディレクトリを返す。

    pip インストール時はパッケージ同梱の assets/ を優先し、
    開発時はプロジェクトルートの assets/ にフォールバックする。
    """
    package_root = Path(__file__).resolve().parent.parent
    package_assets = package_root / "assets"
    if (package_assets / "ui" / "index.html").exists():
        return package_assets
    return get_project_root() / "assets"


def resolve_output_dir(workspace_dir: Path | None = None) -> Path:
    """既定の解析結果出力先を返す。"""
    base = workspace_dir or Path.cwd()
    return (base / DEFAULT_OUTPUT_DIR).resolve()
