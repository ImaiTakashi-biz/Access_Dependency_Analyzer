"""ドラッグ＆ドロップ処理のテスト。"""

from access_dependency_analyzer.app.drag_drop import _extract_dropped_paths


def test_extract_dropped_paths_from_pywebview_full_path() -> None:
    event = {
        "dataTransfer": {
            "files": [
                {"pywebviewFullPath": r"C:\data\製品マスタ.accdb"},
                {"pywebviewFullPath": r"C:\data\readme.txt"},
            ]
        }
    }
    paths = _extract_dropped_paths(event)
    assert paths == [r"C:\data\製品マスタ.accdb"]


def test_extract_dropped_paths_returns_empty_when_no_files() -> None:
    assert _extract_dropped_paths({}) == []
