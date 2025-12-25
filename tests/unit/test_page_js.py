#!/usr/bin/env python3
# ruff: noqa: S101
"""
metrics/webapi/page_js.py のユニットテスト
"""


class TestGenerateChartJavascript:
    """generate_chart_javascript 関数のテスト"""

    def test_generate_chart_javascript_returns_string(self):
        """JavaScript文字列を返すこと"""
        from weather_display.metrics.webapi.page_js import generate_chart_javascript

        js_code = generate_chart_javascript()

        assert isinstance(js_code, str)
        assert len(js_code) > 0

    def test_generate_chart_javascript_contains_required_functions(self):
        """必要な関数が含まれていること"""
        from weather_display.metrics.webapi.page_js import generate_chart_javascript

        js_code = generate_chart_javascript()

        # 必要な関数が含まれていることを確認
        assert "generateHourlyCharts" in js_code
        assert "generateDiffSecCharts" in js_code
        assert "generateBoxplotCharts" in js_code
        assert "generateTrendsCharts" in js_code
        assert "generatePanelTrendsCharts" in js_code
        assert "generatePanelTimeSeriesChart" in js_code
        assert "getBoxplotColor" in js_code
        assert "getBorderColor" in js_code

    def test_generate_chart_javascript_contains_chart_creation(self):
        """Chart.js のチャート作成コードが含まれていること"""
        from weather_display.metrics.webapi.page_js import generate_chart_javascript

        js_code = generate_chart_javascript()

        assert "new Chart" in js_code
        assert "type: 'line'" in js_code
        assert "type: 'boxplot'" in js_code
        assert "type: 'bar'" in js_code

    def test_generate_chart_javascript_contains_canvas_ids(self):
        """キャンバスIDが含まれていること"""
        from weather_display.metrics.webapi.page_js import generate_chart_javascript

        js_code = generate_chart_javascript()

        assert "drawPanelHourlyChart" in js_code
        assert "displayImageHourlyChart" in js_code
        assert "diffSecHourlyChart" in js_code
        assert "drawPanelBoxplotChart" in js_code
        assert "displayImageBoxplotChart" in js_code
        assert "drawPanelTrendsChart" in js_code
        assert "displayImageTrendsChart" in js_code
        assert "panelTimeSeriesChart" in js_code
