"""VBAモジュール読み取り（複数バックエンド）。"""

from __future__ import annotations

import logging
from pathlib import Path

from access_dependency_analyzer.readers.file_resolver import normalize_access_path
from access_dependency_analyzer.readers.vba_dao_reader import read_vba_modules_via_dao
from access_dependency_analyzer.readers.vba_oletools_reader import (
    read_vba_modules_via_oletools,
)
from access_dependency_analyzer.readers.vba_pyopenvba_reader import (
    read_vba_modules_via_pyopenvba,
)
from access_dependency_analyzer.readers.vba_types import RawVbaModule

logger = logging.getLogger("access_dependency_analyzer.readers.vba")


def read_vba_modules(
    file_path: str | Path,
    known_module_names: list[str] | None = None,
) -> list[RawVbaModule]:
    """Accessファイルから VBA モジュールを抽出する。

    優先順位:
    1. pyOpenVBA - .accdb / .mdb 向け純 Python 解析（ネットワークファイルはローカルコピー）
    2. DAO / Access COM - Access 導入環境向け（信頼設定が必要な場合あり）
    3. oletools - .mdb 向けフォールバック
    """
    path = normalize_access_path(file_path)
    suffix = path.suffix.lower()
    failures: list[str] = []

    modules = read_vba_modules_via_pyopenvba(path)
    if modules:
        logger.info(
            "VBA抽出完了 (%s): backend=pyopenvba, modules=%d",
            path.name,
            len(modules),
        )
        return modules
    failures.append("pyopenvba: モジュールなし")

    modules = read_vba_modules_via_dao(path, known_module_names=known_module_names)
    if modules:
        logger.info(
            "VBA抽出完了 (%s): backend=dao, modules=%d",
            path.name,
            len(modules),
        )
        return modules
    failures.append("dao: モジュールなし")

    if suffix == ".mdb":
        modules = read_vba_modules_via_oletools(path)
        if modules:
            logger.info(
                "VBA抽出完了 (%s): backend=oletools, modules=%d",
                path.name,
                len(modules),
            )
            return modules
        failures.append("oletools: モジュールなし")

    if known_module_names and not modules:
        logger.warning(
            "VBA抽出に失敗しました (%s): MSysObjects 上は %d 件あるがソース未取得 (%s)",
            path.name,
            len(known_module_names),
            " / ".join(failures),
        )
    elif failures:
        logger.info(
            "VBAマクロは検出されませんでした (%s): %s",
            path.name,
            " / ".join(failures),
        )

    return []
