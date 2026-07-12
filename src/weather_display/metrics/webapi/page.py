#!/usr/bin/env python3
# ruff: noqa: E501

import datetime
import logging
import pathlib

import flask
import my_lib.config
import my_lib.flask_util
from flask_pydantic import validate

import weather_display.metrics.collector
import weather_display.metrics.webapi.schemas as schemas

# NOTE: URL prefix はアプリ側の register_blueprint(url_prefix=...) で指定する
blueprint = flask.Blueprint(
    "metrics",
    __name__,
    static_folder="static",
    static_url_path="/static",
)


@blueprint.after_request
def _apply_cache_max_age(response: flask.Response) -> flask.Response:
    # NOTE: my_lib.flask_util.gzipped は gzip 応答時に Cache-Control: max-age=86400 を
    # 無条件で設定する。毎分更新されるメトリクスが丸一日キャッシュされるのを防ぐため、
    # 各エンドポイントが flask.g.cache_max_age に設定した値でここで上書きする。
    # (blueprint の after_request は after_this_request のコールバックより後に実行される)
    max_age = flask.g.pop("cache_max_age", None)
    if max_age is not None:
        response.headers["Cache-Control"] = f"max-age={max_age}"
    return response


# Heroicons SVG definitions (outline style, 24x24)
_HEROICONS = {
    "chart-line": '<svg class="hero-icon" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path stroke-linecap="round" stroke-linejoin="round" d="M3.75 3v11.25A2.25 2.25 0 0 0 6 16.5h2.25M3.75 3h-1.5m1.5 0h16.5m0 0h1.5m-1.5 0v11.25A2.25 2.25 0 0 1 18 16.5h-2.25m-7.5 0h7.5m-7.5 0-1 3m8.5-3 1 3m0 0 .5 1.5m-.5-1.5h-9.5m0 0-.5 1.5M9 11.25v1.5M12 9v3.75m3-6v6" /></svg>',
    "link": '<svg class="hero-icon" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path stroke-linecap="round" stroke-linejoin="round" d="M13.19 8.688a4.5 4.5 0 0 1 1.242 7.244l-4.5 4.5a4.5 4.5 0 0 1-6.364-6.364l1.757-1.757m13.35-.622 1.757-1.757a4.5 4.5 0 0 0-6.364-6.364l-4.5 4.5a4.5 4.5 0 0 0 1.242 7.244" /></svg>',
    "calendar": '<svg class="hero-icon" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path stroke-linecap="round" stroke-linejoin="round" d="M6.75 3v2.25M17.25 3v2.25M3 18.75V7.5a2.25 2.25 0 0 1 2.25-2.25h13.5A2.25 2.25 0 0 1 21 7.5v11.25m-18 0A2.25 2.25 0 0 0 5.25 21h13.5A2.25 2.25 0 0 0 21 18.75m-18 0v-7.5A2.25 2.25 0 0 1 5.25 9h13.5A2.25 2.25 0 0 1 21 11.25v7.5" /></svg>',
    "check": '<svg class="hero-icon" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path stroke-linecap="round" stroke-linejoin="round" d="m4.5 12.75 6 6 9-13.5" /></svg>',
}


def _icon(name: str) -> str:
    """Return Heroicon SVG by name."""
    return _HEROICONS.get(name, "")


# デフォルトの期間（日数）
_DEFAULT_DAYS = 30


def _get_period_params_from_query(
    query: schemas.PeriodRequest,
) -> tuple[int | None, datetime.datetime | None, datetime.datetime | None]:
    """スキーマから期間パラメータを取得する。

    Args:
        query: PeriodRequest schema

    Returns:
        tuple: (days_limit, start_date, end_date)
            - カスタム期間の場合: (None, start_date, end_date)
            - 日数指定の場合: (days_limit, None, None)
    """
    try:
        # まずカスタム期間（start/end）をチェック
        if query.start and query.end:
            try:
                start_date = datetime.datetime.fromisoformat(query.start.replace("Z", "+00:00"))
                end_date = datetime.datetime.fromisoformat(query.end.replace("Z", "+00:00"))
                return None, start_date, end_date
            except ValueError:
                pass  # 無効な日付形式の場合はフォールバック

        # 有効な範囲にクランプ（1日〜365日）
        return max(1, min(365, query.days)), None, None
    except (ValueError, TypeError):
        return _DEFAULT_DAYS, None, None


def _get_days_limit_from_query(query: schemas.PeriodRequest) -> int:
    """スキーマから期間パラメータを取得する。"""
    days_limit, start_date, end_date = _get_period_params_from_query(query)
    if days_limit is not None:
        return days_limit
    # カスタム期間の場合は日数を計算
    if start_date and end_date:
        delta = end_date - start_date
        return max(1, min(365, delta.days + 1))
    return _DEFAULT_DAYS


def _get_period_kwargs(query: schemas.PeriodRequest) -> dict:
    """analyzer メソッドに渡す期間パラメータを構築する。"""
    days_limit, start_date, end_date = _get_period_params_from_query(query)
    return {"days_limit": days_limit, "start_date": start_date, "end_date": end_date}


def _get_url_prefix() -> str:
    """Blueprint の登録先 URL prefix を返す。"""
    return flask.url_for("metrics.metrics_view").removesuffix("/api/metrics")


def _get_metrics_db_path() -> str | None:
    """メトリクス DB のパスを取得する。

    メトリクスサーバー経由では起動時にロード済みの設定 (CONFIG) を参照し、
    webui 経由では設定ファイル (CONFIG_FILE_NORMAL) を読み込む。
    """
    app_config = flask.current_app.config.get("CONFIG")
    if app_config is not None:
        return str(app_config.metrics.data) if app_config.metrics is not None else None

    config_file = flask.current_app.config.get("CONFIG_FILE_NORMAL", "config.yaml")
    config = my_lib.config.load(config_file, pathlib.Path("schema/config.schema"))
    return config.get("metrics", {}).get("data", "data/metrics.db")


@blueprint.route("/api/metrics", methods=["GET"])
@my_lib.flask_util.gzipped
def metrics_view():
    """メトリクスダッシュボードのHTMLページを返す（データなし）"""
    # HTMLを生成（データは含まない）
    html_content = generate_metrics_html_skeleton(_get_url_prefix())
    return flask.Response(html_content, mimetype="text/html")


@blueprint.route("/api/metrics/data", methods=["GET"])
@my_lib.flask_util.gzipped
@validate()
def metrics_data(query: schemas.PeriodRequest) -> flask.Response | tuple[flask.Response, int]:
    """メトリクスデータをJSONで返す（非推奨：個別エンドポイントを使用）"""
    # NOTE: メトリクスデータは3分間キャッシュする（パフォーマンス改善）
    flask.g.cache_max_age = 180

    try:
        analyzer, error_response, error_code = _get_analyzer()
        if analyzer is None:
            assert error_response is not None and error_code is not None  # noqa: S101
            return error_response, error_code

        # 期間パラメータを取得
        days_limit = _get_days_limit_from_query(query)
        period = _get_period_kwargs(query)

        # データ範囲を取得
        data_range = analyzer.get_data_range()

        # すべてのメトリクスデータを収集（期間制限付き）
        basic_stats = analyzer.get_basic_statistics(**period)
        hourly_patterns = analyzer.get_hourly_patterns(**period)
        anomalies = analyzer.detect_anomalies(**period)
        trends = analyzer.get_performance_trends(**period)
        alerts = analyzer.check_performance_alerts()
        panel_trends = analyzer.get_panel_performance_trends(**period)
        performance_stats = analyzer.get_performance_statistics(**period)

        # JSONレスポンスを返す
        return flask.jsonify(
            {
                "data_range": data_range,
                "days_limit": days_limit,
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
    db_path = _get_metrics_db_path()

    if db_path is None or not pathlib.Path(db_path).exists():
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
@validate()
def metrics_basic_stats(query: schemas.PeriodRequest) -> flask.Response | tuple[flask.Response, int]:
    """基本統計データをJSONで返す"""
    flask.g.cache_max_age = 180

    try:
        analyzer, error_response, error_code = _get_analyzer()
        if analyzer is None:
            assert error_response is not None and error_code is not None  # noqa: S101
            return error_response, error_code

        days_limit = _get_days_limit_from_query(query)
        basic_stats = analyzer.get_basic_statistics(**_get_period_kwargs(query))
        return flask.jsonify({"basic_stats": basic_stats, "days_limit": days_limit})

    except Exception as e:
        logging.exception("基本統計データ取得エラー")
        return flask.jsonify({"error": "internal_error", "message": str(e)}), 500


@blueprint.route("/api/metrics/hourly-patterns", methods=["GET"])
@my_lib.flask_util.gzipped
@validate()
def metrics_hourly_patterns(query: schemas.PeriodRequest) -> flask.Response | tuple[flask.Response, int]:
    """時間別パターンデータをJSONで返す"""
    flask.g.cache_max_age = 180

    try:
        analyzer, error_response, error_code = _get_analyzer()
        if analyzer is None:
            assert error_response is not None and error_code is not None  # noqa: S101
            return error_response, error_code

        days_limit = _get_days_limit_from_query(query)
        hourly_patterns = analyzer.get_hourly_patterns(**_get_period_kwargs(query))
        return flask.jsonify({"hourly_patterns": hourly_patterns, "days_limit": days_limit})

    except Exception as e:
        logging.exception("時間別パターンデータ取得エラー")
        return flask.jsonify({"error": "internal_error", "message": str(e)}), 500


@blueprint.route("/api/metrics/trends", methods=["GET"])
@my_lib.flask_util.gzipped
@validate()
def metrics_trends(query: schemas.PeriodRequest) -> flask.Response | tuple[flask.Response, int]:
    """パフォーマンス推移データをJSONで返す"""
    flask.g.cache_max_age = 180

    try:
        analyzer, error_response, error_code = _get_analyzer()
        if analyzer is None:
            assert error_response is not None and error_code is not None  # noqa: S101
            return error_response, error_code

        days_limit = _get_days_limit_from_query(query)
        trends = analyzer.get_performance_trends(**_get_period_kwargs(query))
        return flask.jsonify({"trends": trends, "days_limit": days_limit})

    except Exception as e:
        logging.exception("パフォーマンス推移データ取得エラー")
        return flask.jsonify({"error": "internal_error", "message": str(e)}), 500


@blueprint.route("/api/metrics/panel-trends", methods=["GET"])
@my_lib.flask_util.gzipped
@validate()
def metrics_panel_trends(query: schemas.PeriodRequest) -> flask.Response | tuple[flask.Response, int]:
    """パネル別処理時間推移データをJSONで返す"""
    flask.g.cache_max_age = 180

    try:
        analyzer, error_response, error_code = _get_analyzer()
        if analyzer is None:
            assert error_response is not None and error_code is not None  # noqa: S101
            return error_response, error_code

        days_limit = _get_days_limit_from_query(query)
        panel_trends = analyzer.get_panel_performance_trends(**_get_period_kwargs(query))
        return flask.jsonify({"panel_trends": panel_trends, "days_limit": days_limit})

    except Exception as e:
        logging.exception("パネル別処理時間推移データ取得エラー")
        return flask.jsonify({"error": "internal_error", "message": str(e)}), 500


@blueprint.route("/api/metrics/panel-daily-trends", methods=["GET"])
@my_lib.flask_util.gzipped
@validate()
def metrics_panel_daily_trends(query: schemas.PeriodRequest) -> flask.Response | tuple[flask.Response, int]:
    """パネル別日別処理時間推移データをJSONで返す"""
    flask.g.cache_max_age = 180

    try:
        analyzer, error_response, error_code = _get_analyzer()
        if analyzer is None:
            assert error_response is not None and error_code is not None  # noqa: S101
            return error_response, error_code

        days_limit = _get_days_limit_from_query(query)
        panel_daily_trends = analyzer.get_panel_daily_trends(**_get_period_kwargs(query))
        return flask.jsonify({"panel_daily_trends": panel_daily_trends, "days_limit": days_limit})

    except Exception as e:
        logging.exception("パネル別日別処理時間推移データ取得エラー")
        return flask.jsonify({"error": "internal_error", "message": str(e)}), 500


@blueprint.route("/api/metrics/alerts", methods=["GET"])
@my_lib.flask_util.gzipped
@validate()
def metrics_alerts(query: schemas.PeriodRequest) -> flask.Response | tuple[flask.Response, int]:
    """アラートデータをJSONで返す"""
    flask.g.cache_max_age = 180

    try:
        analyzer, error_response, error_code = _get_analyzer()
        if analyzer is None:
            assert error_response is not None and error_code is not None  # noqa: S101
            return error_response, error_code

        alerts = analyzer.check_performance_alerts()
        return flask.jsonify({"alerts": alerts})

    except Exception as e:
        logging.exception("アラートデータ取得エラー")
        return flask.jsonify({"error": "internal_error", "message": str(e)}), 500


@blueprint.route("/api/metrics/anomalies", methods=["GET"])
@my_lib.flask_util.gzipped
@validate()
def metrics_anomalies(query: schemas.PeriodRequest) -> flask.Response | tuple[flask.Response, int]:
    """異常検知データをJSONで返す"""
    flask.g.cache_max_age = 180

    try:
        analyzer, error_response, error_code = _get_analyzer()
        if analyzer is None:
            assert error_response is not None and error_code is not None  # noqa: S101
            return error_response, error_code

        days_limit = _get_days_limit_from_query(query)
        period = _get_period_kwargs(query)
        anomalies = analyzer.detect_anomalies(**period)
        performance_stats = analyzer.get_performance_statistics(**period)
        data_range = analyzer.get_data_range()
        return flask.jsonify(
            {
                "anomalies": anomalies,
                "performance_stats": performance_stats,
                "data_range": data_range,
                "days_limit": days_limit,
            }
        )

    except Exception as e:
        logging.exception("異常検知データ取得エラー")
        return flask.jsonify({"error": "internal_error", "message": str(e)}), 500


@blueprint.route("/favicon.png", methods=["GET"])
def favicon():
    """frontend/public/favicon.pngを返す"""
    try:
        # プロジェクトルートからの相対パスでfavicon.pngを取得
        favicon_path = (
            pathlib.Path(__file__).parent.parent.parent.parent.parent / "frontend" / "public" / "favicon.png"
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


def generate_metrics_html_skeleton(url_prefix: str = ""):
    """データを含まない軽量なHTMLスケルトンを生成。"""
    favicon_path = f"{url_prefix}/favicon.png"

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
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4/dist/chart.umd.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/@sgratzl/chartjs-chart-boxplot@4/build/index.umd.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/hammerjs@2.0.8/hammer.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/chartjs-plugin-zoom@2/dist/chartjs-plugin-zoom.min.js"></script>
    <script defer src="{url_prefix}/static/metrics.js"></script>
    <script defer src="{url_prefix}/static/chart-functions.js"></script>
    <script defer src="{url_prefix}/static/metrics-loader.js"></script>
    <style>
        /* Heroicons inline SVG styles */
        .hero-icon {{
            display: inline-block;
            width: 1em;
            height: 1em;
            vertical-align: -0.125em;
            fill: none;
            stroke: currentColor;
            stroke-width: 1.5;
        }}
        .hero-icon-solid {{
            display: inline-block;
            width: 1em;
            height: 1em;
            vertical-align: -0.125em;
            fill: currentColor;
            stroke: none;
        }}
        .metrics-card {{ margin-bottom: 1rem; position: relative; }}
        .section {{ padding-top: 1.5rem; padding-bottom: 1.5rem; }}
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

        /* セクション内のローディング表示スタイル */
        .section-loading {{
            display: flex;
            align-items: center;
            justify-content: center;
            min-height: 200px;
            color: #666;
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
                        <span class="icon is-large">{_icon("chart-line")}</span>
                        天気パネル メトリクス ダッシュボード
                        <span class="permalink-icon" onclick="copyPermalink('dashboard')">{_icon("link")}</span>
                    </div>
                </h1>
                <p class="subtitle has-text-centered" id="subtitle">パフォーマンス監視と異常検知</p>

                <!-- 期間選択 -->
                <div class="section" id="period-selector" style="padding-top: 0;">
                    <h2 class="title is-4 section-header">
                        <div class="permalink-container">
                            <span class="icon">{_icon("calendar")}</span>
                            表示期間
                            <span class="permalink-icon" onclick="copyPermalink('period-selector')">{_icon("link")}</span>
                        </div>
                    </h2>
                    <div class="field">
                        <div class="field is-grouped is-grouped-multiline">
                            <div class="control">
                                <button class="button is-small" data-days="7" onclick="selectPeriod(7)">
                                    過去7日間
                                </button>
                            </div>
                            <div class="control">
                                <button class="button is-small is-primary" data-days="30"
                                        onclick="selectPeriod(30)">
                                    過去1ヶ月間
                                </button>
                            </div>
                            <div class="control">
                                <button class="button is-small" data-days="90" onclick="selectPeriod(90)">
                                    過去3ヶ月
                                </button>
                            </div>
                            <div class="control">
                                <button class="button is-small" data-days="180" onclick="selectPeriod(180)">
                                    過去半年
                                </button>
                            </div>
                            <div class="control">
                                <button class="button is-small" data-days="365" onclick="selectPeriod(365)">
                                    全期間
                                </button>
                            </div>
                            <div class="control">
                                <button class="button is-small" data-days="custom" id="custom-period-btn"
                                        onclick="toggleCustomPeriod()">
                                    カスタム
                                </button>
                            </div>
                        </div>
                    </div>

                    <!-- カスタム期間入力フォーム（初期非表示） -->
                    <div id="custom-period-form" style="display: none; margin-top: 1rem;">
                        <div class="columns">
                            <div class="column">
                                <div class="field">
                                    <label class="label is-small">開始日時</label>
                                    <div class="control">
                                        <input type="datetime-local" id="custom-start"
                                               class="input is-small" onchange="onCustomDateChange()"
                                               onkeypress="onCustomKeyPress(event)">
                                    </div>
                                </div>
                            </div>
                            <div class="column">
                                <div class="field">
                                    <label class="label is-small">終了日時</label>
                                    <div class="control">
                                        <input type="datetime-local" id="custom-end"
                                               class="input is-small" onchange="onCustomDateChange()"
                                               onkeypress="onCustomKeyPress(event)">
                                    </div>
                                </div>
                            </div>
                        </div>
                        <div class="field">
                            <div class="control">
                                <button id="apply-custom-period" class="button is-small is-fullwidth"
                                        onclick="applyCustomPeriod()" disabled>
                                    <span class="icon is-small">{_icon("check")}</span>
                                    <span>期間を確定して更新</span>
                                </button>
                            </div>
                        </div>
                    </div>
                </div>

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
        window.metricsApiUrl = '{url_prefix}/api/metrics/data';
        window.metricsApiBaseUrl = '{url_prefix}';
    </script>
</html>
    """
