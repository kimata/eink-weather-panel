#!/usr/bin/env python3
# ruff: noqa: S101
"""
パネル描画の統合テスト

各パネルモジュールの統合テストを行います。
"""
import datetime
import zoneinfo

import pytest


class TestWeatherPanel:
    """天気パネルのテスト"""

    def test_weather_panel_create(self, config, image_checker):
        """天気パネルを生成できること"""
        import weather_display.panel.weather

        result = weather_display.panel.weather.create(config)

        assert len(result) >= 2
        img = result[0]
        elapsed = result[1]

        assert img is not None
        assert elapsed >= 0
        image_checker.check(img, config.weather.panel)

    def test_weather_panel_create_not_side_by_side(self, config, image_checker):
        """横並びでない天気パネルを生成できること"""
        import weather_display.panel.weather

        result = weather_display.panel.weather.create(config, is_side_by_side=False)

        assert len(result) >= 2
        img = result[0]
        assert img is not None
        image_checker.check(img, config.weather.panel)


class TestWbgtPanel:
    """WBGT パネルのテスト"""

    def test_wbgt_panel_create(self, config, image_checker):
        """WBGT パネルを生成できること"""
        import weather_display.panel.wbgt

        result = weather_display.panel.wbgt.create(config)

        assert len(result) >= 2
        img = result[0]
        elapsed = result[1]

        assert img is not None
        assert elapsed >= 0
        image_checker.check(img, config.wbgt.panel)


class TestTimePanel:
    """時刻パネルのテスト"""

    def test_time_panel_create(self, config, image_checker):
        """時刻パネルを生成できること"""
        import weather_display.panel.time

        result = weather_display.panel.time.create(config)

        assert len(result) >= 2
        img = result[0]
        elapsed = result[1]

        assert img is not None
        assert elapsed >= 0
        image_checker.check(img, config.time.panel)


class TestRainCloudPanel:
    """雨雲パネルのテスト"""

    def test_rain_cloud_panel_create(self, config, image_checker):
        """雨雲パネルを生成できること"""
        import weather_display.panel.rain_cloud

        result = weather_display.panel.rain_cloud.create(config)

        assert len(result) >= 2
        img = result[0]
        elapsed = result[1]

        assert img is not None
        assert elapsed >= 0
        image_checker.check(img, config.rain_cloud.panel)

    def test_rain_cloud_panel_create_not_side_by_side(self, config, image_checker):
        """横並びでない雨雲パネルを生成できること"""
        import weather_display.panel.rain_cloud

        result = weather_display.panel.rain_cloud.create(config, is_side_by_side=False)

        assert len(result) >= 2
        img = result[0]
        assert img is not None


class TestSensorGraphPanel:
    """センサーグラフパネルのテスト"""

    def test_sensor_graph_panel_create(self, config, image_checker, mock_sensor_fetch_data):
        """センサーグラフパネルを生成できること"""
        import weather_display.panel.sensor_graph

        mock_sensor_fetch_data()

        result = weather_display.panel.sensor_graph.create(config)

        assert len(result) >= 2
        img = result[0]
        elapsed = result[1]

        assert img is not None
        assert elapsed >= 0
        image_checker.check(img, config.sensor.panel)


class TestPowerGraphPanel:
    """電力グラフパネルのテスト"""

    def test_power_graph_panel_create(self, config, image_checker, mock_sensor_fetch_data):
        """電力グラフパネルを生成できること"""
        import weather_display.panel.power_graph

        mock_sensor_fetch_data()

        result = weather_display.panel.power_graph.create(config)

        assert len(result) >= 2
        img = result[0]
        elapsed = result[1]

        assert img is not None
        assert elapsed >= 0
        image_checker.check(img, config.power.panel)


class TestRainFallPanel:
    """降雨パネルのテスト"""

    def test_rain_fall_panel_create(self, config, image_checker):
        """降雨パネルを生成できること"""
        import weather_display.panel.rain_fall

        result = weather_display.panel.rain_fall.create(config)

        assert len(result) >= 2
        img = result[0]
        elapsed = result[1]

        assert img is not None
        assert elapsed >= 0
        image_checker.check(img, config.rain_fall.panel)
