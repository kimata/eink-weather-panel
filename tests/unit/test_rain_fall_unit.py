#!/usr/bin/env python3
# ruff: noqa: S101
"""
rain_fall.py のユニットテスト
"""
import datetime

import PIL.Image
import PIL.ImageFont
import pytest


class TestDrawRainfall:
    """draw_rainfall 関数のテスト"""

    @pytest.fixture
    def sample_image(self):
        """サンプル画像"""
        return PIL.Image.new("RGBA", (800, 600), (255, 255, 255, 255))

    @pytest.fixture
    def icon_config(self, config):
        """アイコン設定"""
        return config.rain_fall.icon

    @pytest.fixture
    def face_map(self, config):
        """フォントマップ"""
        font_path = config.font.path
        return {
            "value": PIL.ImageFont.truetype(f"{font_path}/migmix-1p-bold.ttf", 30),
            "unit": PIL.ImageFont.truetype(f"{font_path}/migmix-1p-regular.ttf", 16),
        }

    def test_draw_rainfall_raining_not_dict(self, sample_image, icon_config, face_map):
        """raining が辞書でない場合"""
        from weather_display.panel.rain_fall import draw_rainfall

        rainfall_status = {
            "amount": 5.0,
            "raining": "not a dict",
        }

        result = draw_rainfall(sample_image, rainfall_status, icon_config, face_map)

        # 画像がそのまま返される
        assert result is sample_image

    def test_draw_rainfall_start_not_datetime(self, sample_image, icon_config, face_map):
        """start が datetime でない場合"""
        from weather_display.panel.rain_fall import draw_rainfall

        rainfall_status = {
            "amount": 5.0,
            "raining": {
                "status": True,
                "start": "not a datetime",
            },
        }

        result = draw_rainfall(sample_image, rainfall_status, icon_config, face_map)

        # アイコンだけ描画されて返る
        assert result is not None


class TestGetRainfallStatus:
    """get_rainfall_status 関数のテスト"""

    def test_get_rainfall_status_invalid_returns_none(self, config, mocker):
        """データが無効な場合 None を返す"""
        from dataclasses import dataclass

        from weather_display.panel.rain_fall import get_rainfall_status

        @dataclass
        class InvalidResult:
            valid: bool = False
            value: list | None = None

            def __post_init__(self):
                if self.value is None:
                    self.value = []

        mocker.patch("my_lib.sensor_data.fetch_data", return_value=InvalidResult())

        result = get_rainfall_status(config.rain_fall, config.influxdb)

        assert result is None

    def test_get_rainfall_status_raining_with_start_time(self, config, mocker):
        """降雨中の場合に開始時刻を取得する"""
        from dataclasses import dataclass

        from weather_display.panel.rain_fall import get_rainfall_status

        now = datetime.datetime.now(datetime.timezone.utc)

        @dataclass
        class ValidRainResult:
            valid: bool = True
            value: list | None = None

            def __post_init__(self):
                if self.value is None:
                    self.value = [1.0, 2.0]

        @dataclass
        class RainingResult:
            valid: bool = True
            value: list | None = None

            def __post_init__(self):
                if self.value is None:
                    self.value = [True]

        fetch_mock = mocker.patch("my_lib.sensor_data.fetch_data")
        fetch_mock.side_effect = [ValidRainResult(), RainingResult()]

        mocker.patch("my_lib.sensor_data.get_last_event", return_value=now)

        result = get_rainfall_status(config.rain_fall, config.influxdb)

        assert result is not None
        assert isinstance(result, dict)
        raining = result["raining"]
        assert isinstance(raining, dict)
        assert raining["status"] is True
        assert raining["start"] == now

    def test_get_rainfall_status_not_raining(self, config, mocker):
        """降雨していない場合は start が None (line 97)"""
        from dataclasses import dataclass

        from weather_display.panel.rain_fall import get_rainfall_status

        @dataclass
        class ValidRainResult:
            valid: bool = True
            value: list | None = None

            def __post_init__(self):
                if self.value is None:
                    self.value = [1.0, 2.0]

        @dataclass
        class NotRainingResult:
            valid: bool = True
            value: list | None = None

            def __post_init__(self):
                if self.value is None:
                    self.value = [False]  # 降雨していない

        fetch_mock = mocker.patch("my_lib.sensor_data.fetch_data")
        fetch_mock.side_effect = [ValidRainResult(), NotRainingResult()]

        result = get_rainfall_status(config.rain_fall, config.influxdb)

        assert result is not None
        assert isinstance(result, dict)
        raining = result["raining"]
        assert isinstance(raining, dict)
        assert raining["status"] is False
        assert raining["start"] is None


class TestGenAmountText:
    """gen_amount_text 関数のテスト"""

    @pytest.mark.parametrize(
        "amount,expected",
        [
            (0.5, "0.5"),
            (0.55, "0.55"),  # 2桁小数点
            (1.0, "1.0"),  # < 10 は .1f
            (1.5, "1.5"),
            (5.0, "5.0"),  # < 10 は .1f
            (10.0, "10"),  # >= 10 は int
            (15.5, "15"),  # >= 10 は int
            (100.0, "100"),
        ],
    )
    def test_gen_amount_text_various_values(self, amount, expected):
        """様々な降水量でテキスト生成"""
        from weather_display.panel.rain_fall import gen_amount_text

        result = gen_amount_text(amount)

        assert result == expected


class TestGenStartText:
    """gen_start_text 関数のテスト"""

    def test_gen_start_text_minutes(self, mocker):
        """分単位の場合"""
        import pytz

        from weather_display.panel.rain_fall import gen_start_text

        now = datetime.datetime.now(pytz.utc)
        start = now - datetime.timedelta(minutes=30)

        result = gen_start_text(start)

        assert "30分前" in result

    def test_gen_start_text_1_hour(self, mocker):
        """1時間以上2時間未満の場合"""
        import pytz

        from weather_display.panel.rain_fall import gen_start_text

        now = datetime.datetime.now(pytz.utc)
        start = now - datetime.timedelta(minutes=90)

        result = gen_start_text(start)

        assert "1時間" in result

    def test_gen_start_text_hours(self, mocker):
        """2時間以上の場合"""
        import pytz

        from weather_display.panel.rain_fall import gen_start_text

        now = datetime.datetime.now(pytz.utc)
        start = now - datetime.timedelta(hours=5)

        result = gen_start_text(start)

        assert "5時間前" in result
