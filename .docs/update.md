# 更新履歴

## 2026-06-11

- Access Dependency Analyzer の初版（MVP + VBA解析 + AIレポート）を実装
- テーブル / リンクテーブル / クエリ解析
- 依存関係グラフ（Markdown / Mermaid / HTML）出力
- pywebview によるドラッグ＆ドロップ UI
- `report_for_ai.md` 自動生成
- プロジェクト構成を整理（`core/` `app/` `readers/` `assets/` `output/`）
- 解析結果の既定出力先を `output/analysis/` に変更
- `.gitignore` を追加
- 不要ファイル削除（`__pycache__`、`.pytest_cache`、生成済み `output/analysis/`、`python-version.txt`）
- pywebview 向けドラッグ＆ドロップ修正（`pywebviewFullPath` 経由でファイル受付）
- VBA 抽出を多段化（pyOpenVBA → DAO → oletools）
- ネットワークパス UNC 対応（ローカルコピー経由で pyOpenVBA 解析）
- MSysObjects から VBA モジュール名を事前取得
- Python 3.12 専用化、依存パッケージのバージョン範囲を整理
- DAO テーブル読取をテーブル単位のエラーハンドリングに変更（1テーブル失敗時も解析継続）
- 初回エラー3件（QRモニタDB / セット予定材料管理 / 協力会社委託加工処理品）の再解析を実施
