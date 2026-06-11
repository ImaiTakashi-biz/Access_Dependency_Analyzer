"""解析結果を保持するデータモデル。"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class FieldInfo:
    """テーブルフィールド情報。"""

    name: str
    data_type: str
    size: int | None = None
    required: bool = False


@dataclass
class TableInfo:
    """テーブル情報。"""

    access_file: str
    table_name: str
    is_linked: bool
    record_count: int | None
    primary_key: str
    fields: list[FieldInfo] = field(default_factory=list)


@dataclass
class LinkedTableInfo:
    """リンクテーブル情報。"""

    access_file: str
    table_name: str
    source_access: str
    target_access: str
    target_table: str
    connection_string: str


@dataclass
class QueryInfo:
    """クエリ情報。"""

    access_file: str
    query_name: str
    sql: str
    referenced_tables: list[str] = field(default_factory=list)
    is_update: bool = False
    is_select: bool = False


@dataclass
class FormInfo:
    """フォーム情報。"""

    access_file: str
    form_name: str
    record_source: str
    used_tables: list[str] = field(default_factory=list)
    used_queries: list[str] = field(default_factory=list)


@dataclass
class ReportInfo:
    """レポート情報。"""

    access_file: str
    report_name: str
    record_source: str
    used_tables: list[str] = field(default_factory=list)
    used_queries: list[str] = field(default_factory=list)


@dataclass
class VbaModuleInfo:
    """VBAモジュール情報。"""

    access_file: str
    module_name: str
    code: str
    sql_strings: list[str] = field(default_factory=list)
    docmd_usages: list[str] = field(default_factory=list)
    dao_usages: list[str] = field(default_factory=list)
    adodb_usages: list[str] = field(default_factory=list)


@dataclass
class AccessFileDependency:
    """Accessファイル間の依存関係。"""

    source_file: str
    target_file: str
    link_table: str
    target_table: str


@dataclass
class AnalysisResult:
    """解析結果の集約。"""

    source_files: list[str] = field(default_factory=list)
    tables: list[TableInfo] = field(default_factory=list)
    linked_tables: list[LinkedTableInfo] = field(default_factory=list)
    queries: list[QueryInfo] = field(default_factory=list)
    forms: list[FormInfo] = field(default_factory=list)
    reports: list[ReportInfo] = field(default_factory=list)
    vba_modules: list[VbaModuleInfo] = field(default_factory=list)
    dependencies: list[AccessFileDependency] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def output_dir(self) -> Path:
        """出力先ディレクトリ名。"""
        from access_dependency_analyzer.core.constants import DEFAULT_OUTPUT_DIR

        return Path(DEFAULT_OUTPUT_DIR)
