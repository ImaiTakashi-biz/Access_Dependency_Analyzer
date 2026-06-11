"""Access ファイルのローカル読み取り支援。"""

from __future__ import annotations

import logging
import shutil
import tempfile
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from access_dependency_analyzer.utils.path_utils import (
    is_unc_path,
    normalize_access_path,
)

logger = logging.getLogger("access_dependency_analyzer.readers.file_resolver")

__all__ = ["is_unc_path", "normalize_access_path", "local_access_file"]


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
