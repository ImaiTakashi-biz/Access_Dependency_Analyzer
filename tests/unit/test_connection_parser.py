"""接続文字列解析のテスト。"""

from access_dependency_analyzer.utils.connection_parser import (
    extract_database_path,
    extract_target_table,
)


def test_extract_database_path_from_database_key() -> None:
    connect = 'DATABASE=C:\\data\\製品マスタ.accdb;TABLE=製品;'
    path = extract_database_path(connect)
    assert path.endswith("製品マスタ.accdb")


def test_extract_database_path_from_dbq_key() -> None:
    connect = "Dbq=D:\\master\\customer.mdb;"
    path = extract_database_path(connect)
    assert path.endswith("customer.mdb")


def test_extract_target_table_from_source_table_name() -> None:
    connect = "DATABASE=C:\\data\\製品マスタ.accdb;"
    assert extract_target_table(connect, "T_製品") == "T_製品"


def test_extract_target_table_from_connect() -> None:
    connect = "DATABASE=C:\\data\\製品マスタ.accdb;TABLE=T_製品;"
    assert extract_target_table(connect, "") == "T_製品"


def test_extract_database_path_from_unc() -> None:
    connect = r"DATABASE=\\192.168.1.200\share\master.accdb;TABLE=T_製品;"
    path = extract_database_path(connect)
    assert path.startswith("\\\\")
    assert path.endswith("master.accdb")
