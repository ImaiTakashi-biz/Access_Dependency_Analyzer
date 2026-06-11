# Access Dependency Analyzer

Microsoft Access システム群の依存関係を自動解析し、Python + PostgreSQL 移行を支援する Windows 向けデスクトップツールです。

## 機能概要

- テーブル解析（実テーブル / リンクテーブル、フィールド、主キー、レコード数）
- リンクテーブル解析（リンク元・リンク先 Access、接続情報）
- クエリ解析（SQL全文、参照テーブル、更新系/参照系判定）
- VBA解析（モジュールコード、SQL文字列、DoCmd/DAO/ADODB 利用箇所）
- Access ファイル間の依存関係解析
- 解析結果の CSV / Markdown / Mermaid / HTML / AIレポート出力

## プロジェクト構成

```text
Access_Dependency_Analyzer/
├── .docs/                  # 更新履歴などのドキュメント
├── assets/                 # 静的リソース（UI）
│   └── ui/
│       └── index.html
├── output/                 # 解析結果の出力先（自動生成・gitignore）
│   └── .gitkeep
├── src/
│   └── access_dependency_analyzer/
│       ├── __main__.py     # python -m 用エントリ
│       ├── main.py         # アプリ起動
│       ├── app/            # UI / API ブリッジ
│       ├── core/           # モデル・定数・ログ
│       ├── readers/        # Access / VBA 読み取り
│       ├── analyzers/      # 解析ロジック
│       ├── exporters/      # 結果出力
│       └── utils/          # 共通ユーティリティ
├── tests/
│   ├── conftest.py
│   └── unit/               # 単体テスト
├── AGENTS.md
├── README.md
├── pyproject.toml
└── requirements.txt
```

## 必要環境

- Windows 10 以降
- Python 3.12
- [uv](https://github.com/astral-sh/uv)（推奨）または pip
- Microsoft Access Database Engine (ACE) 2016 以降（推奨）
  - DAO 経由でリンクテーブル接続文字列やクエリ SQL を安定取得できます
  - Access Runtime 自体は不要です

### 環境変数

本ツールで必須の環境変数はありません。

## セットアップ

### uv を使う場合（推奨）

```powershell
cd C:\Users\SEIZOU20\PythonProjects\Access_Dependency_Analyzer
uv venv --python 3.12
uv pip install -e .
uv pip install pytest
```

### pip を使う場合

```powershell
cd C:\Users\SEIZOU20\PythonProjects\Access_Dependency_Analyzer
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
pip install -e .
```

## 実行方法

### GUI（pywebview）

```powershell
python -m access_dependency_analyzer
```

または

```powershell
access-analyzer
```

操作手順:

1. `.accdb` / `.mdb` をドラッグ＆ドロップ、または「ファイル選択」で複数指定
2. 「解析開始」をクリック
3. `output/analysis/` に結果が出力されます

### CLI

```powershell
python -m access_dependency_analyzer --files "C:\data\製品マスタ.accdb" "C:\data\不具合情報.accdb"
```

出力先を変更する場合:

```powershell
python -m access_dependency_analyzer --files "C:\data\製品マスタ.accdb" --output output/analysis
```

## 出力ファイル

`output/analysis/` フォルダに以下を生成します。

| ファイル | 内容 |
|---|---|
| `tables.csv` | テーブル一覧 |
| `linked_tables.csv` | リンクテーブル一覧 |
| `queries.csv` | クエリ一覧 |
| `forms.csv` | フォーム一覧 |
| `reports.csv` | レポート一覧 |
| `vba_modules.csv` | VBAモジュール一覧 |
| `relationship.md` | 上流/中間/下流の整理 |
| `dependency_graph.mmd` | Mermaid 依存関係図 |
| `dependency_graph.html` | ブラウザ表示用依存関係図 |
| `report_for_ai.md` | AI への引き渡し用レポート |

## PostgreSQL 移行での使い方

1. 社内の関連 Access ファイルをまとめて解析
2. `report_for_ai.md` を AI に渡す
3. AI に以下を依頼
   - PostgreSQL スキーマ設計
   - 移行順序
   - 共通マスタ設計
   - 上流/下流整理

## テスト

```powershell
pytest
```

## 制約・注意事項

- Windows 専用です（DAO / pyodbc 前提）
- ACE 未導入環境では解析範囲が限定されます
- pyodbc モードではリンク接続文字列が取得できない場合があります
- VBA は oletools による抽出のため、難読化や破損ファイルでは取得できない場合があります
- `output/` 配下は解析のたびに上書き生成されます（Git 管理対象外）
