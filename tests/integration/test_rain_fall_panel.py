#!/usr/bin/env python3
# ruff: noqa: S101
"""
降雨パネルの統合テスト
"""

import datetime

import pytest
import pytz


class TestRainFallPanel:
    """降雨パネルのテスト"""

    def test_rain_fall_panel_create(self, config, image_checker):
        """降雨パネルを生成できること"""
        import weather_display.panel.rain_fall

        result = weather_display.panel.rain_fall.create(config)

        assert len(result) >= 2
        img = result[0]
        assert img is not None
        image_checker.check(img, config.rain_fall.panel)


class TestRainFallPanelWithRain:
    """降雨状態のパネルテスト"""

    @pytest.fixture
    def mock_rainfall_status(self, mocker):
        """降雨状態のモック"""

        def create_mock(raining=True, amount=5.0, start_minutes_ago=30):
            start_time = datetime.datetime.now(pytz.utc) - datetime.timedelta(minutes=start_minutes_ago)
            status = {
                "amount": amount,
                "raining": {
                    "status": raining,
                    "start": start_time if raining else None,
                },
            }
            mocker.patch(
                "weather_display.panel.rain_fall._get_rainfall_status",
                return_value=status,
            )
            return status

        return create_mock

    def test_rain_fall_panel_with_rain(self, config, image_checker, mock_rainfall_status):
        """降雨中のパネルを生成できること"""
        import weather_display.panel.rain_fall

        mock_rainfall_status(raining=True, amount=5.0, start_minutes_ago=30)

        result = weather_display.panel.rain_fall.create(config)

        assert len(result) >= 2
        img = result[0]
        assert img is not None

    def test_rain_fall_panel_no_rain(self, config, image_checker, mock_rainfall_status):
        """降雨なしのパネルを生成できること"""
        import weather_display.panel.rain_fall

        mock_rainfall_status(raining=False, amount=0.0)

        result = weather_display.panel.rain_fall.create(config)

        assert len(result) >= 2
        img = result[0]
        assert img is not None

    @pytest.mark.parametrize("amount", [0.05, 0.5, 1.0, 5.5, 10.0, 50.0])
    def test_rain_fall_panel_various_amounts(self, config, image_checker, mock_rainfall_status, amount):
        """様々な降水量で正しく描画されること"""
        import weather_display.panel.rain_fall

        mock_rainfall_status(raining=True, amount=amount, start_minutes_ago=30)

        result = weather_display.panel.rain_fall.create(config)

        assert len(result) >= 2

    @pytest.mark.parametrize("minutes", [5, 30, 60, 90, 120, 180])
    def test_rain_fall_panel_various_start_times(self, config, image_checker, mock_rainfall_status, minutes):
        """様々な開始時間で正しく描画されること"""
        import weather_display.panel.rain_fall

        mock_rainfall_status(raining=True, amount=5.0, start_minutes_ago=minutes)

        result = weather_display.panel.rain_fall.create(config)

        assert len(result) >= 2


class TestRainFallPanelError:
    """降雨パネルのエラーハンドリングテスト"""

    def test_rain_fall_panel_fetch_error(self, config, image_checker, mocker):
        """データ取得エラー時に空画像を返すこと"""
        import weather_display.panel.rain_fall

        mocker.patch(
            "weather_display.panel.rain_fall._get_rainfall_status",
            return_value=None,
        )

        result = weather_display.panel.rain_fall.create(config)

        assert len(result) >= 2
        img = result[0]
        assert img is not None

    def test_rain_fall_panel_exception(self, config, image_checker, mocker):
        """例外発生時にエラー画像を返すこと"""
        import weather_display.panel.rain_fall

        mocker.patch(
            "weather_display.panel.rain_fall._create_rain_fall_panel_impl",
            side_effect=RuntimeError("Test exception"),
        )

        result = weather_display.panel.rain_fall.create(config)

        assert len(result) == 3
        assert "Traceback" in result[2]

    def test_rain_fall_panel_low_amount(self, config, image_checker, mocker):
        """極小降水量の場合の描画"""
        import weather_display.panel.rain_fall

        start_time = datetime.datetime.now(pytz.utc) - datetime.timedelta(minutes=30)
        status = {
            "amount": 0.001,  # 極小値
            "raining": {
                "status": True,
                "start": start_time,
            },
        }
        mocker.patch(
            "weather_display.panel.rain_fall._get_rainfall_status",
            return_value=status,
        )

        result = weather_display.panel.rain_fall.create(config)

        assert len(result) >= 2
