# E-Ink Weather Panel

[![Test Status](https://github.com/kimata/eink-weather-panel/actions/workflows/regression.yaml/badge.svg)](https://github.com/kimata/eink-weather-panel/actions/workflows/regression.yaml)
[![Test Report](https://img.shields.io/badge/test-report-blue)](https://kimata.github.io/eink-weather-panel/report.html)
[![Coverage Report](https://img.shields.io/badge/coverage-report-blue)](https://kimata.github.io/eink-weather-panel/coverage/)

> **総合気象パネル for E-Ink Display**
> Raspberry Pi と E-Ink ディスプレイで構築する、包括的な気象情報表示システム

## 目次

- [特徴](#特徴)
- [デモ](#デモ)
- [システム構成](#システム構成)
- [クイックスタート](#クイックスタート)
- [設定](#設定)
- [Raspberry Pi セットアップ](#raspberry-pi-セットアップ)
- [デプロイメント](#デプロイメント)
- [メトリクス機能](#メトリクス機能)
- [テスト](#テスト)
- [開発者向け](#開発者向け)
- [ライセンス](#ライセンス)

## 特徴

- **多彩な気象情報** - Yahoo Weather API、気象庁雨雲レーダー、ローカルセンサーデータを統合表示
- **高度な可視化** - 温度・湿度・照度・電力消費をリアルタイムグラフ表示
- **E-Ink最適化** - グレースケール表示に最適化されたレイアウトとフォント
- **Web インターフェース** - React製のWebアプリで画像生成とプレビュー機能
- **クラウドネイティブ** - Docker/Kubernetes対応で運用環境を選ばない

## デモ

### 表示サンプル

![表示サンプル](img/example.png)

### ライブデモ

リアルタイム画像生成を体験できます:
https://weather-panel-webapp-demo.kubernetes.green-rabbit.net/weather_panel/

## システム構成

### 主要コンポーネント

| 機能 | 説明 | 実装 |
|------|------|------|
| **天気予報** | Yahoo Weather APIから詳細な気象予報を取得 | `weather.py` |
| **雨雲レーダー** | 気象庁から最新の降水レーダー画像を取得 | `rain_cloud.py` |
| **センサーグラフ** | InfluxDBから温度・湿度・照度データを可視化 | `sensor_graph.py` |
| **電力監視** | 消費電力の履歴とトレンド分析 | `power_graph.py` |
| **WBGT指数** | 熱中症警戒レベルの算出と表示 | `wbgt.py` |
| **Web API** | React フロントエンドとの連携 | `webui.py` |

### パネル構成

| モード | 解像度 | パネル数 | 対応機器 |
|--------|--------|----------|----------|
| 標準 | 3200×1800 | 7 | BOOX Mira Pro |
| 小型 | 2200×1650 | 4 | BOOX Mira |

詳細なアーキテクチャは [ARCHITECTURE.md](ARCHITECTURE.md) を参照してください。

## クイックスタート

### 必要要件

| 項目 | 最小要件 | 推奨 |
|------|----------|------|
| **Python** | 3.10+ | 3.13 |
| **OS** | Linux | Ubuntu 24.04 |
| **メモリ** | 1GB | 2GB+ |
| **ディスク** | 500MB | 1GB+ |

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
    uv sync
    ```

### 実行方法

#### Docker Compose (推奨)

```bash
# React フロントエンドをビルド
cd react && npm ci && npm run build && cd -

# サービス起動
docker compose up --build
```

#### ローカル開発

```bash
# 画像生成と表示
env RASP_HOSTNAME="your-raspi-hostname" uv run src/display_image.py

# Web サーバー起動
uv run src/webui.py

# テスト実行
uv run pytest tests/test_basic.py
```

## 設定

### 基本設定

メインの設定ファイル `config.yaml` では以下を設定します：

```yaml
panel:
    device:
        width: 3200   # ディスプレイ幅
        height: 1800  # ディスプレイ高さ

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

- `src/weather_display/panel/sensor_graph.py` - センサーデータ取得ロジック
- `src/weather_display/panel/power_graph.py` - 電力データ処理

## Raspberry Pi セットアップ

### 対応E-Inkディスプレイ

| モデル | 解像度 | 設定ファイル |
|--------|--------|--------------|
| **BOOX Mira Pro** | 3200×1800 | `config.example.yaml` |
| **BOOX Mira** | 2200×1650 | `config-small.example.yaml` |

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
    ssh-copy-id -i key/panel.id_rsa.pub ubuntu@"your-raspi-hostname"
    ```

## デプロイメント

### 環境変数

| 変数名 | 説明 | デフォルト |
|--------|------|------------|
| `RASP_HOSTNAME` | ターゲット Raspberry Pi のホスト名 | **必須** |
| `SSH_KEY` | SSH 秘密鍵のパス | `key/panel.id_rsa` |
| `INFLUXDB_TOKEN` | InfluxDB 認証トークン | - |
| `DUMMY_MODE` | `true` でダミーデータを使用 | `false` |

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

**リソース設定:**
- Namespace: `panel`
- Liveness probe: `healthz.py`（初期遅延 120秒、周期 60秒）
- メモリ: requests 512Mi、limits 2Gi

## メトリクス機能

本システムには、パフォーマンス監視と異常検知機能が組み込まれています。SQLiteデータベースに処理時間データを自動収集し、Webインターフェースで可視化できます。

### 収集メトリクス

#### 画像生成処理 (draw_panel)

- **総処理時間** - 全パネル生成にかかる総時間
- **個別パネル処理時間** - 各パネル（天気、センサー、雨雲等）の実行時間
- **エラー情報** - 失敗したパネルとエラーメッセージ

#### 表示実行処理 (display_image)

- **表示処理時間** - Raspberry Piへの画像送信時間
- **表示タイミング** - 定期実行での時刻ずれ（diff_sec）
- **成功/失敗状況** - 表示の成功率とエラー詳細

### 分析・可視化機能

Webインターフェース（`/weather_panel/api/metrics`）で以下を提供：

- **基本統計** - 平均/最小/最大実行時間、エラー率
- **時間帯パターン** - 24時間の処理時間分布
- **異常検知** - Isolation Forest による異常な処理時間の検出

### 設定

```yaml
metrics:
    data: ./data/metrics.db
```

## テスト

### テスト構成

テストは 37 ファイルで構成されています：

```
tests/
├── conftest.py              # 共有フィクスチャ
├── test_basic.py            # 統合テスト
├── unit/                    # ユニットテスト（12ファイル）
├── integration/             # 統合テスト（9ファイル）
├── webapp/                  # Web API テスト（2ファイル）
└── e2e/                     # Playwright E2E テスト
```

### テスト実行

```bash
# 基本テスト
uv run pytest tests/test_basic.py

# カバレッジレポート生成
uv run pytest --cov=src --cov-report=html tests/

# 並列テスト（自動ワーカー数）
uv run pytest --numprocesses=auto tests/

# Selenium テストを除外
uv run pytest -m "not selenium" tests/

# E2E テスト（Web サーバー起動が必要）
uv run pytest tests/e2e/ --host <host-ip> --port <port>
```

### Pre-commit フック

```bash
# インストール
pre-commit install

# 手動実行
pre-commit run --all-files
```

### CI/CD

| プラットフォーム | 用途 |
|------------------|------|
| **GitHub Actions** | テスト実行、GitHub Pages へのレポート公開 |
| **GitLab CI** | Docker ビルド、Kubernetes デプロイ |

## 開発者向け

### アーキテクチャ

詳細なアーキテクチャ（データフロー図、シーケンス図、コードパターン）は [ARCHITECTURE.md](ARCHITECTURE.md) を参照してください。

### ディレクトリ構成

```bash
src/
├── weather_display/
│   ├── panel/             # 気象パネル実装
│   │   ├── weather.py     # 天気予報
│   │   ├── sensor_graph.py # センサーグラフ
│   │   └── rain_cloud.py  # 雨雲レーダー
│   └── metrics/           # メトリクス収集
├── webui.py               # Flask Web API
└── display_image.py       # メイン実行スクリプト

react/                     # React フロントエンド
tests/                     # テストスイート（37ファイル）
kubernetes/                # K8s マニフェスト
```

### コントリビューション

1. Fork このリポジトリ
2. Feature ブランチを作成: `git checkout -b feature/amazing-feature`
3. 変更をコミット: `git commit -m 'Add amazing feature'`
4. ブランチにプッシュ: `git push origin feature/amazing-feature`
5. Pull Request を作成

## ライセンス

**Apache License 2.0** - 詳細は [LICENSE](LICENSE) ファイルをご覧ください。

---

<div align="center">

**このプロジェクトが役に立った場合は、Star をお願いします！**

[Issue 報告](https://github.com/kimata/eink-weather-panel/issues) | [Feature Request](https://github.com/kimata/eink-weather-panel/issues/new?template=feature_request.md) | [Wiki](https://github.com/kimata/eink-weather-panel/wiki)

</div>
