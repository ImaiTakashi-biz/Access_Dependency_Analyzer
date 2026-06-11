"""パス正規化ユーティリティ。"""

from __future__ import annotations

from pathlib import Path


def is_unc_path(path: Path | str) -> bool:
    """UNC パスかどうかを判定する。"""
    text = str(path)
    return text.startswith("\\\\") or Path(path).as_posix().startswith("//")


def normalize_access_path(file_path: str | Path) -> Path:
    """Access ファイルパスを正規化する（UNC は resolve しない）。"""
    cleaned = str(file_path).strip().strip('"').strip("'")
    path = Path(cleaned)
    if is_unc_path(path):
        return path
    try:
        return path.resolve()
    except OSError:
        return path.absolute()


def normalize_access_path_str(path_text: str) -> str:
    """接続文字列等から取り出したパス文字列を正規化する。"""
    cleaned = path_text.strip().strip('"').strip("'")
    if not cleaned:
        return ""
    return str(normalize_access_path(cleaned))
