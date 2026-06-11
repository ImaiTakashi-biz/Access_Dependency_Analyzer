"""pyOpenVBA による VBA 抽出。"""

from __future__ import annotations

import logging
from pathlib import Path

from access_dependency_analyzer.readers.file_resolver import local_access_file
from access_dependency_analyzer.readers.vba_types import RawVbaModule

logger = logging.getLogger("access_dependency_analyzer.readers.vba_pyopenvba")

MSYS_MODULE_TYPE = -32761


def _extract_with_access_reader(database: object) -> list[RawVbaModule]:
    """AccessReader から VBA モジュールを抽出する。"""
    modules: list[RawVbaModule] = []
    seen_names: set[str] = set()

    module_names: list[str] = []
    if hasattr(database, "vba_module_names"):
        try:
            module_names = list(database.vba_module_names())
        except Exception as error:
            logger.debug("vba_module_names 取得失敗: %s", error)

    if not module_names and hasattr(database, "iter_msys_modules"):
        try:
            module_names = [str(obj.name) for obj in database.iter_msys_modules()]
        except Exception as error:
            logger.debug("iter_msys_modules 取得失敗: %s", error)

    for module_name in module_names:
        if not module_name or module_name in seen_names:
            continue
        seen_names.add(module_name)
        try:
            source_code = database.read_vba_module(module_name)  # type: ignore[attr-defined]
        except Exception as error:
            logger.debug("read_vba_module 失敗 (%s): %s", module_name, error)
            continue
        if source_code:
            modules.append(
                RawVbaModule(name=str(module_name), code=str(source_code))
            )

    if modules:
        return modules

    if hasattr(database, "iter_vba_modules"):
        for module in database.iter_vba_modules():
            if not module.name or module.name in seen_names:
                continue
            if not module.source:
                continue
            seen_names.add(module.name)
            modules.append(
                RawVbaModule(name=str(module.name), code=str(module.source))
            )

    if not modules and hasattr(database, "vba_modules"):
        try:
            for module_name, source_code in database.vba_modules().items():  # type: ignore[attr-defined]
                if module_name in seen_names or not source_code:
                    continue
                seen_names.add(module_name)
                modules.append(
                    RawVbaModule(name=str(module_name), code=str(source_code))
                )
        except Exception as error:
            logger.debug("vba_modules 取得失敗: %s", error)

    return modules


def read_vba_modules_via_pyopenvba(file_path: str | Path) -> list[RawVbaModule]:
    """pyOpenVBA で Access ファイルから VBA を抽出する。"""
    try:
        from pyopenvba import AccessReader  # type: ignore[import-untyped]
    except ImportError:
        logger.debug("pyOpenVBA が未インストールのためスキップします")
        return []

    path = Path(file_path)

    try:
        with local_access_file(path) as readable_path:
            with AccessReader(str(readable_path)) as database:
                modules = _extract_with_access_reader(database)

        if modules:
            logger.info(
                "pyOpenVBA で VBA を抽出しました: %s (%d 件)",
                path.name,
                len(modules),
            )
        else:
            logger.info("pyOpenVBA: VBA モジュールは検出されませんでした (%s)", path.name)
    except Exception as error:
        logger.warning(
            "pyOpenVBA VBA 抽出に失敗しました (%s): %s",
            path.name,
            error,
        )
        return []

    return modules
