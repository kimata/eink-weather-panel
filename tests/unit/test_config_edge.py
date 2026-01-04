#!/usr/bin/env python3
# ruff: noqa: S101
"""
config.py のエッジケーステスト
"""

import pytest


class TestParseAircon:
    """_parse_aircon 関数のテスト"""

    def test_parse_aircon_none(self):
        """data が None の場合"""
        from weather_display.config import _parse_aircon

        result = _parse_aircon(None)

        assert result is None


class TestParseSensorParam:
    """_parse_sensor_param 関数のテスト"""

    def test_parse_sensor_param_invalid_range_type(self):
        """range の型が不正な場合"""
        from weather_display.config import _parse_sensor_param

        data = {
            "name": "temp",
            "label": "温度",
            "unit": "℃",
            "format": "{:.1f}",
            "range": 100,  # Invalid: not 'auto' or list
            "scale": "linear",
        }

        with pytest.raises(TypeError, match="range must be 'auto' or a list"):
            _parse_sensor_param(data)

    def test_parse_sensor_param_invalid_scale(self):
        """scale が不正な場合"""
        from weather_display.config import _parse_sensor_param

        data = {
            "name": "temp",
            "label": "温度",
            "unit": "℃",
            "format": "{:.1f}",
            "range": "auto",
            "scale": "invalid",  # Invalid: not 'linear' or 'log'
        }

        with pytest.raises(ValueError, match="scale must be 'linear' or 'log'"):
            _parse_sensor_param(data)


class TestParseMetrics:
    """_parse_metrics 関数のテスト"""

    def test_parse_metrics_none(self):
        """data が None の場合"""
        from weather_display.config import _parse_metrics

        result = _parse_metrics(None)

        assert result is None


class TestParseWebapp:
    """_parse_webapp 関数のテスト"""

    def test_parse_webapp_none(self):
        """data が None の場合"""
        from weather_display.config import _parse_webapp

        result = _parse_webapp(None)

        assert result is None
