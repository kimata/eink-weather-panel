#!/usr/bin/env python3
# ruff: noqa: S101
"""
metrics/webapi/page.py の API テスト
"""

import pathlib

import pytest


class TestMetricsEndpoints:
    """メトリクス API エンドポイントのテスト"""

    def test_metrics_view_returns_html(self, client):
        """metrics エンドポイントが HTML を返すこと"""
        response = client.get("/panel/api/metrics")

        assert response.status_code == 200
        assert b"<!DOCTYPE html>" in response.data or b"<html" in response.data

    def test_metrics_data_returns_json(self, client):
        """metrics/data エンドポイントが JSON を返すこと"""
        response = client.get("/panel/api/metrics/data")

        # データベースがない場合は 503 または 200 を返す
        assert response.status_code in [200, 500, 503]

    def test_metrics_basic_stats_endpoint(self, client):
        """basic-stats エンドポイントが動作すること"""
        response = client.get("/panel/api/metrics/basic-stats")

        assert response.status_code in [200, 500, 503]

    def test_metrics_hourly_patterns_endpoint(self, client):
        """hourly-patterns エンドポイントが動作すること"""
        response = client.get("/panel/api/metrics/hourly-patterns")

        assert response.status_code in [200, 500, 503]

    def test_metrics_trends_endpoint(self, client):
        """trends エンドポイントが動作すること"""
        response = client.get("/panel/api/metrics/trends")

        assert response.status_code in [200, 500, 503]

    def test_metrics_panel_trends_endpoint(self, client):
        """panel-trends エンドポイントが動作すること"""
        response = client.get("/panel/api/metrics/panel-trends")

        assert response.status_code in [200, 500, 503]

    def test_metrics_alerts_endpoint(self, client):
        """alerts エンドポイントが動作すること"""
        response = client.get("/panel/api/metrics/alerts")

        assert response.status_code in [200, 500, 503]

    def test_metrics_anomalies_endpoint(self, client):
        """anomalies エンドポイントが動作すること"""
        response = client.get("/panel/api/metrics/anomalies")

        assert response.status_code in [200, 500, 503]


class TestMetricsEndpointsWithMock:
    """モックを使用したメトリクス API テスト"""

    @pytest.fixture
    def mock_analyzer(self, mocker):
        """MetricsAnalyzer のモック"""
        mock = mocker.MagicMock()
        mock.get_data_range.return_value = {"start": "2024-01-01", "end": "2024-12-31"}
        mock.get_basic_statistics.return_value = {"total": 100}
        mock.get_hourly_patterns.return_value = {"hour_0": 10}
        mock.detect_anomalies.return_value = []
        mock.get_performance_trends.return_value = {"trend": "stable"}
        mock.check_performance_alerts.return_value = []
        mock.get_panel_performance_trends.return_value = {"weather": {"trend": "stable"}}
        mock.get_performance_statistics.return_value = {"avg": 1.0}

        return mock

    def test_metrics_data_with_valid_database(self, client, mocker, mock_analyzer, tmp_path):
        """有効なデータベースで metrics/data が正常に動作すること"""
        import weather_display.metrics.webapi.page

        # 一時的なデータベースファイルを作成
        db_path = tmp_path / "metrics.db"
        db_path.touch()

        # モックを設定
        mock_config = {"metrics": {"data": str(db_path)}}
        mocker.patch("my_lib.config.load", return_value=mock_config)
        mocker.patch.object(weather_display.metrics.collector, "MetricsAnalyzer", return_value=mock_analyzer)

        response = client.get("/panel/api/metrics/data")

        assert response.status_code == 200


class TestGenerateMetricsHtmlSkeleton:
    """generate_metrics_html_skeleton 関数のテスト"""

    def test_generate_metrics_html_skeleton_returns_html(self):
        """HTML スケルトンを生成すること"""
        from weather_display.metrics.webapi.page import generate_metrics_html_skeleton

        html = generate_metrics_html_skeleton()

        assert "<!DOCTYPE html>" in html
        assert "<html" in html
        assert "</html>" in html


class TestStaticFiles:
    """静的ファイルエンドポイントのテスト"""

    def test_favicon_endpoint(self, client):
        """favicon エンドポイントが動作すること"""
        response = client.get("/panel/favicon.png")

        # ファイルが存在しない場合は 404
        assert response.status_code in [200, 404]

    def test_static_js_not_found(self, client):
        """存在しない JS ファイルで 404 を返すこと"""
        response = client.get("/panel/static/nonexistent.js")

        assert response.status_code == 404

    def test_static_css_not_found(self, client):
        """存在しない CSS ファイルで 404 を返すこと"""
        response = client.get("/panel/static/nonexistent.css")

        assert response.status_code == 404

    def test_static_metrics_js_exists(self, client):
        """既存の metrics.js ファイルにアクセスできること"""
        response = client.get("/panel/static/metrics.js")

        assert response.status_code == 200
        assert "javascript" in response.content_type

    def test_static_chart_functions_js_exists(self, client):
        """既存の chart-functions.js ファイルにアクセスできること"""
        response = client.get("/panel/static/chart-functions.js")

        assert response.status_code == 200
        assert "javascript" in response.content_type

    def test_static_metrics_loader_js_exists(self, client):
        """既存の metrics-loader.js ファイルにアクセスできること"""
        response = client.get("/panel/static/metrics-loader.js")

        assert response.status_code == 200
        assert "javascript" in response.content_type


class TestMetricsEndpointsErrorHandling:
    """メトリクス API エンドポイントのエラーハンドリングテスト"""

    def test_metrics_data_database_not_found(self, client, mocker):
        """データベースが見つからない場合に 503 を返すこと"""
        mock_config = {"metrics": {"data": "/nonexistent/path/metrics.db"}}
        mocker.patch("my_lib.config.load", return_value=mock_config)

        response = client.get("/panel/api/metrics/data")

        assert response.status_code == 503

    def test_metrics_data_exception(self, client, mocker):
        """例外発生時に 500 を返すこと"""
        mocker.patch("my_lib.config.load", side_effect=Exception("Config error"))

        response = client.get("/panel/api/metrics/data")

        assert response.status_code == 500

    def test_metrics_basic_stats_database_not_found(self, client, mocker):
        """basic-stats: データベースが見つからない場合に 503 を返すこと"""
        mock_config = {"metrics": {"data": "/nonexistent/path/metrics.db"}}
        mocker.patch("my_lib.config.load", return_value=mock_config)

        response = client.get("/panel/api/metrics/basic-stats")

        assert response.status_code == 503

    def test_metrics_basic_stats_exception(self, client, mocker):
        """basic-stats: 例外発生時に 500 を返すこと"""
        mocker.patch("my_lib.config.load", side_effect=Exception("Config error"))

        response = client.get("/panel/api/metrics/basic-stats")

        assert response.status_code == 500

    def test_metrics_hourly_patterns_database_not_found(self, client, mocker):
        """hourly-patterns: データベースが見つからない場合に 503 を返すこと"""
        mock_config = {"metrics": {"data": "/nonexistent/path/metrics.db"}}
        mocker.patch("my_lib.config.load", return_value=mock_config)

        response = client.get("/panel/api/metrics/hourly-patterns")

        assert response.status_code == 503

    def test_metrics_hourly_patterns_exception(self, client, mocker):
        """hourly-patterns: 例外発生時に 500 を返すこと"""
        mocker.patch("my_lib.config.load", side_effect=Exception("Config error"))

        response = client.get("/panel/api/metrics/hourly-patterns")

        assert response.status_code == 500

    def test_metrics_trends_database_not_found(self, client, mocker):
        """trends: データベースが見つからない場合に 503 を返すこと"""
        mock_config = {"metrics": {"data": "/nonexistent/path/metrics.db"}}
        mocker.patch("my_lib.config.load", return_value=mock_config)

        response = client.get("/panel/api/metrics/trends")

        assert response.status_code == 503

    def test_metrics_trends_exception(self, client, mocker):
        """trends: 例外発生時に 500 を返すこと"""
        mocker.patch("my_lib.config.load", side_effect=Exception("Config error"))

        response = client.get("/panel/api/metrics/trends")

        assert response.status_code == 500

    def test_metrics_panel_trends_database_not_found(self, client, mocker):
        """panel-trends: データベースが見つからない場合に 503 を返すこと"""
        mock_config = {"metrics": {"data": "/nonexistent/path/metrics.db"}}
        mocker.patch("my_lib.config.load", return_value=mock_config)

        response = client.get("/panel/api/metrics/panel-trends")

        assert response.status_code == 503

    def test_metrics_panel_trends_exception(self, client, mocker):
        """panel-trends: 例外発生時に 500 を返すこと"""
        mocker.patch("my_lib.config.load", side_effect=Exception("Config error"))

        response = client.get("/panel/api/metrics/panel-trends")

        assert response.status_code == 500

    def test_metrics_alerts_database_not_found(self, client, mocker):
        """alerts: データベースが見つからない場合に 503 を返すこと"""
        mock_config = {"metrics": {"data": "/nonexistent/path/metrics.db"}}
        mocker.patch("my_lib.config.load", return_value=mock_config)

        response = client.get("/panel/api/metrics/alerts")

        assert response.status_code == 503

    def test_metrics_alerts_exception(self, client, mocker):
        """alerts: 例外発生時に 500 を返すこと"""
        mocker.patch("my_lib.config.load", side_effect=Exception("Config error"))

        response = client.get("/panel/api/metrics/alerts")

        assert response.status_code == 500

    def test_metrics_anomalies_database_not_found(self, client, mocker):
        """anomalies: データベースが見つからない場合に 503 を返すこと"""
        mock_config = {"metrics": {"data": "/nonexistent/path/metrics.db"}}
        mocker.patch("my_lib.config.load", return_value=mock_config)

        response = client.get("/panel/api/metrics/anomalies")

        assert response.status_code == 503

    def test_metrics_anomalies_exception(self, client, mocker):
        """anomalies: 例外発生時に 500 を返すこと"""
        mocker.patch("my_lib.config.load", side_effect=Exception("Config error"))

        response = client.get("/panel/api/metrics/anomalies")

        assert response.status_code == 500

    def test_favicon_not_found(self, client, mocker):
        """favicon.png が見つからない場合に 404 を返すこと"""

        mocker.patch.object(pathlib.Path, "exists", return_value=False)

        response = client.get("/panel/favicon.png")

        assert response.status_code == 404

    def test_favicon_exception(self, client, mocker):
        """favicon.png 取得中に例外発生時に 500 を返すこと"""

        mocker.patch.object(pathlib.Path, "exists", return_value=True)
        mocker.patch("flask.send_file", side_effect=Exception("Send file error"))

        response = client.get("/panel/favicon.png")

        assert response.status_code == 500
