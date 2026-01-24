# CLAUDE.md

このファイルは Claude Code がこのリポジトリで作業する際のガイダンスを提供します。

## プロジェクト概要

E-Ink Weather Panel は、Raspberry Pi に接続された E-Ink ディスプレイ向けに気象情報表示画像を生成する Python アプリケーションです。Yahoo Weather API、気象庁雨雲レーダー、InfluxDB センサーデータを統合し、マルチパネルの気象ディスプレイを作成します。

## 重要な注意事項

### 外部ライブラリ (my_lib) の変更

- `my_lib` のソースコードは `../my-py-lib` に存在する
- リファクタリング等で `my_lib` の修正が必要な場合：
    1. **必ず事前に何を変更したいか説明し、確認を取ること**
    2. `../my-py-lib` で修正を行い、commit & push する
    3. このリポジトリの `pyproject.toml` のコミットハッシュを更新する
    4. `uv sync` を実行して依存関係を更新する

### プロジェクト設定ファイルの変更

- `pyproject.toml` をはじめとする一般的なプロジェクト管理ファイルは `../py-project` で管理している
- 設定ファイルを変更したい場合：
    1. **必ず事前に何を変更したいか説明し、確認を取ること**
    2. `../py-project` を使って更新する
    3. **このリポジトリの設定ファイルを直接編集しないこと**

### ドキュメントの更新

- コードを更新した際は、`README.md` や `CLAUDE.md` を更新する必要がないか検討すること
- 特に以下の場合は更新を検討：
    - 新機能の追加
    - API やコマンドの変更
    - アーキテクチャの変更
    - 設定項目の追加・変更

## 開発コマンド

### Python 環境 (uv)

```bash
# 依存関係のインストール
uv sync

# アプリケーションのローカル実行
env RASP_HOSTNAME="hostname" uv run src/display_image.py

# ユニットテスト
uv run pytest --timeout=240 -x tests/unit

# 統合テスト
uv run pytest --timeout=240 -x tests/integration

# カバレッジ付き全テスト
uv run pytest --cov=src --cov-report=html tests/

# 特定のテストファイルを実行
uv run pytest tests/unit/test_config.py

# E2E テスト (webapp の起動が必要)
uv run pytest tests/e2e/test_webapp.py --host <host-ip> --port <port>

# 型チェック
uv run pyright
```

### React フロントエンド

```bash
cd react

# 依存関係のインストール
npm ci

# 開発サーバー起動
npm run dev

# 本番用ビルド
npm run build

# Lint
npm run lint
```

### Docker 開発

```bash
# フロントエンドを先にビルド
cd react && npm ci && npm run build && cd -

# Docker Compose で実行
docker compose run --build --rm weather_panel
```

## アーキテクチャ

### コアコンポーネント

| ファイル                         | 説明                                                              |
| -------------------------------- | ----------------------------------------------------------------- |
| `src/create_image.py`            | multiprocessing を使用した並列パネル描画による画像生成            |
| `src/display_image.py`           | メインループ、Raspberry Pi への SSH 接続管理                      |
| `src/healthz.py`                 | Kubernetes liveness probe                                         |
| `src/webui.py`                   | Flask ベースの Web UI サーバー                                    |
| `src/weather_display/display.py` | SSH 接続管理、画像転送、`exec_patiently()` によるリトライロジック |
| `src/weather_display/config.py`  | frozen dataclass ベースの YAML 設定パース                         |

### 気象パネル (`src/weather_display/panel/`)

| ファイル                | 説明                                                     | データソース            |
| ----------------------- | -------------------------------------------------------- | ----------------------- |
| `weather.py`            | 天気予報 (24-48時間の時間別)、気温、降水量、風、体感温度 | Yahoo Weather API       |
| `rain_cloud.py`         | 雨雲レーダー画像 (現在 + 1時間予報)                      | 気象庁 (Selenium 経由)  |
| `sensor_graph.py`       | 複数部屋のセンサーデータ可視化 (温度、湿度、CO2、照度)   | InfluxDB                |
| `sensor_graph_utils.py` | アイコン描画、エアコン電力検出のユーティリティ           | -                       |
| `power_graph.py`        | 電力消費監視グラフ                                       | InfluxDB                |
| `wbgt.py`               | WBGT 暑さ指数表示 (5段階フェイスアイコン)                | 環境省 API              |
| `rain_fall.py`          | 現在の降水量オーバーレイ                                 | InfluxDB (雨量センサー) |
| `time.py`               | 現在時刻表示 (Asia/Tokyo タイムゾーン)                   | システム時計            |

### サポートモジュール

| モジュール                                      | 説明                                                       |
| ----------------------------------------------- | ---------------------------------------------------------- |
| `src/weather_display/timing_filter.py`          | カルマンフィルタベースの更新同期タイミング制御             |
| `src/weather_display/metrics/server.py`         | Flask ベースのメトリクス Web サーバー (別スレッド)         |
| `src/weather_display/metrics/collector.py`      | SQLite ベースのメトリクス保存と異常検知 (Isolation Forest) |
| `src/weather_display/metrics/webapi/page.py`    | メトリクスダッシュボード Web ページ                        |
| `src/weather_display/metrics/webapi/page_js.py` | メトリクスダッシュボード用 JavaScript                      |
| `src/weather_display/runner/webapi/run.py`      | `create_image.py` の非同期サブプロセス実行                 |

### 設定

- **Python バージョン**: 3.13 (3.10 以上必須)
- **2つの表示モード**: 標準 (3200x1800) と小型 (2200x1650)
- **YAML 設定** (JSON Schema バリデーション付き)
- **設定例**: `config.example.yaml` と `config-small.example.yaml`
- **全設定は frozen dataclass** にパースされ、型安全性と不変性を保証

### データフロー

1. `display_image.py` がメインループとメトリクスサーバーを起動
2. 更新サイクルごとに `create_image.py` をサブプロセスとして生成
3. `create_image.py` が `multiprocessing.Pool` を使用して 7 パネル (標準) または 4 パネル (小型) を並列生成
4. 生成画像を SSH 経由で Raspberry Pi にパイプし、`fbi` で表示

### エラーコード

| コード | 定数               | 説明                          |
| ------ | ------------------ | ----------------------------- |
| 220    | `ERROR_CODE_MINOR` | パネル生成エラー (表示は継続) |
| 222    | `ERROR_CODE_MAJOR` | 表示失敗 (クリティカルエラー) |

### 外部依存関係

- **my-py-lib**: Slack 通知、InfluxDB アクセス、画像ユーティリティ、Selenium ヘルパーのカスタムライブラリ
- **Selenium/Chrome**: `rain_cloud.py` で気象庁レーダースクレイピングに使用 (ヘッドレス Chrome 必須)
- **InfluxDB**: センサーデータ用時系列データベース (`my_lib.sensor_data.InfluxDBConfig` で設定)

## テスト戦略

### テスト構造

```
tests/
├── conftest.py              # 共有フィクスチャとヘルパー
├── unit/                    # ユニットテスト
│   ├── test_config.py           # 設定パース
│   ├── test_timing_filter.py    # カルマンフィルタロジック
│   ├── test_sensor_graph_utils.py  # ユーティリティ関数
│   ├── test_rain_fall_utils.py  # 降水量フォーマット
│   ├── test_weather_calc.py     # 体感温度計算
│   ├── test_metrics_collector.py  # メトリクスと異常検知
│   ├── test_display.py          # SSH ディスプレイ制御
│   ├── test_healthz.py          # ヘルスチェック
│   └── test_webapi_run.py       # Web API サブプロセス実行
├── integration/             # 統合テスト
│   ├── test_create_image.py     # 画像生成ワークフロー
│   ├── test_display_image.py    # ディスプレイ制御
│   ├── test_weather_panel.py    # 天気パネル
│   ├── test_sensor_graph_panel.py  # センサーグラフ
│   ├── test_power_graph_panel.py   # 電力グラフ
│   ├── test_rain_cloud_panel.py    # 雨雲レーダー (Selenium)
│   ├── test_rain_fall_panel.py     # 降水量
│   └── test_wbgt_panel.py          # WBGT
├── webapp/                  # Web API テスト
│   └── test_api.py              # Flask API エンドポイント
└── e2e/                     # E2E テスト (Playwright)
    └── test_webapp.py           # Web UI E2E テスト
```

### 主要テストフィクスチャ (conftest.py)

| フィクスチャ              | 説明                             |
| ------------------------- | -------------------------------- |
| `config` / `config_small` | 設定例ファイルのロード           |
| `ssh_mock`                | Raspberry Pi への SSH 接続モック |
| `mock_sensor_fetch_data`  | InfluxDB データ取得モック        |
| `image_checker`           | 生成画像の保存・検証ヘルパー     |
| `slack_checker`           | Slack 通知の動作検証             |

### テスト実行

- テストはデフォルトで `DUMMY_MODE=true` で実行 (実 API 呼び出しを回避)
- カバレッジレポートは `htmlcov/` に生成
- テストレポート (HTML、画像) は `reports/` に保存

## デプロイ

### ローカル

```bash
env RASP_HOSTNAME="hostname" uv run src/display_image.py
```

### Docker

- **ベース**: Ubuntu 24.04
- **ロケール**: Japanese (ja_JP.UTF-8)
- **パッケージマネージャ**: uv
- **init システム**: tini
- **Chrome**: Selenium ベースのレーダースクレイピング用にインストール済み
- **エントリポイント**: `tini` + `uv run src/display_image.py`

### Kubernetes

- **Namespace**: `panel`
- **Deployment**: `kubernetes/eink-weather-panel.yaml`
- **Liveness probe**: `healthz.py` (初期遅延 120秒、周期 60秒)
- **リソース制限**: 最小 512Mi、最大 2Gi メモリ

### 環境変数

| 変数             | 説明                                              |
| ---------------- | ------------------------------------------------- |
| `RASP_HOSTNAME`  | ターゲット Raspberry Pi のホスト名 (必須)         |
| `SSH_KEY`        | SSH 秘密鍵のパス (デフォルト: `key/panel.id_rsa`) |
| `INFLUXDB_TOKEN` | InfluxDB 認証トークン                             |
| `DUMMY_MODE`     | `true` でキャッシュ/ダミーデータを使用            |

## React フロントエンド

### 構造 (`frontend/`)

| ファイル                       | 説明                                 |
| ------------------------------ | ------------------------------------ |
| `src/App.tsx`                  | メインアプリケーションコンポーネント |
| `src/main.tsx`                 | エントリポイント                     |
| `src/App.css`, `src/index.css` | スタイリング                         |
| `vite.config.ts`               | Vite ビルド設定                      |

### 主要依存関係

- React 18.3.1 (TypeScript)
- Vite (ビルドツール)
- Bootstrap 5.3.1 (react-bootstrap)
- react-zoom-pan-pinch (画像表示)

## 主要依存関係

### バックエンド (Python)

| カテゴリ           | パッケージ                                             |
| ------------------ | ------------------------------------------------------ |
| 画像処理           | PIL/Pillow, matplotlib, opencv-contrib-python-headless |
| データ             | influxdb-client, pandas, scipy, scikit-learn           |
| Web スクレイピング | selenium                                               |
| SSH                | paramiko                                               |
| Web サーバー       | flask, flask-cors                                      |

### 開発

| カテゴリ       | パッケージ                                                                 |
| -------------- | -------------------------------------------------------------------------- |
| テスト         | pytest, pytest-cov, pytest-html, pytest-mock, pytest-xdist, pytest-timeout |
| ブラウザテスト | playwright, pytest-playwright                                              |
| 時刻モック     | time-machine                                                               |
| 品質           | pre-commit, pyright                                                        |

## コードパターン

### インポートスタイル

`from xxx import yyy` は基本的に使用せず、`import xxx` としてモジュールをインポートし、参照時は `xxx.yyy` と完全修飾名で記述する：

```python
# 推奨
import my_lib.selenium_util

driver = my_lib.selenium_util.create_driver(...)

# 非推奨
from my_lib.selenium_util import create_driver

driver = create_driver(...)
```

これにより、関数やクラスがどのモジュールに属しているかが明確になり、コードの可読性と保守性が向上する。

### 型アノテーションと型情報のないライブラリ

型情報を持たないライブラリを使用する場合、大量の `# type: ignore[union-attr]` を記載する代わりに、変数に `Any` 型を明示的に指定する：

```python
from typing import Any

# 推奨: Any 型を明示して type: ignore を不要にする
result: Any = some_untyped_lib.call()
result.method1()
result.method2()

# 非推奨: 大量の type: ignore コメント
result = some_untyped_lib.call()  # type: ignore[union-attr]
result.method1()  # type: ignore[union-attr]
result.method2()  # type: ignore[union-attr]
```

これにより、コードの可読性を維持しつつ型チェッカーのエラーを抑制できる。

### pyright エラーへの対処方針

pyright のエラー対策として、各行に `# type: ignore` コメントを記載して回避するのは**最後の手段**とする。

**優先順位：**

1. **型推論できるようにコードを修正する** - 変数の初期化時に型が明確になるようにする
2. **型アノテーションを追加する** - 関数の引数や戻り値、変数に適切な型を指定する
3. **Any 型を使用する** - 型情報のないライブラリの場合（上記セクション参照）
4. **`# type: ignore` コメント** - 上記で解決できない場合の最終手段

```python
# 推奨: 型推論可能なコード
items: list[str] = []
items.append("value")

# 非推奨: type: ignore の多用
items = []  # type: ignore[var-annotated]
items.append("value")  # type: ignore[union-attr]
```

**例外：** テストコードでは、モックやフィクスチャの都合上 `# type: ignore` の使用を許容する。

### パネル作成パターン

各パネルモジュールは以下のパターンに従う：

```python
def create(config: AppConfig) -> tuple[PIL.Image.Image, float] | tuple[PIL.Image.Image, float, str]:
    """
    戻り値:
        - (image, elapsed_time): 成功時
        - (image, elapsed_time, error_message): エラー時
    """
```

### エラーハンドリング

- パネルは `my_lib.panel_util.draw_panel_patiently()` でリトライロジックを使用
- エラーはログに記録され、オプションで Slack に通知
- 失敗したパネルはエラー画像を表示 (全体のクラッシュを防止)
- display モジュールは `exec_patiently()` で SSH コマンドをリトライ

### 設定アクセス

設定は frozen dataclass を使用：

```python
config.weather.panel.width  # パネルサイズ
config.influxdb.url         # InfluxDB 接続
config.font.path            # フォントディレクトリ
```

### マルチプロセシング戦略

- `create_image.py` が `multiprocessing.Pool` を生成してパネルを並列生成
- 各パネルは別プロセスで実行 (matplotlib のスレッド問題を回避)
- パネルごとに処理時間とエラー状態のメトリクスを収集

## 開発ワークフロー規約

### コミット時の注意

- 今回のセッションで作成し、プロジェクトが機能するのに必要なファイル以外は git add しないこと
- 気になる点がある場合は追加して良いか質問すること

### バグ修正の原則

- 憶測に基づいて修正しないこと
- 必ず原因を論理的に確定させた上で修正すること
- 「念のため」の修正でコードを複雑化させないこと

### コード修正時の確認事項

- 関連するテストも修正すること
- 関連するドキュメントも更新すること
- mypy, pyright, ty がパスすることを確認すること

### リリース時の CHANGELOG 更新

- タグを打つ際は `CHANGELOG.md` を更新すること
- `[Unreleased]` セクションの内容を新しいバージョンセクションに移動する
- 以下のカテゴリを絵文字付きで記載：
    - `### ✨ Added`: 新機能
    - `### 🔄 Changed`: 既存機能の変更
    - `### 🐛 Fixed`: バグ修正
    - `### 🗑️ Removed`: 削除された機能
    - `### 🔒 Security`: セキュリティ関連の修正
    - `### ⚡ Performance`: パフォーマンス改善
    - `### 📝 Documentation`: ドキュメント更新
    - `### 🧪 Tests`: テスト関連
    - `### 🔧 CI`: CI/CD 関連
    - `### 🏗️ Infrastructure`: インフラ関連
- 日付は `YYYY-MM-DD` 形式で記載する
