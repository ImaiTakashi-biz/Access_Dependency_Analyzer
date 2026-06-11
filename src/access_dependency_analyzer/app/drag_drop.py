"""pywebview 向けドラッグ＆ドロップ処理。"""

from __future__ import annotations

import json
import logging
from typing import Any

from webview.dom import DOMEventHandler

from access_dependency_analyzer.core.constants import SUPPORTED_EXTENSIONS

logger = logging.getLogger("access_dependency_analyzer.app.drag_drop")


def _extract_dropped_paths(event: dict[str, Any]) -> list[str]:
    """ドロップイベントからファイルパスを抽出する。"""
    files = event.get("dataTransfer", {}).get("files", [])
    paths: list[str] = []

    for file_info in files:
        path = (
            file_info.get("pywebviewFullPath")
            or file_info.get("path")
            or file_info.get("name")
            or ""
        )
        if not path:
            continue
        suffix = path[path.rfind(".") :].lower() if "." in path else ""
        if suffix in SUPPORTED_EXTENSIONS:
            paths.append(path)

    return paths


def _notify_frontend(window: Any, paths: list[str]) -> None:
    """フロントエンドへドロップされたファイルを通知する。"""
    paths_json = json.dumps(paths, ensure_ascii=False)
    window.evaluate_js(f"addFilesFromNative({paths_json})")


def bind_file_drop(window: Any) -> None:
    """ウィンドウへファイルドロップイベントをバインドする。"""

    def on_drag(_event: dict[str, Any]) -> None:
        """ドラッグ中の既定動作を許可する。"""
        return None

    def on_drop(event: dict[str, Any]) -> None:
        """ドロップされたファイルをフロントエンドへ渡す。"""
        paths = _extract_dropped_paths(event)
        logger.info("ファイルがドロップされました: %s 件", len(paths))

        if not paths:
            window.evaluate_js(
                "setStatus("
                "'対応していないファイルです。.accdb / .mdb をドロップしてください。', "
                "'error'"
                ")"
            )
            return

        _notify_frontend(window, paths)

    window.dom.document.events.dragenter += DOMEventHandler(on_drag, True, True)
    window.dom.document.events.dragover += DOMEventHandler(on_drag, True, True)
    window.dom.document.events.drop += DOMEventHandler(on_drop, True, True)
    logger.info("ドラッグ＆ドロップを有効化しました")
