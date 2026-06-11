"""VBA 読み取り用データ型。"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class RawVbaModule:
    """VBAモジュールの生データ。"""

    name: str
    code: str
