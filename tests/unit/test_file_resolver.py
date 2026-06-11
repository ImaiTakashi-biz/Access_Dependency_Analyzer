"""ファイルパス解決のテスト。"""

from pathlib import Path

from access_dependency_analyzer.readers.file_resolver import (
    is_unc_path,
    normalize_access_path,
)


def test_is_unc_path() -> None:
    assert is_unc_path(Path(r"\\server\share\file.accdb"))
    assert not is_unc_path(Path(r"C:\data\file.accdb"))


def test_normalize_access_path_keeps_unc() -> None:
    unc = Path(r"\\192.168.1.200\share\test.accdb")
    assert normalize_access_path(unc).as_posix().startswith("//")
