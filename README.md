# E-Ink Weather Panel

[![Test Status](https://github.com/kimata/eink-weather-panel/actions/workflows/regression.yaml/badge.svg)](https://github.com/kimata/eink-weather-panel/actions/workflows/regression.yaml)

> **総合気象パネル for E-Ink Display**
> Raspberry Pi と E-Ink ディスプレイで構築する、包括的な気象情報表示システム

## 📖 目次

- [✨ 特徴](#-特徴)
- [🎯 デモ](#-デモ)
    - [表示サンプル](#表示サンプル)
    - [ライブデモ](#ライブデモ)
- [🔧 システム構成](#-システム構成)
    - [主要コンポーネント](#主要コンポーネント)
- [🚀 クイックスタート](#-クイックスタート)
    - [必要要件](#必要要件)
    - [インストール](#インストール)
    - [実行方法](#実行方法)
- [⚙️ 設定](#️-設定)
    - [基本設定](#基本設定)
    - [センサーデータのカスタマイズ](#センサーデータのカスタマイズ)
- [🖥️ Raspberry Pi セットアップ](#️-raspberry-pi-セットアップ)
    - [対応E-Inkディスプレイ](#対応e-inkディスプレイ)
    - [基本セットアップ](#基本セットアップ)
- [☁️ デプロイメント](#️-デプロイメント)
    - [Docker Compose](#docker-compose)
    - [Kubernetes](#kubernetes)
- [📊 メトリクス機能](#-メトリクス機能)
    - [パフォーマンス監視](#パフォーマンス監視)
    - [グラフ表示機能](#グラフ表示機能)
- [📊 テスト](#-テスト)
    - [テスト実行](#テスト実行)
    - [CI/CD状況](#cicd状況)
- [🛠️ 開発者向け](#️-開発者向け)
    - [アーキテクチャ](#アーキテクチャ)
    - [コントリビューション](#コントリビューション)
- [📄 ライセンス](#-ライセンス)

## ✨ 特徴

- 🌤️ **多彩な気象情報** - Yahoo Weather API、気象庁雨雲レーダー、ローカルセンサーデータを統合表示
- 📊 **高度な可視化** - 温度・湿度・照度・電力消費をリアルタイムグラフ表示
- 🎨 **E-Ink最適化** - グレースケール表示に最適化されたレイアウトとフォント
- 🌐 **Web インターフェース** - React製のWebアプリで画像生成とプレビュー機能
- ☁️ **クラウドネイティブ** - Docker/Kubernetes対応で運用環境を選ばない

## 🎯 デモ

### 表示サンプル

![表示サンプル](img/example.png)

### ライブデモ

リアルタイム画像生成を体験できます:
https://weather-panel-webapp-demo.kubernetes.green-rabbit.net/weather_panel/

## 🔧 システム構成

### 主要コンポーネント

| 機能               | 説明                                       | 実装                  |
| ------------------ | ------------------------------------------ | --------------------- |
| **天気予報**       | Yahoo Weather APIから詳細な気象予報を取得  | `weather_panel.py`    |
| **雨雲レーダー**   | 気象庁から最新の降水レーダー画像を取得     | `rain_cloud_panel.py` |
| **センサーグラフ** | InfluxDBから温度・湿度・照度データを可視化 | `sensor_graph.py`     |
| **電力監視**       | 消費電力の履歴とトレンド分析               | `power_graph.py`      |
| **WBGT指数**       | 熱中症警戒レベルの算出と表示               | `wbgt_panel.py`       |
| **Web API**        | React フロントエンドとの連携               | `webui.py`            |

## 🚀 クイックスタート

### 必要要件

| 項目         | 最小要件 | 推奨         |
| ------------ | -------- | ------------ |
| **Python**   | 3.10+    | 3.13+        |
| **OS**       | Linux    | Ubuntu 24.04 |
| **メモリ**   | 1GB      | 2GB+         |
| **ディスク** | 500MB    | 1GB+         |

### インストール

1. **リポジトリのクローン**

    ```bash
    git clone https://github.com/kimata/eink-weather-panel.git
    cd eink-weather-panel
    ```

2. **設定ファイルの準備**

    ```bash
    cp config.example.yaml config.yaml
    cp config-small.example.yaml config-small.yaml
    # お手元の環境に合わせて編集
    ```

3. **依存関係のインストール**
    ```bash
    # UV使用
    uv sync
    ```

### 実行方法

#### 🐳 Docker Compose (推奨)

```bash
# React フロントエンドをビルド
cd react && npm ci && npm run build && cd -

# サービス起動
docker compose up --build
```

#### 🔧 ローカル開発

```bash
# 画像生成と表示
env RASP_HOSTNAME="your-raspi-hostname" uv run src/display_image.py

# Web サーバー起動
uv run src/webui.py

# テスト実行
uv run pytest tests/test_basic.py
```

## ⚙️ 設定

### 基本設定

メインの設定ファイル `config.yaml` では以下を設定します：

```yaml
panel:
    device:
        width: 3200 # ディスプレイ幅
        height: 1800 # ディスプレイ高さ

influxdb:
    url: "http://your-influxdb:8086"
    org: "your-org"
    bucket: "sensor-data"
    token: "your-token"

weather:
    location: "東京都"
    yahoo_app_id: "your-yahoo-app-id"
```

### センサーデータのカスタマイズ

InfluxDBスキーマに合わせて調整が必要な場合：

- `src/weather_display/sensor_graph.py` - センサーデータ取得ロジック
- `src/weather_display/power_graph.py` - 電力データ処理

## 🖥️ Raspberry Pi セットアップ

### 対応E-Inkディスプレイ

| モデル            | 解像度    | 設定値 | 備考             |
| ----------------- | --------- | ------ | ---------------- |
| **BOOX Mira Pro** | 3200×1800 | ✅     | 大型・高解像度   |
| **BOOX Mira**     | 2200×1650 | ✅     | 中型・省スペース |

### 基本セットアップ

1. **必要パッケージのインストール**

    ```bash
    sudo apt-get update
    sudo apt-get install -y fbi
    ```

2. **ディスプレイ解像度設定**

    `/boot/firmware/config.txt` に追加：

    **BOOX Mira Pro (3200×1800)**

    ```ini
    framebuffer_width=3200
    framebuffer_height=1800
    max_framebuffer_width=3200
    max_framebuffer_height=1800
    hdmi_group=2
    hdmi_mode=87
    hdmi_timings=3200 1 48 32 80 1800 1 3 5 54 0 0 0 10 0 183422400 3
    ```

    **BOOX Mira (2200×1650)**

    ```ini
    framebuffer_width=2200
    framebuffer_height=1650
    max_framebuffer_width=2200
    max_framebuffer_height=1650
    hdmi_group=2
    hdmi_mode=87
    hdmi_timings=2200 1 48 32 80 1650 1 3 5 54 0 0 0 10 0 160000000 1
    ```

3. **画面の消灯防止**

    ```bash
    # /boot/firmware/cmdline.txtに追加
    echo "consoleblank=0" | sudo tee -a /boot/firmware/cmdline.txt
    ```

4. **SSH認証設定**
    ```bash
    # SSH公開鍵をコピー
    ssh-copy-id -i key/panel.id_rsa.pub ubuntu@"your-raspi-hostname"
    ```

## ☁️ デプロイメント

### Docker Compose

```yaml
# compose.yaml の例
services:
    weather_panel:
        build: .
        environment:
            - RASP_HOSTNAME=your-raspi-hostname
        volumes:
            - ./config.yaml:/app/config.yaml
            - ./key:/app/key
```

### Kubernetes

```bash
# Kubernetesデプロイ
kubectl apply -f kubernetes/eink-weather-panel.yaml

# 設定の更新
kubectl create configmap weather-config --from-file=config.yaml
```

## 📊 メトリクス機能

本システムには、パフォーマンス監視と異常検知機能が組み込まれています。SQLiteデータベースに処理時間データを自動収集し、Webインターフェースで可視化できます。

### 収集メトリクス

システムが自動的に以下のデータを収集します：

#### 画像生成処理 (draw_panel)

- **総処理時間** - 全パネル生成にかかる総時間
- **個別パネル処理時間** - 各パネル（天気、センサー、雨雲等）の実行時間
- **エラー情報** - 失敗したパネルとエラーメッセージ
- **実行モード** - 小型モード、テストモード、ダミーモード
- **タイムスタンプ** - 時間帯・曜日分析用

#### 表示実行処理 (display_image)

- **表示処理時間** - Raspberry Piへの画像送信時間
- **表示タイミング** - 定期実行での時刻ずれ（diff_sec）
- **成功/失敗状況** - 表示の成功率とエラー詳細
- **対象ホスト名** - 複数Raspberry Pi環境での識別

### 分析・可視化機能

Webインターフェース（`/weather_panel/api/metrics`）で以下を提供：

#### 統計ダッシュボード

- **基本統計** - 平均/最小/最大実行時間、エラー率
- **時間帯パターン** - 24時間の処理時間分布
- **パフォーマンス推移** - 日別の処理時間トレンド
- **パネル別分析** - 各気象パネルの処理時間比較

#### 異常検知

- **Isolation Forest** - 機械学習による異常な処理時間の検出
- **アラート機能** - 設定した閾値を超えた場合の警告
- **箱ヒゲ図** - 処理時間の統計分布と外れ値の可視化

### 設定

設定ファイル（config.yaml）でデータベースパスを指定：

```yaml
metrics:
    data: ./data/metrics.db
```

メトリクスは処理実行時に自動収集され、手動設定は不要です。

## 📊 テスト

### テスト実行

```bash
# 基本テスト
uv run pytest tests/test_basic.py

# カバレッジレポート生成
uv run pytest --cov=src --cov-report=html tests/

# 並列テスト
uv run pytest --numprocesses=auto tests/
```

### CI/CD状況

- **テスト結果**: [GitHub Actions](https://github.com/kimata/eink-weather-panel/actions)
- **カバレッジレポート**: [Coverage Report](https://kimata.github.io/eink-weather-panel/coverage/)
- **テスト詳細**: [Test Results](https://kimata.github.io/eink-weather-panel/)

## 🛠️ 開発者向け

### アーキテクチャ

#### 詳細データフロー図

```mermaid
flowchart TB
    subgraph "外部データソース"
        YAHOO[Yahoo Weather API<br/>🌤️ 7日間予報<br/>📊 気温・湿度・風速]
        JMA[気象庁雨雲レーダー<br/>🌧️ リアルタイム降水量<br/>🗾 地域別降水分布]
        INFLUX[InfluxDB<br/>📈 時系列センサーデータ<br/>🌡️ 温度・湿度・照度・CO2]
        POWER_DB[Power Monitor DB<br/>⚡ 電力消費データ<br/>📊 使用量履歴]
    end

    subgraph "コア処理エンジン"
        DI[display_image.py<br/>🎛️ メイン実行制御<br/>⏰ 定期実行スケジューラー<br/>🔄 タイミング制御]
        CI[create_image.py<br/>🖼️ 画像合成エンジン<br/>⚙️ マルチプロセス制御<br/>📏 レイアウト管理]
    end

    subgraph "気象パネル処理"
        WP[weather.py<br/>🌤️ 天気予報パネル<br/>📅 7日間予報表示<br/>🎨 天気アイコン生成]
        RC[rain_cloud.py<br/>🌧️ 雨雲レーダーパネル<br/>🗾 地図合成処理<br/>🎯 位置マーカー]
        RF[rain_fall.py<br/>☔ 降水量グラフ<br/>📊 時間別降水量<br/>📈 予報データ]
        SG[sensor_graph.py<br/>📊 センサーグラフ<br/>📈 多軸グラフ生成<br/>🎨 カラーマップ]
        PG[power_graph.py<br/>⚡ 電力グラフ<br/>📊 消費量推移<br/>💰 コスト計算]
        WBGT[wbgt.py<br/>🌡️ WBGT指数<br/>⚠️ 熱中症警戒<br/>🚨 アラート表示]
        TP[time.py<br/>🕐 現在時刻<br/>📅 日付表示<br/>🌅 日の出・日の入り]
    end

    subgraph "Web インターフェース"
        WEBAPP[webui.py<br/>🌐 Flask REST API<br/>🔄 非同期処理<br/>📤 JSON レスポンス]
        REACT[React Frontend<br/>⚛️ SPA アプリ<br/>🖼️ リアルタイムプレビュー<br/>⚙️ パラメータ調整]
        GENERATOR[generator.py<br/>🎛️ Web画像生成<br/>🔧 動的パラメータ<br/>📱 レスポンシブ対応]
    end

    subgraph "表示・出力"
        DISPLAY[🖥️ E-Ink Display<br/>📺 Raspberry Pi<br/>🔌 SSH接続<br/>🖼️ フレームバッファ出力]
        PNG_OUTPUT[🖼️ PNG画像ファイル<br/>💾 ローカル保存<br/>🌐 Web配信]
    end

    subgraph "監視・メトリクス"
        MCOLLECT[metrics/collector.py<br/>📊 パフォーマンス収集<br/>⏱️ 実行時間測定<br/>❌ エラー追跡]
        MSERVER[metrics/server.py<br/>🌐 メトリクスAPI<br/>📈 統計処理<br/>🔍 異常検知]
        SQLITE[(SQLite DB<br/>📁 metrics.db<br/>📊 パフォーマンス履歴<br/>⚠️ エラーログ)]
    end

    subgraph "設定・制御"
        CONFIG[config.yaml<br/>⚙️ システム設定<br/>🎨 レイアウト定義<br/>🔧 API認証情報]
        TIMING[timing_filter.py<br/>⏰ カルマンフィルター<br/>🎯 更新タイミング制御<br/>📐 遅延補正]
    end

    %% データフロー接続
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

    CONFIG --> DI
    CONFIG --> CI
    CONFIG --> WP
    CONFIG --> RC
    CONFIG --> SG

    DI --> CI
    CI --> PNG_OUTPUT
    DI --> DISPLAY

    REACT --> WEBAPP
    WEBAPP --> GENERATOR
    GENERATOR --> CI

    DI --> MCOLLECT
    CI --> MCOLLECT
    MCOLLECT --> SQLITE
    MSERVER --> SQLITE
    DI --> MSERVER

    TIMING --> DI

    %% スタイリング
    style YAHOO fill:#e3f2fd
    style JMA fill:#e8f5e8
    style INFLUX fill:#fff3e0
    style POWER_DB fill:#fce4ec
    style DI fill:#e1f5fe
    style CI fill:#f3e5f5
    style WEBAPP fill:#e8f5e8
    style REACT fill:#fff3e0
    style SQLITE fill:#f5f5f5
    style DISPLAY fill:#ffebee
```

#### create_image.py と display_image.py のインタラクション

```mermaid
sequenceDiagram
    participant User as 👤 User/Cron
    participant DI as display_image.py<br/>🎛️ Main Controller
    participant TC as timing_filter.py<br/>⏰ Timing Control
    participant SSH as 🔗 SSH Connection
    participant CI as create_image.py<br/>🖼️ Image Generator
    participant MP as 🔄 Multiprocess Pool
    participant P1 as 🌤️ Weather Panel
    participant P2 as 🌧️ Rain Panel
    participant P3 as 📊 Sensor Panel
    participant PN as ⚡ Other Panels...
    participant MC as metrics/collector.py<br/>📊 Metrics
    participant DB as 💾 SQLite DB
    participant RPI as 🥧 Raspberry Pi

    User->>DI: python display_image.py

    Note over DI: 🚀 Initialize & Load Config
    DI->>DI: Load config.yaml
    DI->>TC: Initialize TimingController
    DI->>SSH: ssh_connect(rasp_hostname)

    loop ♾️ Main Display Loop
        Note over DI: ⏰ Calculate Sleep Time
        DI->>TC: calculate_sleep_time()
        TC-->>DI: sleep_time, diff_sec

        Note over DI: 🎯 Execute Display Process
        DI->>SSH: ssh_kill_and_close("fbi")
        DI->>CI: subprocess call create_image.py

        Note over CI: 🖼️ Image Generation Process
        CI->>MP: Create multiprocess pool

        par 🔄 Parallel Panel Generation
            CI->>P1: weather.create()
            CI->>P2: rain_cloud.create()
            CI->>P3: sensor_graph.create()
            CI->>PN: other panels...
        end

        Note over MP: ⏳ Wait for all panels
        P1-->>CI: (panel_image, elapsed_time)
        P2-->>CI: (panel_image, elapsed_time)
        P3-->>CI: (panel_image, elapsed_time)
        PN-->>CI: (panel_image, elapsed_time)

        CI->>CI: Composite all panels
        CI->>MC: collect_draw_panel_metrics()
        MC->>DB: INSERT panel metrics

        CI-->>DI: Return PNG image

        Note over DI: 📤 Display on E-Ink
        DI->>SSH: scp image to Raspberry Pi
        DI->>SSH: fbi command for display
        SSH->>RPI: Display image on E-Ink

        DI->>MC: collect_display_image_metrics()
        MC->>DB: INSERT display metrics

        alt 🔄 Continuous Mode
            DI->>DI: sleep(sleep_time)
        else 1️⃣ One-time Mode
            DI->>User: Exit
        end
    end

    Note over DI,DB: 📊 Metrics Collection Throughout Process
    Note over TC: 🎯 Adaptive timing control using Kalman filter
    Note over MP: ⚡ Parallel processing for performance
```

#### パネル生成の詳細フロー

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
    participant MC as Metrics Collector

    Note over CI: 🚀 Start Panel Generation
    CI->>MP: Create process pool

    par 🌤️ Weather Panel
        MP->>WP: weather.create(config)
        WP->>API1: Request 7-day forecast
        API1-->>WP: Weather data (JSON)
        WP->>WP: Generate weather icons
        WP->>WP: Create forecast layout
        WP-->>MP: (weather_image, elapsed_time)
    and 🌧️ Rain Cloud Panel
        MP->>RC: rain_cloud.create(config)
        RC->>API2: Download radar image
        API2-->>RC: Rain radar PNG
        RC->>RC: Overlay location markers
        RC->>RC: Add timestamp & legend
        RC-->>MP: (rain_image, elapsed_time)
    and 📊 Sensor Panel
        MP->>SG: sensor_graph.create(config)
        SG->>API3: Query sensor data
        API3-->>SG: Time series data
        SG->>SG: Generate multi-axis graphs
        SG->>SG: Apply color mapping
        SG-->>MP: (sensor_image, elapsed_time)
    end

    Note over MP: ⏳ Wait for all panels to complete
    MP-->>CI: All panel images + metrics

    CI->>CI: Composite panels onto base image
    CI->>MC: Record total generation time

    Note over CI: 📊 Performance Monitoring
    CI->>MC: Log individual panel times
    CI->>MC: Log any errors occurred
    MC->>MC: Calculate statistics
```

#### ファイル構成

```bash
src/
├── weather_display/        # 表示パネル実装
│   ├── weather_panel.py   # 天気予報
│   ├── sensor_graph.py    # センサーグラフ
│   └── rain_cloud_panel.py # 雨雲レーダー
├── webui.py               # Flask Web API
└── display_image.py       # メイン実行スクリプト

react/                     # React フロントエンド
tests/                     # テストスイート
kubernetes/                # K8s マニフェスト
```

### コントリビューション

1. Fork このリポジトリ
2. Feature ブランチを作成: `git checkout -b feature/amazing-feature`
3. 変更をコミット: `git commit -m 'Add amazing feature'`
4. ブランチにプッシュ: `git push origin feature/amazing-feature`
5. Pull Request を作成

## 📄 ライセンス

**Apache License 2.0** - 詳細は [LICENSE](LICENSE) ファイルをご覧ください。

---

<div align="center">

**⭐ このプロジェクトが役に立った場合は、Star をお願いします！**

[🐛 Issue 報告](https://github.com/kimata/eink-weather-panel/issues) | [💡 Feature Request](https://github.com/kimata/eink-weather-panel/issues/new?template=feature_request.md) | [📖 Wiki](https://github.com/kimata/eink-weather-panel/wiki)

</div>
