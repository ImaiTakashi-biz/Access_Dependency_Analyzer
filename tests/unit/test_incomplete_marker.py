"""不完全解析マーカーのテスト。"""

from __future__ import annotations

from pathlib import Path

from access_dependency_analyzer.core.models import AnalysisResult
from access_dependency_analyzer.exporters.incomplete_marker import (
    INCOMPLETE_FILE_NAME,
    export_incomplete_marker,
)


def test_export_incomplete_marker_writes_file(tmp_path: Path) -> None:
    result = AnalysisResult(errors=["sample.accdb: 接続失敗"])
    created = export_incomplete_marker(result, tmp_path)

    assert created is True
    marker = tmp_path / INCOMPLETE_FILE_NAME
    assert marker.exists()
    text = marker.read_text(encoding="utf-8")
    assert "不完全" in text
    assert "sample.accdb" in text


def test_export_incomplete_marker_removes_marker_when_clean(tmp_path: Path) -> None:
    marker = tmp_path / INCOMPLETE_FILE_NAME
    marker.write_text("old", encoding="utf-8")

    created = export_incomplete_marker(AnalysisResult(), tmp_path)

    assert created is False
    assert not marker.exists()
