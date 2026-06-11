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
├── .docs/                  # 更新履歴
├── assets/                 # 静的リソース（UI）
│   └── ui/
│       └── index.html
├── output/                 # 解析結果の出力先（自動生成・Git管理外）
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
├── .gitignore
├── .python-version         # pyenv / uv 用（3.12）
├── AGENTS.md
├── README.md
├── pyproject.toml          # プロジェクト定義・依存関係
├── python-version.txt      # 使用 Python バージョン（3.12）
└── requirements.txt        # pip 用依存関係一覧
```

## 必要環境

| 項目 | 内容 |
|---|---|
| OS | Windows 10 以降 |
| Python | **3.12 のみ**（3.12.x） |
| パッケージ管理 | [uv](https://github.com/astral-sh/uv)（推奨）または pip |
| **必須（リンク解析）** | [Microsoft Access Database Engine (ACE)](https://www.microsoft.com/en-us/download/details.aspx?id=54920) 2016 以降 |
| フォールバック | pyodbc（ACE 未導入時のみ。機能制限あり） |

### DAO（ACE）が必須な理由

本ツールの核心機能である **リンクテーブル解析・ファイル間依存関係の構築** は、DAO（ACE）接続が前提です。

| 機能 | DAO（ACE） | pyodbc のみ |
|---|---|---|
| テーブル名・フィールド | ○ | ○ |
| リンク接続文字列・リンク先 DB | ○ | × |
| クエリ SQL 全文 | ○ | △（制限あり） |
| フォーム / レポート | ○ | × |
| ファイル間依存グラフ | ○ | ×（リンク未検出） |

ACE 未導入環境では pyodbc にフォールバックしますが、**PostgreSQL 移行の依存関係調査には不十分**です。  
必ず ACE（64bit / 32bit は Python のビット数に合わせる）をインストールしてください。  
Access Runtime 自体は不要です。

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
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python --version   # Python 3.12.x であることを確認
pip install -r requirements.txt
pip install -e ".[dev]"
```

> `requirements.txt` は実行に必要なライブラリ一覧です。  
> `pip install -e .` でも `pyproject.toml` から同じ依存関係がインストールされます。

## 実行方法

仮想環境を有効化してから実行してください。

```powershell
.\.venv\Scripts\Activate.ps1
```

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

一部ファイルだけ再解析した結果を、既存の一括解析出力へ統合する場合:

```powershell
python -m access_dependency_analyzer --merge-retry
```

- 統合先（既定）: `output/analysis/`
- 再解析入力（既定）: `output/retry_analysis/`
- `report_for_ai.md` / 各 CSV / 依存関係図を再生成します

特定ファイルだけ上書き統合する場合（ファイル名のみ指定）:

```powershell
python -m access_dependency_analyzer --merge-retry --merge-files "QRモニタDB.accdb" "セット予定材料管理.accdb"
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
| `dependency_graph.html` | ブラウザ表示用依存関係図（オフライン対応、`mermaid.min.js` 同梱） |
| `report_for_ai.md` | AI への引き渡し用レポート |
| `_INCOMPLETE.txt` | 解析エラーあり時のみ出力される警告ファイル |

## PostgreSQL 移行での使い方

1. 社内の関連 Access ファイルをまとめて解析
2. エラーが出たファイルは個別に再解析し、`--merge-retry` で統合
3. `output/analysis/report_for_ai.md` と `tables.csv` 等を AI に渡す
4. AI に以下を依頼
   - PostgreSQL スキーマ設計
   - 移行順序
   - 共通マスタ設計
   - 上流/下流整理

## テスト

```powershell
.\.venv\Scripts\Activate.ps1
pytest
```

## 制約・注意事項

- Windows 専用です（DAO / pyodbc 前提）
- **リンク依存関係の解析には ACE（DAO）が必須**です（pyodbc のみでは不十分）
- ACE 未導入環境ではテーブル一覧のみ取得され、移行設計に必要な依存情報が欠落します
- VBA は pyOpenVBA / DAO / oletools の順で抽出を試行します
- DAO 利用時は Access の「VBA プロジェクト オブジェクト モデルへのアクセスを信頼する」設定が必要な場合があります
- `output/` 配下は解析のたびに上書き生成されます（`.gitignore` 対象）
- 一部ファイルでエラーがある場合、`_INCOMPLETE.txt` が出力されます（移行設計前に要確認）
- `dependency_graph.html` は `assets/vendor/mermaid.min.js` を同梱コピーしてオフライン表示に対応します

## 依存ライブラリ

| ライブラリ | 用途 | バージョン目安 |
|---|---|---|
| pywebview | デスクトップ UI | 5.x〜6.x |
| pywin32 | DAO による Access 読み取り | 312+ |
| pyodbc | ODBC による Access 読み取り（フォールバック） | 5.x |
| pyOpenVBA | `.accdb` / `.mdb` の VBA 抽出 | 3.x |
| oletools | VBA 抽出フォールバック（`.mdb`） | 0.60.x |
