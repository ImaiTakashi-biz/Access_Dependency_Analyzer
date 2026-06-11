"""定数・パス解決のテスト。"""

from __future__ import annotations

from pathlib import Path

from access_dependency_analyzer.core.constants import get_assets_dir, get_project_root


def test_get_assets_dir_prefers_dev_project_assets() -> None:
    assets = get_assets_dir()
    assert (assets / "ui" / "index.html").exists()


def test_get_project_root_points_to_repo_root() -> None:
    root = get_project_root()
    assert (root / "pyproject.toml").exists()
    assert (root / "assets" / "ui" / "index.html").exists()
