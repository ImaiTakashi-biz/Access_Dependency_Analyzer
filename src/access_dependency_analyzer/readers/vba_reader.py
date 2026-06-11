"""VBAモジュール読み取り（oletools）。"""

from __future__ import annotations

import logging
import zipfile
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger("access_dependency_analyzer.reader.vba")


@dataclass
class RawVbaModule:
    """VBAモジュールの生データ。"""

    name: str
    code: str


def read_vba_modules(file_path: str | Path) -> list[RawVbaModule]:
    """AccessファイルからVBAモジュールを抽出する。"""
    path = Path(file_path).resolve()
    modules: list[RawVbaModule] = []

    try:
        from oletools.olevba import VBA_Parser  # type: ignore[import-untyped]
    except ImportError:
        logger.error("oletools がインストールされていません")
        return modules

    try:
        parser = VBA_Parser(str(path))
        if not parser.detect_vba_macros():
            logger.info("VBAマクロは検出されませんでした: %s", path.name)
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
    except zipfile.BadZipFile:
        logger.warning("ZIP形式ではないため oletools 解析をスキップ: %s", path.name)
    except Exception as error:
        logger.error("VBA抽出に失敗しました (%s): %s", path.name, error)

    return modules
