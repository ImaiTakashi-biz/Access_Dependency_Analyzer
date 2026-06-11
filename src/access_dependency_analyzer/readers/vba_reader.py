"""VBAモジュール読み取り（複数バックエンド）。"""

from __future__ import annotations

import logging
from collections.abc import Callable
from pathlib import Path

from access_dependency_analyzer.readers.vba_dao_reader import read_vba_modules_via_dao
from access_dependency_analyzer.readers.vba_oletools_reader import (
    read_vba_modules_via_oletools,
)
from access_dependency_analyzer.readers.vba_pyopenvba_reader import (
    read_vba_modules_via_pyopenvba,
)
from access_dependency_analyzer.readers.vba_types import RawVbaModule

logger = logging.getLogger("access_dependency_analyzer.readers.vba")


def _vba_backends() -> tuple[tuple[str, Callable[[str | Path], list[RawVbaModule]]], ...]:
    """利用可能な VBA 抽出バックエンド一覧。"""
    return (
        ("pyopenvba", read_vba_modules_via_pyopenvba),
        ("dao", read_vba_modules_via_dao),
        ("oletools", read_vba_modules_via_oletools),
    )


def read_vba_modules(file_path: str | Path) -> list[RawVbaModule]:
    """Accessファイルから VBA モジュールを抽出する。

    優先順位:
    1. pyOpenVBA - .accdb / .mdb 向け純 Python 解析（Access 不要）
    2. DAO / Access COM - Access 導入環境向け
    3. oletools - レガシー形式向けフォールバック
    """
    path = Path(file_path)
    failures: list[str] = []

    for backend_name, reader in _vba_backends():
        try:
            modules = reader(path)
        except Exception as error:
            message = f"{backend_name}: {error}"
            failures.append(message)
            logger.debug("VBA backend 失敗 (%s)", message, exc_info=True)
            continue

        if modules:
            logger.info(
                "VBA抽出完了 (%s): backend=%s, modules=%d",
                path.name,
                backend_name,
                len(modules),
            )
            return modules

        failures.append(f"{backend_name}: モジュールなし")

    if failures:
        logger.warning(
            "VBA抽出に失敗しました (%s): %s",
            path.name,
            " / ".join(failures),
        )
    else:
        logger.info("VBAマクロは検出されませんでした: %s", path.name)

    return []
