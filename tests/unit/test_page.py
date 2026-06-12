#!/usr/bin/env python3
# ruff: noqa: S101
"""
metrics/webapi/page.py のユニットテスト

HTML生成関数と各種エンドポイントのテスト
"""


class TestMetricsSkeletonGeneration:
    """generate_metrics_html_skeleton 関数のテスト"""

    def test_skeleton_contains_required_elements(self):
        """スケルトンに必要な要素が含まれること"""
        from weather_display.metrics.webapi.page import generate_metrics_html_skeleton

        html = generate_metrics_html_skeleton()

        assert "metricsApiUrl" in html
        assert "metricsApiBaseUrl" in html
        assert "progress-display" in html
        assert "metrics-content" in html


class TestStaticFilesEndpoint:
    """static_files エンドポイントのテスト"""

    def test_static_js_file_not_found(self, client):
        """存在しないJSファイルが404を返すこと"""
        response = client.get("/panel/static/nonexistent.js")

        assert response.status_code == 404

    def test_static_css_file_not_found(self, client):
        """存在しないCSSファイルが404を返すこと"""
        response = client.get("/panel/static/nonexistent.css")

        assert response.status_code == 404


class TestFaviconEndpoint:
    """favicon エンドポイントのテスト"""

    def test_favicon_returns_response(self, client):
        """favicon エンドポイントがレスポンスを返すこと"""
        response = client.get("/panel/favicon.png")

        # ファイルが存在する場合は200、存在しない場合は404
        assert response.status_code in [200, 404]
