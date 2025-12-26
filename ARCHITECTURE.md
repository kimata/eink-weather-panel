# Architecture

E-Ink Weather Panel のアーキテクチャ詳細ドキュメント。

## 目次

- [システム概要](#システム概要)
- [コアコンポーネント](#コアコンポーネント)
- [気象パネル](#気象パネル)
- [サポートモジュール](#サポートモジュール)
- [データフロー](#データフロー)
- [コードパターン](#コードパターン)
- [エラーコード](#エラーコード)

## システム概要

```
src/
├── create_image.py              # 画像生成エンジン（マルチプロセス）
├── display_image.py             # メイン実行スクリプト
├── healthz.py                   # Kubernetes ヘルスチェック
├── webui.py                     # Flask Web API サーバー
└── weather_display/
    ├── config.py                # YAML設定パーサー（frozen dataclass）
    ├── display.py               # SSH接続・画像転送処理
    ├── timing_filter.py         # カルマンフィルタベースのタイミング制御
    ├── panel/                   # 気象パネルモジュール
    │   ├── weather.py           # 天気予報パネル
    │   ├── rain_cloud.py        # 雨雲レーダーパネル
    │   ├── rain_fall.py         # 降水量グラフ
    │   ├── sensor_graph.py      # センサーグラフ
    │   ├── sensor_graph_utils.py
    │   ├── power_graph.py       # 電力消費グラフ
    │   ├── wbgt.py              # WBGT熱中症指数
    │   └── time.py              # 時刻表示
    ├── metrics/                 # メトリクス収集・分析
    │   ├── collector.py         # SQLiteメトリクス収集
    │   ├── server.py            # メトリクスWebサーバー
    │   └── webapi/              # メトリクスダッシュボード
    └── runner/                  # Web APIサブプロセス実行
        └── webapi/run.py
```

## コアコンポーネント

| ファイル | 説明 |
|----------|------|
| `src/create_image.py` | マルチプロセスプールによる並列パネルレンダリング |
| `src/display_image.py` | メインアプリケーションループ、Raspberry Pi への SSH 接続管理 |
| `src/healthz.py` | Kubernetes liveness probe 実装 |
| `src/webui.py` | Flask ベースの Web UI サーバー |
| `src/weather_display/display.py` | SSH 接続管理、画像転送、`exec_patiently()` によるリトライロジック |
| `src/weather_display/config.py` | frozen dataclass ベースの設定（YAML パース） |

## 気象パネル

`src/weather_display/panel/` 配下のパネルモジュール:

| ファイル | 説明 | データソース |
|----------|------|--------------|
| `weather.py` | 天気予報（24-48時間の時間別予報）、気温、降水量、風速、体感温度 | Yahoo Weather API |
| `rain_cloud.py` | 雨雲レーダー画像（現在 + 1時間予報） | 気象庁（Selenium 経由） |
| `sensor_graph.py` | 複数部屋のセンサーデータ可視化（温度、湿度、CO2、照度）、非同期取得 | InfluxDB |
| `sensor_graph_utils.py` | アイコン描画、エアコン稼働検出のユーティリティ関数 | - |
| `power_graph.py` | 電力消費監視グラフ（履歴トレンド付き） | InfluxDB |
| `wbgt.py` | WBGT 熱中症指数表示（5段階フェイスアイコン） | 環境省 API |
| `rain_fall.py` | 現在の降水量オーバーレイ（継続時間追跡） | InfluxDB（雨量センサー） |
| `time.py` | 現在時刻表示（Asia/Tokyo タイムゾーン） | システムクロック |

### パネル構成

| モード | 解像度 | パネル数 | パネル一覧 |
|--------|--------|----------|------------|
| 標準 | 3200×1800 | 7 | weather, sensor_graph, power_graph, wbgt, rain_cloud, rain_fall, time |
| 小型 | 2200×1650 | 4 | weather, sensor_graph, rain_cloud, time |

## サポートモジュール

| モジュール | 説明 |
|------------|------|
| `src/weather_display/timing_filter.py` | 更新同期のためのカルマンフィルタベースタイミング制御 |
| `src/weather_display/metrics/server.py` | Flask ベースのメトリクス Web サーバー（別スレッド実行） |
| `src/weather_display/metrics/collector.py` | SQLite ベースのメトリクス保存（Isolation Forest による異常検知） |
| `src/weather_display/metrics/webapi/page.py` | メトリクスダッシュボード Web ページ |
| `src/weather_display/runner/webapi/run.py` | `create_image.py` の非同期サブプロセス実行（stdout/stderr ストリーミング） |

## データフロー

### 全体フロー

```mermaid
flowchart TB
    subgraph "外部データソース"
        YAHOO[Yahoo Weather API<br/>7日間予報]
        JMA[気象庁雨雲レーダー<br/>リアルタイム降水量]
        INFLUX[InfluxDB<br/>時系列センサーデータ]
        POWER_DB[Power Monitor DB<br/>電力消費データ]
    end

    subgraph "コア処理エンジン"
        DI[display_image.py<br/>メイン実行制御]
        CI[create_image.py<br/>画像合成エンジン]
    end

    subgraph "気象パネル処理"
        WP[weather.py]
        RC[rain_cloud.py]
        RF[rain_fall.py]
        SG[sensor_graph.py]
        PG[power_graph.py]
        WBGT[wbgt.py]
        TP[time.py]
    end

    subgraph "Web インターフェース"
        WEBAPP[webui.py<br/>Flask REST API]
        REACT[React Frontend]
    end

    subgraph "表示・出力"
        DISPLAY[E-Ink Display<br/>Raspberry Pi]
        PNG_OUTPUT[PNG画像ファイル]
    end

    subgraph "監視・メトリクス"
        MCOLLECT[metrics/collector.py]
        MSERVER[metrics/server.py]
        SQLITE[(SQLite DB)]
    end

    YAHOO --> WP
    JMA --> RC
    JMA --> RF
    INFLUX --> SG
    POWER_DB --> PG

    WP --> CI
    RC --> CI
    RF --> CI
    SG --> CI
    PG --> CI
    WBGT --> CI
    TP --> CI

    DI --> CI
    CI --> PNG_OUTPUT
    DI --> DISPLAY

    REACT --> WEBAPP
    WEBAPP --> CI

    DI --> MCOLLECT
    CI --> MCOLLECT
    MCOLLECT --> SQLITE
    MSERVER --> SQLITE

    style DI fill:#e1f5fe
    style CI fill:#f3e5f5
    style DISPLAY fill:#ffebee
```

### シーケンス図

```mermaid
sequenceDiagram
    participant User as User/Cron
    participant DI as display_image.py
    participant TC as timing_filter.py
    participant CI as create_image.py
    participant MP as Multiprocess Pool
    participant Panels as Weather Panels
    participant MC as metrics/collector.py
    participant RPI as Raspberry Pi

    User->>DI: python display_image.py

    Note over DI: Initialize & Load Config
    DI->>TC: Initialize TimingController

    loop Main Display Loop
        DI->>TC: calculate_sleep_time()
        TC-->>DI: sleep_time, diff_sec

        DI->>CI: subprocess call create_image.py

        Note over CI: Image Generation Process
        CI->>MP: Create multiprocess pool

        par Parallel Panel Generation
            MP->>Panels: weather.create()
            MP->>Panels: rain_cloud.create()
            MP->>Panels: sensor_graph.create()
            MP->>Panels: other panels...
        end

        Panels-->>CI: (panel_images, elapsed_times)
        CI->>CI: Composite all panels
        CI->>MC: collect_draw_panel_metrics()

        CI-->>DI: Return PNG image

        DI->>RPI: scp image + fbi command
        DI->>MC: collect_display_image_metrics()

        DI->>DI: sleep(sleep_time)
    end
```

### パネル生成詳細

```mermaid
sequenceDiagram
    participant CI as create_image.py
    participant MP as Multiprocess Pool
    participant WP as weather.py
    participant API1 as Yahoo Weather API
    participant RC as rain_cloud.py
    participant API2 as 気象庁レーダー
    participant SG as sensor_graph.py
    participant API3 as InfluxDB

    CI->>MP: Create process pool

    par Weather Panel
        MP->>WP: weather.create(config)
        WP->>API1: Request forecast
        API1-->>WP: Weather data (JSON)
        WP-->>MP: (weather_image, elapsed_time)
    and Rain Cloud Panel
        MP->>RC: rain_cloud.create(config)
        RC->>API2: Download radar image
        API2-->>RC: Rain radar PNG
        RC-->>MP: (rain_image, elapsed_time)
    and Sensor Panel
        MP->>SG: sensor_graph.create(config)
        SG->>API3: Query sensor data
        API3-->>SG: Time series data
        SG-->>MP: (sensor_image, elapsed_time)
    end

    MP-->>CI: All panel images + metrics
    CI->>CI: Composite panels onto base image
```

## コードパターン

### パネル作成パターン

各パネルモジュールは以下のパターンに従います:

```python
def create(config: AppConfig) -> tuple[PIL.Image.Image, float] | tuple[PIL.Image.Image, float, str]:
    """
    Returns:
        - (image, elapsed_time) on success
        - (image, elapsed_time, error_message) on error
    """
```

### エラーハンドリング

- パネルは `my_lib.panel_util.draw_panel_patiently()` でリトライロジックを使用
- エラーはログに記録され、オプションで Slack に通知
- 失敗したパネルはエラー画像を表示（ディスプレイ全体はクラッシュしない）
- display モジュールは `exec_patiently()` で SSH コマンドをリトライ

### 設定アクセス

設定は frozen dataclass を使用:

```python
config.weather.panel.width  # パネルサイズ
config.influxdb.url         # InfluxDB 接続
config.font.path            # フォントディレクトリ
```

### マルチプロセス戦略

- `create_image.py` は `multiprocessing.Pool` を生成してパネルを並列生成
- 各パネルは別プロセスで実行（matplotlib のスレッド問題を回避）
- パネルごとに経過時間とエラーステータスのメトリクスを収集

## エラーコード

| コード | 定数 | 説明 |
|--------|------|------|
| 220 | `ERROR_CODE_MINOR` | パネル生成エラー（表示は継続） |
| 222 | `ERROR_CODE_MAJOR` | 表示失敗（致命的エラー） |

## 外部依存関係

| 依存 | 説明 |
|------|------|
| **my-py-lib** | Slack 通知、InfluxDB アクセス、画像ユーティリティ、Selenium ヘルパー |
| **Selenium/Chrome** | `rain_cloud.py` で気象庁レーダースクレイピングに使用（ヘッドレス Chrome 必須） |
| **InfluxDB** | センサーデータ用時系列データベース |
