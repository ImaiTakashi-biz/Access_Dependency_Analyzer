"""pyOpenVBA による VBA 抽出。"""

from __future__ import annotations

import logging
from pathlib import Path

from access_dependency_analyzer.readers.vba_types import RawVbaModule

logger = logging.getLogger("access_dependency_analyzer.readers.vba_pyopenvba")


def read_vba_modules_via_pyopenvba(file_path: str | Path) -> list[RawVbaModule]:
    """pyOpenVBA で Access ファイルから VBA を抽出する。"""
    try:
        from pyopenvba import AccessReader  # type: ignore[import-untyped]
    except ImportError:
        logger.debug("pyOpenVBA が未インストールのためスキップします")
        return []

    path = Path(file_path)
    modules: list[RawVbaModule] = []

    try:
        with AccessReader(str(path)) as database:
            vba_modules = database.vba_modules()
            for module_name, source_code in vba_modules.items():
                if not source_code:
                    continue
                modules.append(
                    RawVbaModule(
                        name=str(module_name),
                        code=str(source_code),
                    )
                )

        if modules:
            logger.info(
                "pyOpenVBA で VBA を抽出しました: %s (%d 件)",
                path.name,
                len(modules),
            )
    except Exception as error:
        logger.warning(
            "pyOpenVBA VBA 抽出に失敗しました (%s): %s",
            path.name,
            error,
        )
        return []

    return modules
