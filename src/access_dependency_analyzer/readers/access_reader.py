"""Microsoft Access ファイル読み取り（DAO / pyodbc）。"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from access_dependency_analyzer.core.models import FieldInfo

logger = logging.getLogger("access_dependency_analyzer.reader")

SYSTEM_PREFIXES = ("MSys", "~", "USys", "f_")
DAO_TYPE_MAP = {
    1: "Boolean",
    2: "Byte",
    3: "Integer",
    4: "Long",
    5: "Currency",
    6: "Single",
    7: "Double",
    8: "DateTime",
    9: "Binary",
    10: "Text",
    11: "LongBinary",
    12: "Memo",
    15: "ReplicationID",
    16: "BigInt",
}


@dataclass
class RawTableDef:
    """DAOから取得した生テーブル定義。"""

    name: str
    connect: str
    source_table_name: str
    fields: list[FieldInfo]
    primary_key: str
    record_count: int | None


@dataclass
class RawQueryDef:
    """DAOから取得した生クエリ定義。"""

    name: str
    sql: str


@dataclass
class RawFormDef:
    """フォーム定義。"""

    name: str
    record_source: str


@dataclass
class RawReportDef:
    """レポート定義。"""

    name: str
    record_source: str


class AccessReader:
    """Accessファイルを読み取る。"""

    def __init__(self, file_path: str | Path) -> None:
        self.file_path = Path(file_path).resolve()
        if not self.file_path.exists():
            raise FileNotFoundError(f"Accessファイルが見つかりません: {self.file_path}")
        if self.file_path.suffix.lower() not in {".accdb", ".mdb"}:
            raise ValueError(f"未対応の拡張子です: {self.file_path.suffix}")

        self._engine: Any | None = None
        self._database: Any | None = None
        self._backend = "none"
        self.warnings: list[str] = []

    def __enter__(self) -> AccessReader:
        self.open()
        return self

    def __exit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
        self.close()

    def open(self) -> None:
        """データベース接続を開く。"""
        if self._database is not None:
            return

        if self._try_open_dao():
            self._backend = "dao"
            logger.info("DAOで接続しました: %s", self.file_path)
            return

        if self._try_open_pyodbc():
            self._backend = "pyodbc"
            logger.info("pyodbcで接続しました: %s", self.file_path)
            return

        raise RuntimeError(
            "Accessファイルを開けませんでした。"
            " Microsoft Access Database Engine (ACE) のインストールを確認してください。"
        )

    def close(self) -> None:
        """データベース接続を閉じる。"""
        if self._database is not None:
            try:
                self._database.Close()
            except Exception:
                logger.warning("データベースクローズ時に警告が発生しました", exc_info=True)
            self._database = None
        self._engine = None

    @property
    def backend(self) -> str:
        """使用中のバックエンド名。"""
        return self._backend

    def _try_open_dao(self) -> bool:
        """DAO (win32com) で接続を試みる。"""
        try:
            import win32com.client  # type: ignore[import-untyped]
        except ImportError:
            logger.warning("pywin32 が利用できないため DAO 接続をスキップします")
            return False

        prog_ids = ("DAO.DBEngine.120", "DAO.DBEngine.36")
        for prog_id in prog_ids:
            try:
                engine = win32com.client.Dispatch(prog_id)
                database = engine.OpenDatabase(str(self.file_path))
                self._engine = engine
                self._database = database
                return True
            except Exception as error:
                logger.debug("DAO接続失敗 (%s): %s", prog_id, error)
        return False

    def _try_open_pyodbc(self) -> bool:
        """pyodbc で接続を試みる。"""
        try:
            import pyodbc  # type: ignore[import-untyped]
        except ImportError:
            logger.warning("pyodbc が利用できないため ODBC 接続をスキップします")
            return False

        drivers = [
            "Microsoft Access Driver (*.mdb, *.accdb)",
            "Microsoft Access Driver (*.mdb)",
        ]
        available = set(pyodbc.drivers())
        for driver in drivers:
            if driver not in available:
                continue
            try:
                connection_string = f"DRIVER={{{driver}}};DBQ={self.file_path};"
                connection = pyodbc.connect(connection_string)
                self._database = connection
                return True
            except Exception as error:
                logger.debug("pyodbc接続失敗 (%s): %s", driver, error)
        return False

    def read_tables(self) -> list[RawTableDef]:
        """テーブル定義を読み取る。"""
        self.open()
        if self._backend == "dao":
            return self._read_tables_dao()
        return self._read_tables_pyodbc()

    def read_queries(self) -> list[RawQueryDef]:
        """クエリ定義を読み取る。"""
        self.open()
        if self._backend == "dao":
            return self._read_queries_dao()
        return self._read_queries_pyodbc()

    def read_forms(self) -> list[RawFormDef]:
        """フォーム定義を読み取る。"""
        self.open()
        if self._backend != "dao":
            return []
        return self._read_forms_dao()

    def read_reports(self) -> list[RawReportDef]:
        """レポート定義を読み取る。"""
        self.open()
        if self._backend != "dao":
            return []
        return self._read_reports_dao()

    def _is_system_object(self, name: str) -> bool:
        return any(name.startswith(prefix) for prefix in SYSTEM_PREFIXES)

    def _read_tables_dao(self) -> list[RawTableDef]:
        assert self._database is not None
        tables: list[RawTableDef] = []

        for table_def in self._database.TableDefs:
            name = str(table_def.Name)
            if self._is_system_object(name):
                continue

            try:
                fields = self._read_fields_dao(table_def)
                primary_key = self._read_primary_key_dao(table_def)
            except Exception as error:
                message = (
                    f"{self.file_path.name}: テーブル定義の取得をスキップしました"
                    f" ({name}): {error}"
                )
                logger.warning(message)
                self.warnings.append(message)
                continue

            record_count = self._read_record_count_dao(name)
            tables.append(
                RawTableDef(
                    name=name,
                    connect=str(table_def.Connect or ""),
                    source_table_name=str(table_def.SourceTableName or ""),
                    fields=fields,
                    primary_key=primary_key,
                    record_count=record_count,
                )
            )
        return tables

    def _read_fields_dao(self, table_def: Any) -> list[FieldInfo]:
        fields: list[FieldInfo] = []
        for field in table_def.Fields:
            field_name = str(field.Name)
            if field_name.startswith("Gen"):
                continue
            data_type = DAO_TYPE_MAP.get(int(field.Type), f"Type{field.Type}")
            fields.append(
                FieldInfo(
                    name=field_name,
                    data_type=data_type,
                    size=int(field.Size) if hasattr(field, "Size") else None,
                    required=bool(field.Required),
                )
            )
        return fields

    def _read_primary_key_dao(self, table_def: Any) -> str:
        keys: list[str] = []
        for index in table_def.Indexes:
            if bool(index.Primary):
                for field in index.Fields:
                    keys.append(str(field.Name))
        return ",".join(keys)

    def _read_record_count_dao(self, table_name: str) -> int | None:
        assert self._database is not None
        try:
            recordset = self._database.OpenRecordset(
                f"SELECT COUNT(*) AS cnt FROM [{table_name}]"
            )
            count = int(recordset.Fields("cnt").Value)
            recordset.Close()
            return count
        except Exception as error:
            logger.warning("レコード数取得失敗 (%s): %s", table_name, error)
            return None

    def _read_queries_dao(self) -> list[RawQueryDef]:
        assert self._database is not None
        queries: list[RawQueryDef] = []
        for query_def in self._database.QueryDefs:
            name = str(query_def.Name)
            if self._is_system_object(name):
                continue
            try:
                sql = str(query_def.SQL or "")
            except Exception as error:
                logger.warning("クエリSQL取得失敗 (%s): %s", name, error)
                sql = ""
            queries.append(RawQueryDef(name=name, sql=sql))
        return queries

    def _read_forms_dao(self) -> list[RawFormDef]:
        assert self._database is not None
        forms: list[RawFormDef] = []
        for index in range(self._database.Containers("Forms").Documents.Count):
            document = self._database.Containers("Forms").Documents(index)
            name = str(document.Name)
            if self._is_system_object(name):
                continue
            record_source = self._read_document_property(document, "RecordSource")
            forms.append(RawFormDef(name=name, record_source=record_source))
        return forms

    def _read_reports_dao(self) -> list[RawReportDef]:
        assert self._database is not None
        reports: list[RawReportDef] = []
        for index in range(self._database.Containers("Reports").Documents.Count):
            document = self._database.Containers("Reports").Documents(index)
            name = str(document.Name)
            if self._is_system_object(name):
                continue
            record_source = self._read_document_property(document, "RecordSource")
            reports.append(RawReportDef(name=name, record_source=record_source))
        return reports

    def _read_document_property(self, document: Any, property_name: str) -> str:
        try:
            for prop in document.Properties:
                if str(prop.Name) == property_name:
                    return str(prop.Value or "")
        except Exception:
            logger.debug("プロパティ取得失敗: %s", property_name, exc_info=True)
        return ""

    def _read_tables_pyodbc(self) -> list[RawTableDef]:
        assert self._database is not None
        cursor = self._database.cursor()
        tables: list[RawTableDef] = []

        for row in cursor.tables(tableType="TABLE"):
            name = str(row.table_name)
            if self._is_system_object(name):
                continue
            fields = self._read_fields_pyodbc(cursor, name)
            record_count = self._read_record_count_pyodbc(cursor, name)
            tables.append(
                RawTableDef(
                    name=name,
                    connect="",
                    source_table_name="",
                    fields=fields,
                    primary_key="",
                    record_count=record_count,
                )
            )

        try:
            for row in cursor.tables(tableType="LINK"):
                name = str(row.table_name)
                if self._is_system_object(name):
                    continue
                if any(item.name == name for item in tables):
                    continue
                fields = self._read_fields_pyodbc(cursor, name)
                record_count = self._read_record_count_pyodbc(cursor, name)
                tables.append(
                    RawTableDef(
                        name=name,
                        connect="",
                        source_table_name="",
                        fields=fields,
                        primary_key="",
                        record_count=record_count,
                    )
                )
        except Exception as error:
            logger.warning("リンクテーブル一覧取得に失敗: %s", error)

        return tables

    def _read_fields_pyodbc(self, cursor: Any, table_name: str) -> list[FieldInfo]:
        fields: list[FieldInfo] = []
        try:
            for column in cursor.columns(table=table_name):
                fields.append(
                    FieldInfo(
                        name=str(column.column_name),
                        data_type=str(column.type_name),
                        size=int(column.column_size) if column.column_size else None,
                        required=column.nullable == 0,
                    )
                )
        except Exception as error:
            logger.warning("フィールド取得失敗 (%s): %s", table_name, error)
        return fields

    def _read_record_count_pyodbc(self, cursor: Any, table_name: str) -> int | None:
        try:
            cursor.execute(f"SELECT COUNT(*) FROM [{table_name}]")
            row = cursor.fetchone()
            return int(row[0]) if row else None
        except Exception as error:
            logger.warning("レコード数取得失敗 (%s): %s", table_name, error)
            return None

    def _read_queries_pyodbc(self) -> list[RawQueryDef]:
        assert self._database is not None
        cursor = self._database.cursor()
        queries: list[RawQueryDef] = []
        try:
            for row in cursor.tables(tableType="VIEW"):
                name = str(row.table_name)
                if self._is_system_object(name):
                    continue
                sql = self._read_view_sql_pyodbc(cursor, name)
                queries.append(RawQueryDef(name=name, sql=sql))
        except Exception as error:
            logger.warning("クエリ一覧取得に失敗: %s", error)
        return queries

    def _read_view_sql_pyodbc(self, cursor: Any, view_name: str) -> str:
        try:
            cursor.execute(
                "SELECT SQL FROM MSysQueries WHERE Name = ?",
                (view_name,),
            )
            row = cursor.fetchone()
            if row and row[0]:
                return str(row[0])
        except Exception:
            logger.debug("MSysQueriesからSQL取得失敗: %s", view_name, exc_info=True)
        return ""

    def read_vba_module_names(self) -> list[str]:
        """VBA モジュール名一覧を取得する（Containers → MSysObjects の順）。"""
        self.open()
        if self._backend != "dao":
            return []

        names = self._read_module_names_from_containers()
        if names:
            return names

        return self._read_module_names_from_msysobjects()

    def _read_module_names_from_containers(self) -> list[str]:
        """DAO Containers からモジュール名を取得する。"""
        assert self._database is not None
        names: list[str] = []
        seen: set[str] = set()

        for container_name in ("Modules", "Scripts"):
            try:
                container = self._database.Containers(container_name)
                for index in range(container.Documents.Count):
                    document = container.Documents(index)
                    name = str(document.Name).strip()
                    if not name or name.startswith("~") or name in seen:
                        continue
                    seen.add(name)
                    names.append(name)
            except Exception as error:
                logger.debug(
                    "Containers(%s) からの取得に失敗 (%s): %s",
                    container_name,
                    self.file_path.name,
                    error,
                )

        if names:
            logger.info(
                "Containers からモジュール名を取得: %s (%d 件)",
                self.file_path.name,
                len(names),
            )
        return sorted(names)

    def _read_module_names_from_msysobjects(self) -> list[str]:
        """MSysObjects から VBA モジュール名一覧を取得する。"""
        assert self._database is not None
        names: list[str] = []
        try:
            recordset = self._database.OpenRecordset(
                "SELECT Name FROM MSysObjects "
                "WHERE Type = -32761 AND Left([Name], 1) <> '~' "
                "ORDER BY Name"
            )
            while not recordset.EOF:
                name = str(recordset.Fields("Name").Value or "").strip()
                if name:
                    names.append(name)
                recordset.MoveNext()
            recordset.Close()
            if names:
                logger.info(
                    "MSysObjects から VBA モジュール名を取得: %s (%d 件)",
                    self.file_path.name,
                    len(names),
                )
        except Exception as error:
            logger.warning(
                "MSysObjects から VBA モジュール名を取得できませんでした (%s): %s",
                self.file_path.name,
                error,
            )
        return names
