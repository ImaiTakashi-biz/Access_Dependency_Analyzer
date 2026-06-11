"""Access ファイルのローカル読み取り支援。"""

from __future__ import annotations

import logging
import shutil
import tempfile
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

logger = logging.getLogger("access_dependency_analyzer.readers.file_resolver")

UNC_PREFIXES = ("\\\\", "//")


def is_unc_path(path: Path) -> bool:
    """UNC パスかどうかを判定する。"""
    return path.as_posix().startswith("//") or str(path).startswith("\\\\")


def normalize_access_path(file_path: str | Path) -> Path:
    """Access ファイルパスを正規化する（UNC は resolve しない）。"""
    path = Path(file_path)
    if is_unc_path(path):
        return path
    try:
        return path.resolve()
    except OSError:
        return path.absolute()


@contextmanager
def local_access_file(file_path: str | Path) -> Iterator[Path]:
    """ネットワーク上の Access ファイルをローカルへコピーして読み取る。"""
    source = normalize_access_path(file_path)
    if not source.exists():
        raise FileNotFoundError(f"Accessファイルが見つかりません: {source}")

    if not is_unc_path(source):
        yield source
        return

    suffix = source.suffix or ".accdb"
    temp_dir = Path(tempfile.mkdtemp(prefix="access_analyzer_"))
    local_copy = temp_dir / f"source{suffix}"

    try:
        logger.info("ネットワークファイルをローカルへコピーします: %s", source.name)
        shutil.copy2(source, local_copy)
        yield local_copy
    finally:
        try:
            shutil.rmtree(temp_dir, ignore_errors=True)
        except OSError:
            logger.debug("一時ファイル削除に失敗しました", exc_info=True)
