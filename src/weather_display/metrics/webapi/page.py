#!/usr/bin/env python3

import json
import logging
import pathlib

import flask
import my_lib.config
import my_lib.flask_util
import my_lib.webapp.config

import weather_display.metrics.collector

from . import page_js

blueprint = flask.Blueprint(
    "metrics",
    __name__,
    url_prefix=my_lib.webapp.config.URL_PREFIX,
    static_folder="static",
    static_url_path="/static",
)


@blueprint.route("/api/metrics", methods=["GET"])
@my_lib.flask_util.gzipped
def metrics_view():
    """メトリクスダッシュボードのHTMLページを返す（データなし）"""
    # HTMLを生成（データは含まない）
    html_content = generate_metrics_html_skeleton()
    return flask.Response(html_content, mimetype="text/html")


@blueprint.route("/api/metrics/data", methods=["GET"])
@my_lib.flask_util.gzipped
def metrics_data():
    """メトリクスデータをJSONで返す（非推奨：個別エンドポイントを使用）"""
    # NOTE: メトリクスデータは3分間キャッシュする（パフォーマンス改善）
    flask.g.cache_max_age = 180

    try:
        # 設定ファイルからデータベースパスを取得
        config_file = flask.current_app.config.get("CONFIG_FILE_NORMAL", "config.yaml")
        config = my_lib.config.load(config_file, pathlib.Path("config.schema"))

        # 設定からデータベースパスを取得
        db_path = config.get("metrics", {}).get("data", "data/metrics.db")

        # データベースファイルの存在確認
        if not pathlib.Path(db_path).exists():
            return flask.jsonify(
                {
                    "error": "database_not_found",
                    "message": f"メトリクスデータベースが見つかりません: {db_path}",
                    "details": "システムが十分に動作してからメトリクスが生成されます。",
                }
            ), 503

        # メトリクス分析器を初期化
        analyzer = weather_display.metrics.collector.MetricsAnalyzer(db_path)

        # データ範囲を取得
        data_range = analyzer.get_data_range()

        # すべてのメトリクスデータを収集（全期間）
        basic_stats = analyzer.get_basic_statistics()
        hourly_patterns = analyzer.get_hourly_patterns()
        anomalies = analyzer.detect_anomalies()
        trends = analyzer.get_performance_trends()
        alerts = analyzer.check_performance_alerts()
        panel_trends = analyzer.get_panel_performance_trends()
        performance_stats = analyzer.get_performance_statistics()

        # JSONレスポンスを返す
        return flask.jsonify(
            {
                "data_range": data_range,
                "basic_stats": basic_stats,
                "hourly_patterns": hourly_patterns,
                "anomalies": anomalies,
                "trends": trends,
                "alerts": alerts,
                "panel_trends": panel_trends,
                "performance_stats": performance_stats,
            }
        )

    except Exception as e:
        logging.exception("メトリクスデータ取得エラー")
        return flask.jsonify({"error": "internal_error", "message": str(e)}), 500


def _get_analyzer():
    """メトリクス分析器を初期化する共通関数"""
    config_file = flask.current_app.config.get("CONFIG_FILE_NORMAL", "config.yaml")
    config = my_lib.config.load(config_file, pathlib.Path("config.schema"))
    db_path = config.get("metrics", {}).get("data", "data/metrics.db")

    if not pathlib.Path(db_path).exists():
        return (
            None,
            flask.jsonify(
                {
                    "error": "database_not_found",
                    "message": f"メトリクスデータベースが見つかりません: {db_path}",
                    "details": "システムが十分に動作してからメトリクスが生成されます。",
                }
            ),
            503,
        )

    return weather_display.metrics.collector.MetricsAnalyzer(db_path), None, None


@blueprint.route("/api/metrics/basic-stats", methods=["GET"])
@my_lib.flask_util.gzipped
def metrics_basic_stats():
    """基本統計データをJSONで返す"""
    flask.g.cache_max_age = 180

    try:
        analyzer, error_response, error_code = _get_analyzer()
        if analyzer is None:
            return error_response, error_code

        basic_stats = analyzer.get_basic_statistics()
        return flask.jsonify({"basic_stats": basic_stats})

    except Exception as e:
        logging.exception("基本統計データ取得エラー")
        return flask.jsonify({"error": "internal_error", "message": str(e)}), 500


@blueprint.route("/api/metrics/hourly-patterns", methods=["GET"])
@my_lib.flask_util.gzipped
def metrics_hourly_patterns():
    """時間別パターンデータをJSONで返す"""
    flask.g.cache_max_age = 180

    try:
        analyzer, error_response, error_code = _get_analyzer()
        if analyzer is None:
            return error_response, error_code

        hourly_patterns = analyzer.get_hourly_patterns()
        return flask.jsonify({"hourly_patterns": hourly_patterns})

    except Exception as e:
        logging.exception("時間別パターンデータ取得エラー")
        return flask.jsonify({"error": "internal_error", "message": str(e)}), 500


@blueprint.route("/api/metrics/trends", methods=["GET"])
@my_lib.flask_util.gzipped
def metrics_trends():
    """パフォーマンス推移データをJSONで返す"""
    flask.g.cache_max_age = 180

    try:
        analyzer, error_response, error_code = _get_analyzer()
        if analyzer is None:
            return error_response, error_code

        trends = analyzer.get_performance_trends()
        return flask.jsonify({"trends": trends})

    except Exception as e:
        logging.exception("パフォーマンス推移データ取得エラー")
        return flask.jsonify({"error": "internal_error", "message": str(e)}), 500


@blueprint.route("/api/metrics/panel-trends", methods=["GET"])
@my_lib.flask_util.gzipped
def metrics_panel_trends():
    """パネル別処理時間推移データをJSONで返す"""
    flask.g.cache_max_age = 180

    try:
        analyzer, error_response, error_code = _get_analyzer()
        if analyzer is None:
            return error_response, error_code

        panel_trends = analyzer.get_panel_performance_trends()
        return flask.jsonify({"panel_trends": panel_trends})

    except Exception as e:
        logging.exception("パネル別処理時間推移データ取得エラー")
        return flask.jsonify({"error": "internal_error", "message": str(e)}), 500


@blueprint.route("/api/metrics/alerts", methods=["GET"])
@my_lib.flask_util.gzipped
def metrics_alerts():
    """アラートデータをJSONで返す"""
    flask.g.cache_max_age = 180

    try:
        analyzer, error_response, error_code = _get_analyzer()
        if analyzer is None:
            return error_response, error_code

        alerts = analyzer.check_performance_alerts()
        return flask.jsonify({"alerts": alerts})

    except Exception as e:
        logging.exception("アラートデータ取得エラー")
        return flask.jsonify({"error": "internal_error", "message": str(e)}), 500


@blueprint.route("/api/metrics/anomalies", methods=["GET"])
@my_lib.flask_util.gzipped
def metrics_anomalies():
    """異常検知データをJSONで返す"""
    flask.g.cache_max_age = 180

    try:
        analyzer, error_response, error_code = _get_analyzer()
        if analyzer is None:
            return error_response, error_code

        anomalies = analyzer.detect_anomalies()
        performance_stats = analyzer.get_performance_statistics()
        data_range = analyzer.get_data_range()
        return flask.jsonify(
            {"anomalies": anomalies, "performance_stats": performance_stats, "data_range": data_range}
        )

    except Exception as e:
        logging.exception("異常検知データ取得エラー")
        return flask.jsonify({"error": "internal_error", "message": str(e)}), 500


@blueprint.route("/static/<path:filename>", methods=["GET"])
def static_files(filename):
    """静的ファイル（JS/CSS）を提供する"""
    try:
        static_path = pathlib.Path(__file__).parent / "static" / filename
        if static_path.exists() and static_path.is_file():
            return flask.send_file(
                static_path,
                mimetype="application/javascript" if filename.endswith(".js") else "text/css",
                as_attachment=False,
                max_age=3600,  # 1時間キャッシュ
            )
        else:
            return flask.Response("File not found", status=404)
    except Exception:
        logging.exception("静的ファイル取得エラー")
        return flask.Response("", status=500)


@blueprint.route("/favicon.png", methods=["GET"])
def favicon():
    """react/public/favicon.pngを返す"""
    try:
        # プロジェクトルートからの相対パスでfavicon.pngを取得
        favicon_path = (
            pathlib.Path(__file__).parent.parent.parent.parent.parent / "react" / "public" / "favicon.png"
        )

        if favicon_path.exists():
            return flask.send_file(
                favicon_path,
                mimetype="image/png",
                as_attachment=False,
                max_age=3600,  # 1時間キャッシュ
            )
        else:
            # ファイルが見つからない場合は404を返す
            return flask.Response("Favicon not found", status=404)
    except Exception:
        logging.exception("favicon取得エラー")
        return flask.Response("", status=500)


def generate_metrics_html_skeleton():
    """データを含まない軽量なHTMLスケルトンを生成。"""
    # URL_PREFIXを取得してfaviconパスを構築
    favicon_path = f"{my_lib.webapp.config.URL_PREFIX}/favicon.png"

    return f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>天気パネル メトリクス ダッシュボード</title>
    <link rel="icon" type="image/png" href="{favicon_path}">
    <link rel="apple-touch-icon" href="{favicon_path}">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bulma@0.9.4/css/bulma.min.css">
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/@sgratzl/chartjs-chart-boxplot"></script>
    <script defer src="{my_lib.webapp.config.URL_PREFIX}/static/metrics.js"></script>
    <script defer src="{my_lib.webapp.config.URL_PREFIX}/static/chart-functions.js"></script>
    <script defer src="{my_lib.webapp.config.URL_PREFIX}/static/metrics-loader.js"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        .metrics-card {{ margin-bottom: 1rem; position: relative; }}
        @media (max-width: 768px) {{
            .metrics-card {{ margin-bottom: 0.75rem; }}
        }}
        .stat-number {{ font-size: 2rem; font-weight: bold; }}
        .chart-container {{ position: relative; height: 350px; margin: 0.5rem 0; }}
        @media (max-width: 768px) {{
            .chart-container {{ height: 300px; margin: 0.25rem 0; }}
            .container.is-fluid {{ padding: 0.25rem !important; }}
            .section {{ padding: 0.5rem 0.25rem !important; }}
            .card {{ margin-bottom: 1rem !important; }}
            .columns {{ margin: 0 !important; }}
            .column {{ padding: 0.25rem !important; }}
        }}
        .chart-legend {{ margin-bottom: 1rem; }}
        .legend-item {{ display: inline-block; margin-right: 1rem; margin-bottom: 0.5rem; }}
        .legend-color {{
            display: inline-block; width: 20px; height: 3px;
            margin-right: 0.5rem; vertical-align: middle;
        }}
        .legend-dashed {{ border-top: 3px dashed; height: 0; }}
        .legend-dotted {{ border-top: 3px dotted; height: 0; }}
        .anomaly-item {{
            margin-bottom: 1rem;
            padding: 0.75rem;
            background-color: #fafafa;
            border-radius: 6px;
            border-left: 4px solid #ffdd57;
        }}
        .alert-item {{ margin-bottom: 1rem; }}
        .hourly-grid {{
            display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 1rem;
        }}
        .japanese-font {{
            font-family: "Hiragino Sans", "Hiragino Kaku Gothic ProN",
                         "Noto Sans CJK JP", "Yu Gothic", sans-serif;
        }}

        /* ローディング表示 */
        .loading-overlay {{
            position: static;
            background: rgba(255, 255, 255, 0.9);
            display: flex;
            align-items: center;
            justify-content: center;
            border-radius: 6px;
            padding: 2rem;
            width: 100%;
            height: 100%;
        }}
        .loading-spinner {{
            display: inline-block;
            border: 2px solid #f3f3f3;
            border-top: 2px solid #3273dc;
            border-radius: 50%;
            width: 1.2em;
            height: 1.2em;
            animation: spin 1s linear infinite;
        }}
        @keyframes spin {{
            0% {{ transform: rotate(0deg); }}
            100% {{ transform: rotate(360deg); }}
        }}
        .loading-text {{
            margin-left: 1rem;
            font-weight: 500;
            color: #3273dc;
        }}

        /* パーマリンク機能のスタイル */
        .permalink-container {{
            position: relative;
            display: inline-block;
        }}
        .permalink-icon {{
            position: absolute;
            right: -25px;
            top: 50%;
            transform: translateY(-50%);
            opacity: 0;
            transition: opacity 0.2s ease;
            cursor: pointer;
            color: #3273dc;
            font-size: 0.8em;
        }}
        .permalink-container:hover .permalink-icon {{
            opacity: 1;
        }}
        .permalink-icon:hover {{
            color: #2366d1;
        }}

        /* カード用パーマリンク */
        .card-permalink {{
            position: absolute;
            top: 10px;
            right: 10px;
            opacity: 0;
            transition: opacity 0.2s ease;
            cursor: pointer;
            color: #3273dc;
            font-size: 0.9em;
            z-index: 10;
        }}
        .card:hover .card-permalink {{
            opacity: 1;
        }}
        .card-permalink:hover {{
            color: #2366d1;
        }}

        /* セクション用パーマリンク調整 */
        .section-header {{
            position: relative;
            padding-right: 30px;
        }}

        /* コピー成功通知 */
        .copy-notification {{
            position: fixed;
            top: 20px;
            right: 20px;
            background: #48c774;
            color: white;
            padding: 0.75rem 1rem;
            border-radius: 4px;
            opacity: 0;
            transform: translateY(-20px);
            transition: all 0.3s ease;
            z-index: 1000;
        }}
        .copy-notification.show {{
            opacity: 1;
            transform: translateY(0);
        }}

        /* エラー表示 */
        .error-message {{
            padding: 2rem;
            text-align: center;
            color: #721c24;
            background-color: #f8d7da;
            border: 1px solid #f5c6cb;
            border-radius: 6px;
            margin: 1rem;
        }}

        /* レイアウト安定化 - 各セクションに最小高さを設定 */
        #alerts-container {{
            min-height: 60px;
            position: relative;
            box-sizing: border-box;
        }}
        #basic-stats-container {{
            min-height: 400px;
            position: relative;
            box-sizing: border-box;
        }}
        #hourly-patterns-container {{
            min-height: 800px;
            position: relative;
            box-sizing: border-box;
        }}
        #diff-sec-container {{
            min-height: 400px;
            position: relative;
            box-sizing: border-box;
        }}
        #trends-container {{
            min-height: 600px;
            position: relative;
            box-sizing: border-box;
        }}
        #panel-trends-container {{
            min-height: 800px;
            position: relative;
            box-sizing: border-box;
        }}
        #anomalies-container {{
            min-height: 500px;
            position: relative;
            box-sizing: border-box;
        }}

        /* レイアウトシフト防止 - コンテンツ更新時のスムーズな変更 */
        .metrics-container > div {{
            transition: all 0.3s ease-in-out;
        }}

        /* ローディング時の高さ確保 */
        .loading-placeholder {{
            width: 100%;
            height: 100%;
            display: flex;
            align-items: center;
            justify-content: center;
            box-sizing: border-box;
        }}
    </style>
</head>
<body class="japanese-font">
    <div class="container is-fluid" style="padding: 0.5rem;">
        <section class="section" style="padding: 1rem 0.5rem;">
            <div class="container" style="max-width: 100%; padding: 0;">
                <h1 class="title is-2 has-text-centered" id="dashboard">
                    <div class="permalink-container">
                        <span class="icon is-large"><i class="fas fa-chart-line"></i></span>
                        天気パネル メトリクス ダッシュボード
                        <i class="fas fa-link permalink-icon" onclick="copyPermalink('dashboard')"></i>
                    </div>
                </h1>
                <p class="subtitle has-text-centered" id="subtitle">パフォーマンス監視と異常検知</p>

                <!-- 統一進捗表示エリア（右下フローティング） -->
                <div id="progress-display" style="
                    position: fixed; bottom: 20px; right: 20px;
                    background: rgba(255, 255, 255, 0.95);
                    padding: 1rem 1.5rem; border-radius: 8px;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                    z-index: 1000; display: flex; align-items: center;">
                    <span class="loading-spinner" style="margin-right: 0.5rem;"></span>
                    <span id="progress-text" style="font-size: 0.9rem; color: #363636;">
                        メトリクスデータを取得中...
                    </span>
                </div>

                <!-- 初期ローディング表示（非表示） -->
                <div id="initial-loading" style="display: none;"></div>

                <!-- エラー表示エリア -->
                <div id="error-container" style="display: none;"></div>

                <!-- コンテンツコンテナ（初期状態では非表示） -->
                <div id="metrics-content" style="display: none;">
                    <!-- アラート -->
                    <div id="alerts-container"></div>

                    <!-- 基本統計 -->
                    <div id="basic-stats-container"></div>

                    <!-- 時間別パターン -->
                    <div id="hourly-patterns-container"></div>

                    <!-- 表示タイミング -->
                    <div id="diff-sec-container"></div>

                    <!-- パフォーマンス推移 -->
                    <div id="trends-container"></div>

                    <!-- パネル別処理時間推移 -->
                    <div id="panel-trends-container"></div>

                    <!-- 異常検知 -->
                    <div id="anomalies-container"></div>
                </div>
            </div>
        </section>
    </div>

    <script>
        // API URLの設定
        window.metricsApiUrl = '{my_lib.webapp.config.URL_PREFIX}/api/metrics/data';
        window.metricsApiBaseUrl = '{my_lib.webapp.config.URL_PREFIX}';
    </script>
</html>
    """


def generate_metrics_html(  # noqa: PLR0913
    basic_stats, hourly_patterns, anomalies, trends, alerts, panel_trends, performance_stats, data_range
):
    """Bulma CSSを使用した包括的なメトリクスHTMLを生成。"""
    # データ範囲から動的なタイトルを生成
    import datetime

    subtitle_text = "パフォーマンス監視と異常検知"
    if data_range and data_range["overall"]["earliest"]:
        try:
            earliest_str = data_range["overall"]["earliest"]
            # ISO形式の日時をパース
            earliest_dt = datetime.datetime.fromisoformat(earliest_str.replace("+09:00", "+09:00"))
            latest_str = data_range["overall"]["latest"]
            latest_dt = datetime.datetime.fromisoformat(latest_str.replace("+09:00", "+09:00"))

            # 日数を計算
            days_diff = (latest_dt - earliest_dt).days + 1  # +1 to include both start and end days

            # 開始日をフォーマット
            start_date_formatted = earliest_dt.strftime("%Y年%m月%d日")

            subtitle_text = f"過去{days_diff}日間（{start_date_formatted}〜）のパフォーマンス監視と異常検知"
        except Exception:
            # フォーマットエラーの場合はデフォルトのまま
            subtitle_text = "パフォーマンス監視と異常検知"

    # JavaScript チャート用にデータをJSONに変換
    hourly_data_json = json.dumps(hourly_patterns)
    trends_data_json = json.dumps(trends)
    anomalies_data_json = json.dumps(anomalies)
    panel_trends_data_json = json.dumps(panel_trends)

    # URL_PREFIXを取得してfaviconパスを構築
    favicon_path = f"{my_lib.webapp.config.URL_PREFIX}/favicon.png"

    html = (
        f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>天気パネル メトリクス ダッシュボード</title>
    <link rel="icon" type="image/png" href="{favicon_path}">
    <link rel="apple-touch-icon" href="{favicon_path}">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bulma@0.9.4/css/bulma.min.css">
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/@sgratzl/chartjs-chart-boxplot"></script>
    <script defer src="{my_lib.webapp.config.URL_PREFIX}/static/metrics.js"></script>
    <script defer src="{my_lib.webapp.config.URL_PREFIX}/static/chart-functions.js"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        .metrics-card {{ margin-bottom: 1rem; }}
        @media (max-width: 768px) {{
            .metrics-card {{ margin-bottom: 0.75rem; }}
        }}
        .stat-number {{ font-size: 2rem; font-weight: bold; }}
        .chart-container {{ position: relative; height: 350px; margin: 0.5rem 0; }}
        @media (max-width: 768px) {{
            .chart-container {{ height: 300px; margin: 0.25rem 0; }}
            .container.is-fluid {{ padding: 0.25rem !important; }}
            .section {{ padding: 0.5rem 0.25rem !important; }}
            .card {{ margin-bottom: 1rem !important; }}
            .columns {{ margin: 0 !important; }}
            .column {{ padding: 0.25rem !important; }}
        }}
        .chart-legend {{ margin-bottom: 1rem; }}
        .legend-item {{ display: inline-block; margin-right: 1rem; margin-bottom: 0.5rem; }}
        .legend-color {{
            display: inline-block; width: 20px; height: 3px;
            margin-right: 0.5rem; vertical-align: middle;
        }}
        .legend-dashed {{ border-top: 3px dashed; height: 0; }}
        .legend-dotted {{ border-top: 3px dotted; height: 0; }}
        .anomaly-item {{
            margin-bottom: 1rem;
            padding: 0.75rem;
            background-color: #fafafa;
            border-radius: 6px;
            border-left: 4px solid #ffdd57;
        }}
        .alert-item {{ margin-bottom: 1rem; }}
        .hourly-grid {{
            display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 1rem;
        }}
        .japanese-font {{
            font-family: "Hiragino Sans", "Hiragino Kaku Gothic ProN",
                         "Noto Sans CJK JP", "Yu Gothic", sans-serif;
        }}

        /* パーマリンク機能のスタイル */
        .permalink-container {{
            position: relative;
            display: inline-block;
        }}
        .permalink-icon {{
            position: absolute;
            right: -25px;
            top: 50%;
            transform: translateY(-50%);
            opacity: 0;
            transition: opacity 0.2s ease;
            cursor: pointer;
            color: #3273dc;
            font-size: 0.8em;
        }}
        .permalink-container:hover .permalink-icon {{
            opacity: 1;
        }}
        .permalink-icon:hover {{
            color: #2366d1;
        }}

        /* カード用パーマリンク */
        .card-permalink {{
            position: absolute;
            top: 10px;
            right: 10px;
            opacity: 0;
            transition: opacity 0.2s ease;
            cursor: pointer;
            color: #3273dc;
            font-size: 0.9em;
            z-index: 10;
        }}
        .card:hover .card-permalink {{
            opacity: 1;
        }}
        .card-permalink:hover {{
            color: #2366d1;
        }}

        /* セクション用パーマリンク調整 */
        .section-header {{
            position: relative;
            padding-right: 30px;
        }}

        /* コピー成功通知 */
        .copy-notification {{
            position: fixed;
            top: 20px;
            right: 20px;
            background: #48c774;
            color: white;
            padding: 0.75rem 1rem;
            border-radius: 4px;
            opacity: 0;
            transform: translateY(-20px);
            transition: all 0.3s ease;
            z-index: 1000;
        }}
        .copy-notification.show {{
            opacity: 1;
            transform: translateY(0);
        }}
    </style>
</head>
<body class="japanese-font">
    <div class="container is-fluid" style="padding: 0.5rem;">
        <section class="section" style="padding: 1rem 0.5rem;">
            <div class="container" style="max-width: 100%; padding: 0;">
                <h1 class="title is-2 has-text-centered" id="dashboard">
                    <div class="permalink-container">
                        <span class="icon is-large"><i class="fas fa-chart-line"></i></span>
                        天気パネル メトリクス ダッシュボード
                        <i class="fas fa-link permalink-icon" onclick="copyPermalink('dashboard')"></i>
                    </div>
                </h1>
                <p class="subtitle has-text-centered">{subtitle_text}</p>

                <!-- アラート -->
                {generate_alerts_section(alerts)}

                <!-- 基本統計 -->
                {generate_basic_stats_section(basic_stats)}

                <!-- 時間別パターン -->
                {generate_hourly_patterns_section(hourly_patterns)}

                <!-- 表示タイミング -->
                {generate_diff_sec_section()}

                <!-- パフォーマンス推移 -->
                {generate_trends_section(trends)}

                <!-- パネル別処理時間推移 -->
                {generate_panel_trends_section(panel_trends)}

                <!-- 異常検知 -->
                {generate_anomalies_section(anomalies, performance_stats)}
            </div>
        </section>
    </div>

    <script>
        // データをグローバル変数として設定
        window.hourlyData = """
        + hourly_data_json
        + """;
        window.trendsData = """
        + trends_data_json
        + """;
        window.anomaliesData = """
        + anomalies_data_json
        + """;
        window.panelTrendsData = """
        + panel_trends_data_json
        + """;

        // チャート生成（外部JSファイルで実装）
        document.addEventListener('DOMContentLoaded', function() {
            generateHourlyCharts();
            generateDiffSecCharts();
            generateBoxplotCharts();
            generateTrendsCharts();
            generatePanelTrendsCharts();
            generatePanelTimeSeriesChart();
        });

        """
        + page_js.generate_chart_javascript()
        + """
    </script>
</html>
    """
    )

    return html  # noqa: RET504


def generate_alerts_section(alerts):
    """アラートセクションのHTML生成。"""
    if not alerts:
        return """
        <div class="notification is-success" id="alerts">
            <span class="icon"><i class="fas fa-check-circle"></i></span>
            パフォーマンスアラートは検出されていません。
        </div>
        """

    alerts_html = (
        '<div class="section" id="alerts"><h2 class="title is-4 section-header">'
        '<div class="permalink-container">'
        '<span class="icon"><i class="fas fa-exclamation-triangle"></i></span> '
        "パフォーマンスアラート"
        '<i class="fas fa-link permalink-icon" onclick="copyPermalink(\'alerts\')"></i>'
        "</div></h2>"
    )

    for alert in alerts:
        severity_class = {"critical": "is-danger", "warning": "is-warning", "info": "is-info"}.get(
            alert.get("severity", "info"), "is-info"
        )

        alert_type = alert.get("type", "アラート").replace("_", " ")
        alert_message = alert.get("message", "メッセージなし")

        alerts_html += f"""
        <div class="notification {severity_class} alert-item">
            <strong>{alert_type}:</strong> {alert_message}
        </div>
        """

    alerts_html += "</div>"
    return alerts_html


def generate_basic_stats_section(basic_stats):
    """基本統計セクションのHTML生成。"""
    draw_panel = basic_stats.get("draw_panel", {})
    display_image = basic_stats.get("display_image", {})

    return f"""
    <div class="section" id="basic-stats">
        <h2 class="title is-4 section-header">
            <div class="permalink-container">
                <span class="icon"><i class="fas fa-chart-bar"></i></span>
                基本統計
                <i class="fas fa-link permalink-icon" onclick="copyPermalink('basic-stats')"></i>
            </div>
        </h2>

        <div class="columns">
            <div class="column">
                <div class="card metrics-card" id="draw-panel-stats">
                    <i class="fas fa-link card-permalink" onclick="copyPermalink('draw-panel-stats')"></i>
                    <div class="card-header">
                        <p class="card-header-title">画像生成処理</p>
                    </div>
                    <div class="card-content">
                        <div class="columns is-multiline">
                            <div class="column is-half">
                                <div class="has-text-centered">
                                    <p class="heading">総実行回数</p>
                                    <p class="stat-number has-text-primary">
                                    {draw_panel.get("total_operations", 0):,}
                                </p>
                                </div>
                            </div>
                            <div class="column is-half">
                                <div class="has-text-centered">
                                    <p class="heading">エラー回数</p>
                                    <p class="stat-number has-text-danger">
                                    {draw_panel.get("error_count", 0):,}
                                </p>
                                </div>
                            </div>
                            <div class="column is-half">
                                <div class="has-text-centered">
                                    <p class="heading">平均処理時間（秒）</p>
                                    <p class="stat-number has-text-info">
                                    {draw_panel.get("avg_elapsed_time", 0):.2f}
                                </p>
                                </div>
                            </div>
                            <div class="column is-half">
                                <div class="has-text-centered">
                                    <p class="heading">最大処理時間（秒）</p>
                                    <p class="stat-number has-text-warning">
                                    {draw_panel.get("max_elapsed_time", 0):.2f}
                                </p>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <div class="column">
                <div class="card metrics-card" id="display-image-stats">
                    <i class="fas fa-link card-permalink" onclick="copyPermalink('display-image-stats')"></i>
                    <div class="card-header">
                        <p class="card-header-title">表示実行処理</p>
                    </div>
                    <div class="card-content">
                        <div class="columns is-multiline">
                            <div class="column is-half">
                                <div class="has-text-centered">
                                    <p class="heading">総実行回数</p>
                                    <p class="stat-number has-text-primary">
                                    {display_image.get("total_operations", 0):,}
                                </p>
                                </div>
                            </div>
                            <div class="column is-half">
                                <div class="has-text-centered">
                                    <p class="heading">失敗回数</p>
                                    <p class="stat-number has-text-danger">
                                    {display_image.get("failure_count", 0):,}
                                </p>
                                </div>
                            </div>
                            <div class="column is-half">
                                <div class="has-text-centered">
                                    <p class="heading">平均処理時間（秒）</p>
                                    <p class="stat-number has-text-info">
                                    {display_image.get("avg_elapsed_time", 0):.2f}
                                </p>
                                </div>
                            </div>
                            <div class="column is-half">
                                <div class="has-text-centered">
                                    <p class="heading">最大処理時間（秒）</p>
                                    <p class="stat-number has-text-warning">
                                    {display_image.get("max_elapsed_time", 0):.2f}
                                </p>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
    """


def generate_hourly_patterns_section(hourly_patterns):  # noqa: ARG001
    """時間別パターンセクションのHTML生成。"""
    return """
    <div class="section" id="hourly-patterns">
        <h2 class="title is-4 section-header">
            <div class="permalink-container">
                <span class="icon"><i class="fas fa-clock"></i></span>
                時間別パフォーマンスパターン
                <i class="fas fa-link permalink-icon" onclick="copyPermalink('hourly-patterns')"></i>
            </div>
        </h2>

        <div class="columns">
            <div class="column is-half">
                <div class="card metrics-card" id="draw-panel-hourly">
                    <i class="fas fa-link card-permalink" onclick="copyPermalink('draw-panel-hourly')"></i>
                    <div class="card-header">
                        <p class="card-header-title">画像生成処理 - 時間別パフォーマンス</p>
                    </div>
                    <div class="card-content">
                        <div class="chart-container">
                            <canvas id="drawPanelHourlyChart"></canvas>
                        </div>
                    </div>
                </div>
            </div>
            <div class="column is-half">
                <div class="card metrics-card" id="draw-panel-boxplot">
                    <i class="fas fa-link card-permalink" onclick="copyPermalink('draw-panel-boxplot')"></i>
                    <div class="card-header">
                        <p class="card-header-title">画像生成処理 - 時間別分布</p>
                    </div>
                    <div class="card-content">
                        <div class="chart-container">
                            <canvas id="drawPanelBoxplotChart"></canvas>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <div class="columns">
            <div class="column is-half">
                <div class="card metrics-card" id="display-image-hourly">
                    <i class="fas fa-link card-permalink" onclick="copyPermalink('display-image-hourly')"></i>
                    <div class="card-header">
                        <p class="card-header-title">表示実行処理 - 時間別パフォーマンス</p>
                    </div>
                    <div class="card-content">
                        <div class="chart-container">
                            <canvas id="displayImageHourlyChart"></canvas>
                        </div>
                    </div>
                </div>
            </div>
            <div class="column is-half">
                <div class="card metrics-card" id="display-image-box">
                    <i class="fas fa-link card-permalink" onclick="copyPermalink('display-image-box')"></i>
                    <div class="card-header">
                        <p class="card-header-title">表示実行処理 - 時間別分布</p>
                    </div>
                    <div class="card-content">
                        <div class="chart-container">
                            <canvas id="displayImageBoxplotChart"></canvas>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
    """


def generate_trends_section(trends):  # noqa: ARG001
    """パフォーマンス推移セクションのHTML生成。"""
    return """
    <div class="section" id="performance-trends">
        <h2 class="title is-4 section-header">
            <div class="permalink-container">
                <span class="icon"><i class="fas fa-chart-area"></i></span>
                パフォーマンス推移
                <i class="fas fa-link permalink-icon" onclick="copyPermalink('performance-trends')"></i>
            </div>
        </h2>
        <p class="subtitle is-6">平均処理時間の箱ヒゲ図（実行回数は非表示）</p>

        <div class="columns">
            <div class="column is-6">
                <div class="card metrics-card" id="draw-panel-trends">
                    <i class="fas fa-link card-permalink" onclick="copyPermalink('draw-panel-trends')"></i>
                    <div class="card-header">
                        <p class="card-header-title">画像生成処理 - 日別推移</p>
                    </div>
                    <div class="card-content">
                        <div class="chart-container">
                            <canvas id="drawPanelTrendsChart"></canvas>
                        </div>
                    </div>
                </div>
            </div>
            <div class="column is-6">
                <div class="card metrics-card" id="display-image-trends">
                    <i class="fas fa-link card-permalink" onclick="copyPermalink('display-image-trends')"></i>
                    <div class="card-header">
                        <p class="card-header-title">表示実行処理 - 日別推移</p>
                    </div>
                    <div class="card-content">
                        <div class="chart-container">
                            <canvas id="displayImageTrendsChart"></canvas>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <div class="columns">
            <div class="column is-6">
                <div class="card metrics-card" id="diff-sec-trends">
                    <i class="fas fa-link card-permalink" onclick="copyPermalink('diff-sec-trends')"></i>
                    <div class="card-header">
                        <p class="card-header-title">表示タイミング - 日別推移</p>
                    </div>
                    <div class="card-content">
                        <div class="chart-container">
                            <canvas id="diffSecTrendsChart"></canvas>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
    """


def generate_anomalies_section(anomalies, performance_stats):  # noqa: C901, PLR0912, PLR0915
    """異常検知セクションのHTML生成。"""
    draw_panel_anomalies = anomalies.get("draw_panel", {})
    display_image_anomalies = anomalies.get("display_image", {})

    # 異常の表示用フォーマット
    dp_anomaly_count = draw_panel_anomalies.get("anomalies_detected", 0)
    di_anomaly_count = display_image_anomalies.get("anomalies_detected", 0)
    dp_anomaly_rate = draw_panel_anomalies.get("anomaly_rate", 0) * 100
    di_anomaly_rate = display_image_anomalies.get("anomaly_rate", 0) * 100

    anomalies_html = f"""
    <div class="section" id="anomaly-detection">
        <h2 class="title is-4 section-header">
            <div class="permalink-container">
                <span class="icon"><i class="fas fa-search"></i></span> 異常検知
                <i class="fas fa-link permalink-icon" onclick="copyPermalink('anomaly-detection')"></i>
            </div>
        </h2>

        <div class="notification is-info is-light">
            <p><strong>異常検知について：</strong></p>
            <p>機械学習の<strong>Isolation Forest</strong>アルゴリズムを使用して、
               以下の要素から異常なパターンを検知しています：</p>
            <ul>
                <li><strong>処理時間</strong>：通常より極端に長い、または短い処理時間</li>
                <li><strong>エラー発生</strong>：エラーの有無も考慮要素</li>
            </ul>
            <p>例：異常に長い処理時間、エラーを伴う異常な処理時間など</p>
        </div>

        <div class="columns">
            <div class="column">
                <div class="card metrics-card" id="draw-panel-anomalies">
                    <i class="fas fa-link card-permalink" onclick="copyPermalink('draw-panel-anomalies')"></i>
                    <div class="card-header">
                        <p class="card-header-title">画像生成処理の異常</p>
                    </div>
                    <div class="card-content">
                        <div class="columns">
                            <div class="column has-text-centered">
                                <p class="heading">検出された異常数</p>
                                <p class="stat-number has-text-warning">{dp_anomaly_count}</p>
                            </div>
                            <div class="column has-text-centered">
                                <p class="heading">異常率</p>
                                <p class="stat-number has-text-warning">{dp_anomaly_rate:.2f}%</p>
                            </div>
                        </div>
    """

    # 個別の異常がある場合は表示
    if draw_panel_anomalies.get("anomalies"):
        anomalies_html += '<div class="content"><h5>最近の異常:</h5>'
        # 新しいもの順でソート
        sorted_anomalies = sorted(
            draw_panel_anomalies["anomalies"], key=lambda x: x.get("timestamp", ""), reverse=True
        )
        for anomaly in sorted_anomalies[:20]:  # 最新20件を表示
            timestamp_str = anomaly.get("timestamp", "不明")
            elapsed_time = anomaly.get("elapsed_time", 0)
            # hour = anomaly.get("hour", 0)  # unused
            error_code = anomaly.get("error_code", 0)

            # 異常の種類を分析（統計情報を使用）
            dp_stats = performance_stats.get("draw_panel", {})
            avg_time = dp_stats.get("avg_time", 0)
            std_time = dp_stats.get("std_time", 0)

            anomaly_reasons = []

            anomaly_details = []

            if elapsed_time > 60:  # 1分以上
                anomaly_reasons.append('<span class="tag is-small is-warning">長時間処理</span>')
                if std_time > 0:
                    sigma_deviation = (elapsed_time - avg_time) / std_time
                    sign = "+" if sigma_deviation >= 0 else ""
                    anomaly_details.append(f"平均値から<strong>{sign}{sigma_deviation:.1f}σ</strong>乖離")
                anomaly_details.append(f"実行時間: <strong>{elapsed_time:.2f}秒</strong>")
            elif elapsed_time < 1:  # 1秒未満
                anomaly_reasons.append('<span class="tag is-small is-info">短時間処理</span>')
                if std_time > 0:
                    sigma_deviation = (elapsed_time - avg_time) / std_time
                    sign = "+" if sigma_deviation >= 0 else ""
                    anomaly_details.append(f"平均値から<strong>{sign}{sigma_deviation:.1f}σ</strong>乖離")
                anomaly_details.append(f"実行時間: <strong>{elapsed_time:.2f}秒</strong>")

            if error_code > 0:
                anomaly_reasons.append('<span class="tag is-small is-danger">エラー発生</span>')
                anomaly_details.append(f"エラーコード: <strong>{error_code}</strong>")

            if not anomaly_reasons:
                anomaly_reasons.append('<span class="tag is-small is-light">パターン異常</span>')
                if std_time > 0:
                    sigma_deviation = (elapsed_time - avg_time) / std_time
                    sign = "+" if sigma_deviation >= 0 else ""
                    anomaly_details.append(f"平均値から<strong>{sign}{sigma_deviation:.1f}σ</strong>乖離")
                anomaly_details.append(f"実行時間: <strong>{elapsed_time:.2f}秒</strong>")

            # 日時を自然な日本語形式に変換
            try:
                import datetime

                if timestamp_str != "不明":
                    # ISO形式の日時をパース
                    dt = datetime.datetime.fromisoformat(timestamp_str.replace("+09:00", "+09:00"))
                    # 日本語形式に変換 (年も含める)
                    formatted_time = dt.strftime("%Y年%m月%d日 %H時%M分")

                    # 経過時間を計算
                    now = datetime.datetime.now(dt.tzinfo)
                    elapsed_delta = now - dt

                    if elapsed_delta.days > 0:
                        elapsed_text = f"{elapsed_delta.days}日前"
                    elif elapsed_delta.seconds // 3600 > 0:
                        hours = elapsed_delta.seconds // 3600
                        elapsed_text = f"{hours}時間前"
                    elif elapsed_delta.seconds // 60 > 0:
                        minutes = elapsed_delta.seconds // 60
                        elapsed_text = f"{minutes}分前"
                    else:
                        elapsed_text = "たった今"

                    formatted_time += f" ({elapsed_text})"
                else:
                    formatted_time = "不明"
            except Exception:
                formatted_time = timestamp_str

            reason_tags = " ".join(anomaly_reasons)
            detail_text = " | ".join(anomaly_details)
            anomalies_html += f"""<div class="anomaly-item">
                <div class="mb-2">
                    <span class="tag is-warning">{formatted_time}</span>
                    {reason_tags}
                </div>
                <div class="pl-3 has-text-grey-dark" style="font-size: 0.9rem;">
                    {detail_text}
                </div>
            </div>"""
        anomalies_html += "</div>"

    anomalies_html += f"""
                    </div>
                </div>
            </div>

            <div class="column">
                <div class="card metrics-card" id="display-anomalies">
                    <i class="fas fa-link card-permalink" onclick="copyPermalink('display-anomalies')"></i>
                    <div class="card-header">
                        <p class="card-header-title">表示実行処理の異常</p>
                    </div>
                    <div class="card-content">
                        <div class="columns">
                            <div class="column has-text-centered">
                                <p class="heading">検出された異常数</p>
                                <p class="stat-number has-text-warning">{di_anomaly_count}</p>
                            </div>
                            <div class="column has-text-centered">
                                <p class="heading">異常率</p>
                                <p class="stat-number has-text-warning">{di_anomaly_rate:.2f}%</p>
                            </div>
                        </div>
    """

    # 個別の異常がある場合は表示
    if display_image_anomalies.get("anomalies"):
        anomalies_html += '<div class="content"><h5>最近の異常:</h5>'
        # 新しいもの順でソート
        sorted_anomalies = sorted(
            display_image_anomalies["anomalies"], key=lambda x: x.get("timestamp", ""), reverse=True
        )
        for anomaly in sorted_anomalies[:20]:  # 最新20件を表示
            timestamp_str = anomaly.get("timestamp", "不明")
            elapsed_time = anomaly.get("elapsed_time", 0)
            # hour = anomaly.get("hour", 0)  # unused
            success = anomaly.get("success", True)

            # 異常の種類を分析（表示実行処理用、統計情報を使用）
            di_stats = performance_stats.get("display_image", {})
            avg_time_di = di_stats.get("avg_time", 0)
            std_time_di = di_stats.get("std_time", 0)

            anomaly_reasons = []

            anomaly_details = []

            if elapsed_time > 120:  # 2分以上
                anomaly_reasons.append('<span class="tag is-small is-warning">長時間処理</span>')
                if std_time_di > 0:
                    sigma_deviation = (elapsed_time - avg_time_di) / std_time_di
                    sign = "+" if sigma_deviation >= 0 else ""
                    anomaly_details.append(f"平均値から<strong>{sign}{sigma_deviation:.1f}σ</strong>乖離")
                anomaly_details.append(f"実行時間: <strong>{elapsed_time:.2f}秒</strong>")
            elif elapsed_time < 5:  # 5秒未満
                anomaly_reasons.append('<span class="tag is-small is-info">短時間処理</span>')
                if std_time_di > 0:
                    sigma_deviation = (elapsed_time - avg_time_di) / std_time_di
                    sign = "+" if sigma_deviation >= 0 else ""
                    anomaly_details.append(f"平均値から<strong>{sign}{sigma_deviation:.1f}σ</strong>乖離")
                anomaly_details.append(f"実行時間: <strong>{elapsed_time:.2f}秒</strong>")

            if not success:
                anomaly_reasons.append('<span class="tag is-small is-danger">実行失敗</span>')
                anomaly_details.append("実行結果: <strong>失敗</strong>")

            if not anomaly_reasons:
                anomaly_reasons.append('<span class="tag is-small is-light">パターン異常</span>')
                if std_time_di > 0:
                    sigma_deviation = (elapsed_time - avg_time_di) / std_time_di
                    sign = "+" if sigma_deviation >= 0 else ""
                    anomaly_details.append(f"平均値から<strong>{sign}{sigma_deviation:.1f}σ</strong>乖離")
                anomaly_details.append(f"実行時間: <strong>{elapsed_time:.2f}秒</strong>")

            # 日時を自然な日本語形式に変換
            try:
                import datetime

                if timestamp_str != "不明":
                    # ISO形式の日時をパース
                    dt = datetime.datetime.fromisoformat(timestamp_str.replace("+09:00", "+09:00"))
                    # 日本語形式に変換 (年も含める)
                    formatted_time = dt.strftime("%Y年%m月%d日 %H時%M分")

                    # 経過時間を計算
                    now = datetime.datetime.now(dt.tzinfo)
                    elapsed_delta = now - dt

                    if elapsed_delta.days > 0:
                        elapsed_text = f"{elapsed_delta.days}日前"
                    elif elapsed_delta.seconds // 3600 > 0:
                        hours = elapsed_delta.seconds // 3600
                        elapsed_text = f"{hours}時間前"
                    elif elapsed_delta.seconds // 60 > 0:
                        minutes = elapsed_delta.seconds // 60
                        elapsed_text = f"{minutes}分前"
                    else:
                        elapsed_text = "たった今"

                    formatted_time += f" ({elapsed_text})"
                else:
                    formatted_time = "不明"
            except Exception:
                formatted_time = timestamp_str

            reason_tags = " ".join(anomaly_reasons)
            detail_text = " | ".join(anomaly_details)
            anomalies_html += f"""<div class="anomaly-item">
                <div class="mb-2">
                    <span class="tag is-warning">{formatted_time}</span>
                    {reason_tags}
                </div>
                <div class="pl-3 has-text-grey-dark" style="font-size: 0.9rem;">
                    {detail_text}
                </div>
            </div>"""
        anomalies_html += "</div>"

    anomalies_html += """
                    </div>
                </div>
            </div>
        </div>
    </div>
    """

    return anomalies_html


def generate_diff_sec_section():
    """表示タイミングセクションのHTML生成。"""
    return """
    <div class="section" id="display-timing">
        <h2 class="title is-4 section-header">
            <div class="permalink-container">
                <span class="icon"><i class="fas fa-clock"></i></span> 表示タイミング
                <i class="fas fa-link permalink-icon" onclick="copyPermalink('display-timing')"></i>
            </div>
        </h2>
        <p class="subtitle is-6">表示実行時の分単位での秒数の偏差（0秒が理想的なタイミング）</p>

        <div class="columns">
            <div class="column is-half">
                <div class="card metrics-card" id="diff-sec-hourly">
                    <i class="fas fa-link card-permalink" onclick="copyPermalink('diff-sec-hourly')"></i>
                    <div class="card-header">
                        <p class="card-header-title">表示タイミング - 時間別パフォーマンス</p>
                    </div>
                    <div class="card-content">
                        <div class="chart-container">
                            <canvas id="diffSecHourlyChart"></canvas>
                        </div>
                    </div>
                </div>
            </div>
            <div class="column is-half">
                <div class="card metrics-card" id="diff-sec-boxplot">
                    <i class="fas fa-link card-permalink" onclick="copyPermalink('diff-sec-boxplot')"></i>
                    <div class="card-header">
                        <p class="card-header-title">表示タイミング - 時間別分布</p>
                    </div>
                    <div class="card-content">
                        <div class="chart-container">
                            <canvas id="diffSecBoxplotChart"></canvas>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
    """


def generate_panel_trends_section(panel_trends):  # noqa: ARG001
    """パネル別処理時間推移セクションのHTML生成。"""
    return """
    <div class="section" id="panel-trends">
        <h2 class="title is-4 section-header">
            <div class="permalink-container">
                <span class="icon"><i class="fas fa-puzzle-piece"></i></span>
                パネル別処理時間ヒストグラム
                <i class="fas fa-link permalink-icon" onclick="copyPermalink('panel-trends')"></i>
            </div>
        </h2>
        <p class="subtitle is-6">各パネルの処理時間分布をヒストグラムで表示（横軸：時間、縦軸：割合）</p>

        <div class="columns is-multiline is-variable is-1" id="panelTrendsContainer"
             style="justify-content: flex-start;">
            <!-- パネル別ヒストグラムがJavaScriptで動的に生成される -->
        </div>
    </div>

    <div class="section" id="panel-timeseries">
        <h2 class="title is-4 section-header">
            <div class="permalink-container">
                <span class="icon"><i class="fas fa-chart-line"></i></span>
                パネル別処理時間推移
                <i class="fas fa-link permalink-icon" onclick="copyPermalink('panel-timeseries')"></i>
            </div>
        </h2>
        <p class="subtitle is-6">各パネルの処理時間の時系列推移グラフ（時間軸での処理時間変化）</p>

        <div class="columns">
            <div class="column">
                <div class="card metrics-card" id="panel-time-series">
                    <i class="fas fa-link card-permalink" onclick="copyPermalink('panel-time-series')"></i>
                    <div class="card-header">
                        <p class="card-header-title">パネル別処理時間推移</p>
                    </div>
                    <div class="card-content">
                        <div class="chart-container">
                            <canvas id="panelTimeSeriesChart"></canvas>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
    """
