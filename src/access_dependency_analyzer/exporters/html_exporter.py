"""HTML依存関係図エクスポート。"""

from __future__ import annotations

import logging
import shutil
from pathlib import Path

from access_dependency_analyzer.core.constants import get_assets_dir
from access_dependency_analyzer.core.models import AnalysisResult
from access_dependency_analyzer.exporters.mermaid_exporter import build_mermaid_content

logger = logging.getLogger("access_dependency_analyzer.exporters.html")

MERMAID_VENDOR_FILE = "mermaid.min.js"
MERMAID_CDN_URL = "https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Access Dependency Graph</title>
  <script src="{mermaid_script}"></script>
  <script>
    mermaid.initialize({{ startOnLoad: true, theme: "default" }});
  </script>
  <style>
    body {{
      font-family: "Segoe UI", Meiryo, sans-serif;
      margin: 24px;
      background: #f7f9fc;
      color: #1f2937;
    }}
    h1 {{
      margin-bottom: 8px;
    }}
    .meta {{
      color: #6b7280;
      margin-bottom: 24px;
    }}
    .mermaid {{
      background: #ffffff;
      border: 1px solid #e5e7eb;
      border-radius: 12px;
      padding: 24px;
    }}
  </style>
</head>
<body>
  <h1>Access 依存関係図</h1>
  <p class="meta">解析対象: {file_count} ファイル / リンク依存: {dependency_count} 件</p>
  <div class="mermaid">
{mermaid_content}
  </div>
</body>
</html>
"""


def _resolve_mermaid_script(output_dir: Path) -> str:
    """オフライン用に同梱 Mermaid を出力先へコピーし、script 参照先を返す。"""
    vendor_src = get_assets_dir() / "vendor" / MERMAID_VENDOR_FILE
    if vendor_src.exists():
        shutil.copy2(vendor_src, output_dir / MERMAID_VENDOR_FILE)
        return MERMAID_VENDOR_FILE

    logger.warning(
        "同梱 Mermaid が見つかりません。CDN を参照します: %s",
        MERMAID_CDN_URL,
    )
    return MERMAID_CDN_URL


def export_html(result: AnalysisResult, output_dir: Path) -> None:
    """dependency_graph.html を出力する。"""
    output_dir.mkdir(parents=True, exist_ok=True)
    mermaid_content = build_mermaid_content(result.dependencies)
    html = HTML_TEMPLATE.format(
        mermaid_script=_resolve_mermaid_script(output_dir),
        file_count=len(result.source_files),
        dependency_count=len(result.dependencies),
        mermaid_content=mermaid_content,
    )
    (output_dir / "dependency_graph.html").write_text(html, encoding="utf-8")
