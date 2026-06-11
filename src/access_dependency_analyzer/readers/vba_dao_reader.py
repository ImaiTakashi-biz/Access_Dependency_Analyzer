"""DAO / Access COM による VBA 抽出。"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from access_dependency_analyzer.readers.vba_types import RawVbaModule

logger = logging.getLogger("access_dependency_analyzer.readers.vba_dao")


def read_vba_modules_via_dao(file_path: str | Path) -> list[RawVbaModule]:
    """Access.Application 経由で VBA モジュールを抽出する。"""
    try:
        import win32com.client  # type: ignore[import-untyped]
    except ImportError:
        logger.debug("pywin32 が未インストールのため DAO VBA 抽出をスキップします")
        return []

    path = str(Path(file_path))
    application: Any | None = None
    modules: list[RawVbaModule] = []

    try:
        application = win32com.client.Dispatch("Access.Application")
        application.Visible = False
        application.OpenCurrentDatabase(path, False)

        vb_project = application.VBE.ActiveVBProject
        for index in range(1, vb_project.VBComponents.Count + 1):
            component = vb_project.VBComponents(index)
            module_name = str(component.Name)
            code_module = component.CodeModule
            line_count = int(code_module.CountOfLines)
            code = (
                str(code_module.Lines(1, line_count))
                if line_count > 0
                else ""
            )
            modules.append(RawVbaModule(name=module_name, code=code))

        logger.info(
            "DAO 経由で VBA を抽出しました: %s (%d 件)",
            Path(path).name,
            len(modules),
        )
    except Exception as error:
        logger.warning(
            "DAO VBA 抽出に失敗しました (%s): %s",
            Path(path).name,
            error,
        )
        return []
    finally:
        if application is not None:
            try:
                application.CloseCurrentDatabase()
            except Exception:
                logger.debug("データベースクローズ時に警告", exc_info=True)
            try:
                application.Quit()
            except Exception:
                logger.debug("Access 終了時に警告", exc_info=True)

    return modules
