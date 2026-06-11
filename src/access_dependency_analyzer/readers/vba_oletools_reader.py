"""oletools による VBA 抽出（フォールバック）。"""

from __future__ import annotations

import logging
import zipfile
from pathlib import Path

from access_dependency_analyzer.readers.vba_types import RawVbaModule

logger = logging.getLogger("access_dependency_analyzer.readers.vba_oletools")


def read_vba_modules_via_oletools(file_path: str | Path) -> list[RawVbaModule]:
    """oletools で VBA モジュールを抽出する。"""
    try:
        from oletools.olevba import VBA_Parser  # type: ignore[import-untyped]
    except ImportError:
        logger.debug("oletools が未インストールのためスキップします")
        return []

    path = Path(file_path)
    modules: list[RawVbaModule] = []

    try:
        parser = VBA_Parser(str(path))
        if not parser.detect_vba_macros():
            parser.close()
            return modules

        for (_, _, macro_name, vba_code) in parser.extract_macros():
            if not vba_code:
                continue
            modules.append(
                RawVbaModule(
                    name=str(macro_name),
                    code=vba_code.decode("utf-8", errors="replace"),
                )
            )
        parser.close()

        if modules:
            logger.info(
                "oletools で VBA を抽出しました: %s (%d 件)",
                path.name,
                len(modules),
            )
    except zipfile.BadZipFile:
        logger.debug("oletools: ZIP 形式ではないためスキップ (%s)", path.name)
    except Exception as error:
        logger.warning(
            "oletools VBA 抽出に失敗しました (%s): %s",
            path.name,
            error,
        )
        return []

    return modules
