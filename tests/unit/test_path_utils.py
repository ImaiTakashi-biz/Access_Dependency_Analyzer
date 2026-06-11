"""パス正規化のテスト。"""

from __future__ import annotations

from pathlib import Path

from access_dependency_analyzer.utils.path_utils import (
    is_unc_path,
    normalize_access_path,
    normalize_access_path_str,
)


def test_is_unc_path() -> None:
    assert is_unc_path(r"\\server\share\file.accdb")
    assert not is_unc_path(r"C:\data\file.accdb")


def test_normalize_access_path_keeps_unc() -> None:
    unc = Path(r"\\192.168.1.200\share\test.accdb")
    assert normalize_access_path(unc).as_posix().startswith("//")


def test_normalize_access_path_str_keeps_unc() -> None:
    path = normalize_access_path_str(r'"\\192.168.1.200\share\master.accdb"')
    assert path.startswith("\\\\")
    assert path.endswith("master.accdb")
