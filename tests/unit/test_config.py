#!/usr/bin/env python3
# ruff: noqa: S101
"""
設定ファイル関連のユニットテスト
"""
import pathlib

import pytest


class TestConfigLoad:
    """設定ファイル読み込みのテスト"""

    def test_load_normal_config_succeeds(self):
        """通常設定ファイルが正しく読み込めること"""
        import weather_display.config

        config = weather_display.config.load("config.example.yaml")

        assert config is not None
        assert config.panel.device.width > 0
        assert config.panel.device.height > 0

    def test_load_small_config_succeeds(self):
        """小型ディスプレイ用設定ファイルが正しく読み込めること"""
        import weather_display.config

        config = weather_display.config.load("config-small.example.yaml")

        assert config is not None
        assert config.panel.device.width > 0
        assert config.panel.device.height > 0

    def test_load_with_schema_succeeds(self):
        """スキーマ指定で設定ファイルが読み込めること"""
        import weather_display.config

        config = weather_display.config.load(
            "config.example.yaml",
            pathlib.Path("config.schema"),
        )

        assert config is not None


class TestConfigParse:
    """設定パースのテスト"""

    def test_parse_panel_geometry_has_required_fields(self, config):
        """PanelGeometry に必要なフィールドがあること"""
        panel = config.weather.panel

        assert hasattr(panel, "width")
        assert hasattr(panel, "height")
        assert hasattr(panel, "offset_x")
        assert hasattr(panel, "offset_y")

    def test_parse_influxdb_config_has_required_fields(self, config):
        """InfluxDB 設定に必要なフィールドがあること"""
        influxdb = config.influxdb

        # influxdb は dict 型
        assert "url" in influxdb
        assert "org" in influxdb
        assert "token" in influxdb
        assert "bucket" in influxdb

    def test_parse_font_config_has_required_fields(self, config):
        """フォント設定に必要なフィールドがあること"""
        font = config.font

        assert hasattr(font, "path")
        assert hasattr(font, "map")

    def test_parse_liveness_config_has_required_fields(self, config):
        """Liveness 設定に必要なフィールドがあること"""
        liveness = config.liveness

        assert hasattr(liveness, "file")
        assert hasattr(liveness.file, "display")


class TestConfigValues:
    """設定値の検証テスト"""

    def test_panel_dimensions_are_positive(self, config):
        """パネルサイズが正の値であること"""
        assert config.panel.device.width > 0
        assert config.panel.device.height > 0

    def test_update_interval_is_positive(self, config):
        """更新間隔が正の値であること"""
        assert config.panel.update.interval > 0

    def test_weather_panel_has_valid_geometry(self, config):
        """天気パネルのジオメトリが有効であること"""
        panel = config.weather.panel

        assert panel.width > 0
        assert panel.height > 0
        assert panel.offset_x >= 0
        assert panel.offset_y >= 0

    def test_sensor_config_has_room_list(self, config):
        """センサー設定に部屋リストがあること"""
        if config.sensor is not None:
            assert len(config.sensor.room_list) > 0
            assert len(config.sensor.param_list) > 0


class TestConfigSmall:
    """小型ディスプレイ設定のテスト"""

    def test_small_config_has_smaller_dimensions(self, config, config_small):
        """小型設定は通常設定より小さいサイズであること"""
        assert config_small.panel.device.width <= config.panel.device.width
        assert config_small.panel.device.height <= config.panel.device.height

    def test_small_config_weather_panel_exists(self, config_small):
        """小型設定にも天気パネルがあること"""
        assert config_small.weather is not None
        assert config_small.weather.panel.width > 0

    def test_small_config_wbgt_panel_exists(self, config_small):
        """小型設定にもWBGTパネルがあること"""
        assert config_small.wbgt is not None
        assert config_small.wbgt.panel.width > 0
