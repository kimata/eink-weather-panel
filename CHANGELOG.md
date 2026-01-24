# Changelog

このプロジェクトの注目すべき変更点をすべてこのファイルに記載します。

このファイルのフォーマットは [Keep a Changelog](https://keepachangelog.com/ja/1.1.0/) に基づいており、
このプロジェクトは [Semantic Versioning](https://semver.org/spec/v2.0.0.html) に準拠しています。

## [Unreleased]

## [0.1.0] - 2026-01-24

### ✨ Added

- **気象パネル**
    - 天気予報（24-48時間の時間別）、気温、降水量、風速、体感温度
    - 雨雲レーダー画像（現在 + 1時間予報）
    - 暑さ指数（WBGT）表示（5段階フェイスアイコン）
    - 降水量オーバーレイ
    - 日没時間の表示
    - 服装指数の表示
- **センサーデータ可視化**
    - 複数部屋のセンサーデータ（温度、湿度、CO2、照度）
    - 電力消費監視グラフ
    - エアコン稼働状況の表示
- **メトリクスダッシュボード**
    - パフォーマンス推移グラフ（箱ひげ図）
    - パネル別日別推移グラフ（ドラッグズーム対応）
    - 異常検知表示のソート機能
    - 期間選択 UI と非同期読み込み
    - 各セクションのローディングスピナー
- **インフラ**
    - Docker / Kubernetes 対応
    - Liveness Probe 監視（healthz.py）
    - GitLab CI/CD パイプライン
    - GitHub Actions テストワークフロー
    - ty / pyright / mypy 型チェッカー対応
- **Web UI**
    - React フロントエンド（TypeScript + Vite）
    - 画像表示（ズーム・パン対応）
    - ポート指定オプションとシグナルハンドリング
    - 環境変数 `RECORD_VIDEO=true` でビデオ録画
- **エラー通知**
    - Selenium エラー時にページソースも Slack に投稿
    - エラー時にスクリーンショットを Slack に投稿
- **dataclass ベースの設定クラス（frozen）**

### 🔄 Changed

- フロントエンドのディレクトリ構成をベストプラクティスに準拠（`react/` → `frontend/`）
- Bootstrap → Tailwind CSS, Font Awesome → Heroicons に移行
- 異常検出を IsolationForest から IQR ベースに変更
- rain_cloud で undetected-chromedriver を使用しないように変更
- src/ のインポートスタイルを完全修飾名に統一
- TypedDict を dataclass に変更して型安全性を向上
- SQL クエリをパラメータ化クエリに変更
- Graceful shutdown 処理を os.\_exit() から sys.exit() に変更
- Visionect ディスプレイから Raspberry Pi ベースのシステムに移行
- InfluxDB2 に移行

### 🐛 Fixed

- my_lib API の変更に対応
- chartjs-plugin-zoom の読み込みと初期化順序を修正
- ドラッグズーム機能とパネル別処理時間グラフを修正
- メトリクスダッシュボードのデバッグ機能とエラーハンドリング
- SSH 統合テストで認証完了まで待機するよう修正
- Chrome ドライバー使用後のゾンビプロセス生成問題を修正
- SIGCHLD ハンドラを追加してゾンビプロセスの自動回収を実装
- 並列実行時の Selenium セッション管理を改善
- pyright / ty type checker のエラーを修正

### ⚡ Performance

- メトリクス分析のバックエンド最適化
- power_graph.py にフォントキャッシュを実装
- 画像変換処理の最適化
- サブプロット一括生成による描画処理の最適化
- フォント読み込みに LRU キャッシュを導入
- fetch_data_parallel を使ってセンサーグラフを大幅高速化
- 画像生成を並列実行（multiprocessing.Pool）
- 雨雲画像の並列生成
- 最適なウィンドウサイズをキャッシュして雨雲画像の取得を高速化

[Unreleased]: https://github.com/kimata/eink-weather-panel/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/kimata/eink-weather-panel/commits/v0.1.0
