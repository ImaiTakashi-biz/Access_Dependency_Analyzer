"""VBA 読み取りオーケストレーションのテスト。"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from access_dependency_analyzer.readers.vba_reader import read_vba_modules
from access_dependency_analyzer.readers.vba_types import RawVbaModule


def test_read_vba_modules_uses_first_successful_backend() -> None:
    file_path = Path(r"C:\data\sample.accdb")

    with (
        patch(
            "access_dependency_analyzer.readers.vba_reader.read_vba_modules_via_pyopenvba",
            return_value=[],
        ) as pyopenvba_mock,
        patch(
            "access_dependency_analyzer.readers.vba_reader.read_vba_modules_via_dao",
            return_value=[RawVbaModule(name="Module1", code="Sub Test()\nEnd Sub")],
        ) as dao_mock,
        patch(
            "access_dependency_analyzer.readers.vba_reader.read_vba_modules_via_oletools",
            return_value=[RawVbaModule(name="Module2", code="ignored")],
        ) as oletools_mock,
    ):
        modules = read_vba_modules(file_path)

    assert len(modules) == 1
    assert modules[0].name == "Module1"
    pyopenvba_mock.assert_called_once_with(file_path)
    dao_mock.assert_called_once_with(file_path)
    oletools_mock.assert_not_called()


def test_read_vba_modules_prefers_pyopenvba_result() -> None:
    file_path = Path(r"C:\data\sample.accdb")
    expected = [RawVbaModule(name="Form1", code="Option Compare Database")]

    with (
        patch(
            "access_dependency_analyzer.readers.vba_reader.read_vba_modules_via_pyopenvba",
            return_value=expected,
        ),
        patch(
            "access_dependency_analyzer.readers.vba_reader.read_vba_modules_via_dao",
        ) as dao_mock,
        patch(
            "access_dependency_analyzer.readers.vba_reader.read_vba_modules_via_oletools",
        ) as oletools_mock,
    ):
        modules = read_vba_modules(file_path)

    assert modules == expected
    dao_mock.assert_not_called()
    oletools_mock.assert_not_called()
