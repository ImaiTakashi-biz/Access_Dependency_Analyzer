"""VBA解析。"""

from __future__ import annotations

from access_dependency_analyzer.core.models import VbaModuleInfo
from access_dependency_analyzer.readers.vba_reader import RawVbaModule
from access_dependency_analyzer.utils.sql_parser import (
    extract_api_usages,
    extract_sql_strings_from_vba,
)


def analyze_vba_modules(
    access_file: str,
    raw_modules: list[RawVbaModule],
) -> list[VbaModuleInfo]:
    """VBAモジュール情報を構築する。"""
    results: list[VbaModuleInfo] = []
    for raw in raw_modules:
        results.append(
            VbaModuleInfo(
                access_file=access_file,
                module_name=raw.name,
                code=raw.code,
                sql_strings=extract_sql_strings_from_vba(raw.code),
                docmd_usages=extract_api_usages(raw.code, "DoCmd"),
                dao_usages=extract_api_usages(raw.code, "DAO"),
                adodb_usages=extract_api_usages(raw.code, "ADODB"),
            )
        )
    return results
