"""AccessReader のテスト。"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from access_dependency_analyzer.core.models import FieldInfo
from access_dependency_analyzer.readers.access_reader import AccessReader


@pytest.fixture
def sample_db(tmp_path: Path) -> Path:
    path = tmp_path / "sample.accdb"
    path.write_text("", encoding="utf-8")
    return path


def test_is_system_object_excludes_msys_tables(sample_db: Path) -> None:
    reader = AccessReader(sample_db)
    assert reader._is_system_object("MSysObjects") is True
    assert reader._is_system_object("~TmpTable") is True
    assert reader._is_system_object("t_製品マスタ") is False


def test_read_tables_dao_skips_failed_table(sample_db: Path) -> None:
    reader = AccessReader(sample_db)
    reader._backend = "dao"
    reader._database = MagicMock()
    reader.warnings = []

    ok_def = MagicMock(Name="t_正常", Connect="", SourceTableName="")
    bad_def = MagicMock(Name="t_異常", Connect="", SourceTableName="")
    reader._database.TableDefs = [ok_def, bad_def]

    def read_fields(table_def: MagicMock) -> list[FieldInfo]:
        if str(table_def.Name) == "t_異常":
            raise RuntimeError("OLE error 0x800a0beb")
        return [FieldInfo(name="ID", data_type="Long")]

    reader._read_fields_dao = read_fields  # type: ignore[method-assign]
    reader._read_primary_key_dao = MagicMock(return_value="ID")  # type: ignore[method-assign]
    reader._read_record_count_dao = MagicMock(return_value=10)  # type: ignore[method-assign]

    tables = reader._read_tables_dao()

    assert len(tables) == 1
    assert tables[0].name == "t_正常"
    assert len(reader.warnings) == 1
    assert "t_異常" in reader.warnings[0]


def test_read_tables_dao_excludes_system_tables(sample_db: Path) -> None:
    reader = AccessReader(sample_db)
    reader._backend = "dao"
    reader._database = MagicMock()
    reader.warnings = []

    system_def = MagicMock(Name="MSysObjects", Connect="", SourceTableName="")
    user_def = MagicMock(Name="t_コントロール", Connect="", SourceTableName="")
    reader._database.TableDefs = [system_def, user_def]

    reader._read_fields_dao = MagicMock(return_value=[])  # type: ignore[method-assign]
    reader._read_primary_key_dao = MagicMock(return_value="")  # type: ignore[method-assign]
    reader._read_record_count_dao = MagicMock(return_value=None)  # type: ignore[method-assign]

    tables = reader._read_tables_dao()

    assert len(tables) == 1
    assert tables[0].name == "t_コントロール"
