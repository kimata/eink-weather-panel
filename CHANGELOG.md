# Changelog

このプロジェクトの注目すべき変更点をすべてこのファイルに記載します。

このファイルのフォーマットは [Keep a Changelog](https://keepachangelog.com/ja/1.1.0/) に基づいており、
このプロジェクトは [Semantic Versioning](https://semver.org/spec/v2.0.0.html) に準拠しています。

## [Unreleased]

### 🐛 Fixed

- **表示・監視 (致命的)**
    - fbi の終了ステータスが常に 0 となり表示失敗を検知できなかった問題を修正（`; echo $?` の除去と判定順序の整理）
    - `execute()` が例外を握りつぶし、連続エラー時の Slack 通知・終了処理が永久に発火しなかった問題を修正（例外を再送出し `fail_count` を機能させる）
    - `-O`（1回のみ表示）モードで失敗しても終了コード 0 を返していた問題を修正
    - webui.py が my_lib の削除済み API（`URL_PREFIX`/`init()` 等）を参照し起動不能だった問題を修正（`build_environment()` ベースの新 API へ移行）
    - 想定外の終了コードで `sys.exit()` され、失敗が成功としてメトリクス記録されていた問題を修正（RuntimeError 化）
    - 表示失敗時に新規 SSH 接続がリークしていた問題を修正
    - healthz.py に `-S` オプションを追加し、小型ディスプレイモードで liveness probe が常時失敗する問題を修正
- **パネル**
    - WBGT 欠測（None）時に天気パネル全体がエラー画像になる問題を修正（体感温度へフォールバック）
    - 天気アイコン取得の `urlopen` にタイムアウトを追加（ハングで画像生成サイクル全体が停止する問題）
    - 天気アイコンの BGR/RGB チャンネル取り違えを修正（E-Ink 上の階調が意図とずれる問題）
    - 天気アイコンをパッケージディレクトリへ毎回ダンプ書き込みしていた問題を修正（書き込み自体を除去）
    - rain_fall: 2 回目の InfluxDB クエリの valid 未チェックによる IndexError を修正
    - power_graph: 最新値が 0 W のときの誤表示、全値 0 W のときの TypeError を修正
    - sensor_graph: lux データ全欠損時に「照明 ON」アイコンを誤表示する問題を修正
    - sensor_graph: matplotlib Locator の共有により目盛り・グリッドが消える問題を修正（サブプロットごとに生成）
    - rain_cloud: サブパネル失敗時に Chrome プロファイルを掴んだままリトライして衝突する問題を修正（`executor.shutdown` を finally で保証）
    - rain_cloud: タイル読み込み完了を待たずにスクリーンショットを撮っていた問題を修正（img 要素のロード完了待ちを追加）
- **Web UI / API**
    - サブプロセスのタイムアウト処理がデッドコードだった問題を修正（ハング時に terminate/kill が機能するように）
    - 生成トークンが生成中でも 60 秒で削除される問題を修正（生成完了後・300 秒で削除）
    - `/api/run` のエラー応答を HTTP 500 で返すように修正し、フロントエンドにエラー処理を追加（fetch 失敗時に永久に待ち続ける問題も修正）
    - werkzeug リローダー以外（gunicorn 等）で起動するとスレッドプールが初期化されない問題を修正
- **メトリクス**
    - 日別集計が SQLite の `DATE()` による UTC 変換で 9 時間ズレる問題を修正（`'+9 hours'` 修飾子で JST 補正）
    - ダッシュボードの「失敗回数」が常に 0 と表示される問題を修正（`error_count` フィールド名の不整合）
    - カスタム期間指定が「直近 N 日」にすり替わっていた問題を修正（start/end を SQL まで伝播）
    - メトリクス API が起動時の設定を無視して `config.yaml` を再ロードしていた問題を修正
- **表示・監視 (2026-07-11 追加調査分)**
    - SSH トランスポート死亡時に再接続を試みずプロセス終了する問題を修正（killall を新規接続で表示直前に実行する構造に変更、close はベストエフォート化）
    - エラーサイクル後に Pi 上の stale fbi プロセスが回収されない問題を修正（同上の構造変更で解消）
    - 失敗リトライ経路の `time.sleep(10)` が SIGTERM を無視する問題を修正（`should_terminate.wait()` 化）
    - `fail_count` 到達時の raise で `cleanup()` がスキップされる問題を修正（`try/finally` 化、`cleanup()` の `sys.exit(0)` を除去し異常終了コードを維持）
- **パネル (2026-07-11 追加調査分)**
    - WBGT・服装指数の取得例外（タイムアウト・HTTP エラー・パース失敗）で天気パネル全体がエラー画像になる問題を修正（欠測と同じ縮退にフォールバック）
    - rain_fall: 降雨開始時刻が取得できないと降水量表示ごと消える問題を修正（開始時刻の描画のみスキップ）
    - rain_cloud: WebUI の並列生成で固定 Chrome プロファイルを奪い合いプロファイル破損を招く問題を修正（PID サフィックス付き使い捨てプロファイル + 残存プロファイルの自動回収）
- **Web UI / API (2026-07-11 追加調査分)**
    - 完了済みトークンで `/api/log` を再取得すると応答が終端しない問題を修正（生成完了フラグでストリーム終端）
    - `_panel_data_map` の並行アクセスが無保護だった問題を修正（モジュールレベルのロックで保護、未使用の `PanelData.lock` を削除）
    - 生成タイムアウト・失敗時に空 PNG が 200 (image/png) で返る問題を修正（returncode 検査 + 空画像は 404 返却 + エラーをログキューに通知）
    - トークン有効期限が作成時刻基準でキュー滞留後に即失効し得る問題を修正（生成完了時刻基準に変更）
- **メトリクス (2026-07-11 追加調査分)**
    - メトリクス API 応答がブラウザに 24 時間キャッシュされる問題を修正（blueprint の `after_request` で `flask.g.cache_max_age` を尊重し 3 分キャッシュに）
    - ダッシュボードの Chart.js インスタンスが destroy されずメモリリークする問題を修正（`createOrReplaceChart()` ヘルパーで一元管理）
    - 期間ボタン連打で異なる期間のデータが同一画面に混在する問題を修正（読み込み処理の世代カウンタで古い実行を打ち切り）
    - create_image.py サブプロセスの初回接続時 WAL/SHM クリーンアップが親プロセス使用中のファイルを削除し得る問題を修正（my_lib に追加した `mark_cleanup_done()` API でサブプロセスのクリーンアップを抑止）
    - my_lib: `parse_wbgt_daily` で env.go.jp の実測値リストが短い場合に IndexError が発生する問題を修正（my-py-lib `83a1754` へ更新）
    - `server.py` 単体起動時に dict のまま設定を渡して全データ API が 500 になる問題を修正
- **インフラ (2026-07-11 追加調査分)**
    - k8s liveness probe の破損（存在しないパス・システム python3 依存・短すぎるタイムアウト）を修正（`uv run` 経由 + `timeoutSeconds: 30`、Deployment 名・イメージも実運用に整合）
    - GitHub Actions が存在しない `react/` を参照して CI が恒常的に失敗する問題を修正（`frontend/` に置換）

### 🗑️ Removed

- メトリクスダッシュボードのデッドコード（`generate_metrics_html` 系関数と `page_js.py`）を削除（実際の UI は skeleton + static/ 配下の JS）
- rain_fall.py の rain_cloud パネルからのコピペ残骸（未使用定数・誤った docstring）を削除

### 📝 Documentation

- ドキュメントの `react/` ディレクトリ参照を実体の `frontend/` に修正

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
