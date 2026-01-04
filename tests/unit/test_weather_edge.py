#!/usr/bin/env python3
# ruff: noqa: S101
"""
weather.py のエッジケーステスト
"""

import PIL.Image
import PIL.ImageFont
import pytest


class TestDrawClothing:
    """draw_clothing 関数のテスト"""

    @pytest.fixture
    def clothing_icons(self, config):
        """服装アイコンのモック"""
        icon = {}
        for i in range(1, 6):
            icon[f"clothing-full-{i}"] = PIL.Image.new("RGBA", (50, 50), (128, 128, 128, 255))
            icon[f"clothing-half-{i}"] = PIL.Image.new("RGBA", (50, 50), (200, 200, 200, 255))
        return icon

    def test_draw_clothing_low_value(self, config, clothing_icons):
        """clothing_info が 0 の場合 (icon_index == 0 のケース)"""
        from weather_display.panel.weather import _draw_clothing

        img = PIL.Image.new("RGBA", (800, 600), (255, 255, 255, 255))

        # clothing_info = 0 でテスト (icon_index = ceil(0/20) = 0 → 1 に補正)
        _draw_clothing(
            img=img,
            pos_x=100,
            pos_y=100,
            clothing_info=0,
            icon=clothing_icons,
        )

    def test_draw_clothing_shadow_icon(self, config, clothing_icons):
        """clothing_info が低く shadow_icon が使われるケース"""
        from weather_display.panel.weather import _draw_clothing

        img = PIL.Image.new("RGBA", (800, 600), (255, 255, 255, 255))

        # clothing_info = 5 でテスト (最初のアイコンが shadow)
        _draw_clothing(
            img=img,
            pos_x=100,
            pos_y=100,
            clothing_info=5,
            icon=clothing_icons,
        )

    def test_draw_clothing_half_icon(self, config, clothing_icons):
        """half_icon が使われるケース"""
        from weather_display.panel.weather import _draw_clothing

        img = PIL.Image.new("RGBA", (800, 600), (255, 255, 255, 255))

        # clothing_info = 15 でテスト (最初のアイコンが half)
        _draw_clothing(
            img=img,
            pos_x=100,
            pos_y=100,
            clothing_info=15,
            icon=clothing_icons,
        )


class TestDrawWind:
    """draw_wind 関数のテスト"""

    @pytest.fixture
    def wind_icons(self):
        """風向きアイコンのモック"""
        return {
            "arrow": PIL.Image.new("RGBA", (30, 30), (0, 0, 0, 255)),
            "wind": PIL.Image.new("RGBA", (20, 20), (100, 100, 100, 255)),
        }

    @pytest.fixture
    def wind_face(self, config):
        """風表示用フォント (face_map["wind"] と同じ構造)"""
        from weather_display.panel.weather import _get_face_map

        face_map = _get_face_map(config.font)
        return face_map["wind"]

    def test_draw_wind_zero_speed(self, config, wind_icons, wind_face):
        """wind.speed == 0 の場合 (lines 395-396)"""
        from my_lib.weather import WindInfo

        from weather_display.panel.weather import _draw_wind

        img = PIL.Image.new("RGBA", (800, 600), (255, 255, 255, 255))
        wind = WindInfo(speed=0, dir="静穏")

        result = _draw_wind(
            img=img,
            wind=wind,
            is_first=True,
            pos_x=100,
            pos_y=100,
            icon=wind_icons,
            face=wind_face,
        )

        assert result > 100  # pos_y が更新されていること

    def test_draw_wind_calm_direction(self, config, wind_icons, wind_face):
        """wind.dir == "静穏" の場合 (ROTATION_MAP[wind.dir] is None, line 414->430)"""
        from my_lib.weather import WindInfo

        from weather_display.panel.weather import _draw_wind

        img = PIL.Image.new("RGBA", (800, 600), (255, 255, 255, 255))
        wind = WindInfo(speed=1, dir="静穏")  # speed != 0 but dir is calm

        result = _draw_wind(
            img=img,
            wind=wind,
            is_first=False,
            pos_x=100,
            pos_y=100,
            icon=wind_icons,
            face=wind_face,
        )

        assert result > 100

    def test_draw_wind_speed_3(self, config, wind_icons, wind_face):
        """wind.speed == 3 の場合 (lines 403-405)"""
        from my_lib.weather import WindInfo

        from weather_display.panel.weather import _draw_wind

        img = PIL.Image.new("RGBA", (800, 600), (255, 255, 255, 255))
        wind = WindInfo(speed=3, dir="北")

        result = _draw_wind(
            img=img,
            wind=wind,
            is_first=False,
            pos_x=100,
            pos_y=100,
            icon=wind_icons,
            face=wind_face,
        )

        assert result > 100


class TestDrawWeatherInfo:
    """draw_weather_info 関数のテスト (is_wbgt_exist == True のカバー)"""

    @pytest.fixture
    def weather_info_icons(self, config):
        """天気情報表示用アイコン"""
        icon = {
            "sun": PIL.Image.new("RGBA", (30, 30), (255, 200, 0, 255)),
            "clothes": PIL.Image.new("RGBA", (30, 30), (100, 100, 100, 255)),
            "arrow": PIL.Image.new("RGBA", (30, 30), (0, 0, 0, 255)),
            "wind": PIL.Image.new("RGBA", (20, 20), (100, 100, 100, 255)),
            "thermo": PIL.Image.new("RGBA", (20, 20), (255, 0, 0, 255)),
            "precip": PIL.Image.new("RGBA", (20, 20), (0, 0, 255, 255)),
        }
        for name in ["sunny", "cloudy", "rainy", "snowy"]:
            icon[name] = PIL.Image.new("RGBA", (50, 50), (200, 200, 200, 255))
        return icon

    @pytest.fixture
    def weather_info_face_map(self, config):
        """フェイスマップ (weather.py の get_face_map を使用)"""
        from weather_display.panel.weather import _get_face_map

        return _get_face_map(config.font)

    def test_draw_weather_info_with_wbgt(self, config, weather_info_icons, weather_info_face_map, mocker):
        """is_wbgt_exist == True のケース (line 574)"""
        from my_lib.weather import HourlyData, WeatherInfo, WindInfo

        from weather_display.panel.weather import _draw_hourly_weather

        weather = WeatherInfo(
            icon_url="https://example.com/sunny.png",
            text="晴れ",
        )
        wind = WindInfo(speed=2, dir="北")
        info = HourlyData(
            hour=12,
            weather=weather,
            temp=30.0,
            precip=0.0,
            humi=70.0,
            wind=wind,
        )

        # Mock get_image to avoid network request
        mock_icon = PIL.Image.new("RGBA", (100, 100), (200, 200, 200, 255))
        mocker.patch("weather_display.panel.weather._get_image", return_value=mock_icon)

        img = PIL.Image.new("RGBA", (800, 800), (255, 255, 255, 255))
        overlay = PIL.Image.new("RGBA", (800, 800), (0, 0, 0, 0))
        wbgt = 28.5  # WBGT値が存在

        result = _draw_hourly_weather(
            img=img,
            info=info,
            wbgt=wbgt,
            is_wbgt_exist=True,  # is_wbgt_exist == True をテスト
            is_today=True,
            is_first=True,
            pos_x=100,
            pos_y=50,
            overlay=overlay,
            icon=weather_info_icons,
            face_map=weather_info_face_map,
        )

        assert result > 50  # pos_x が更新されていること


class TestSensorGraphNonDummyMode:
    """DUMMY_MODE=false での sensor_graph テスト"""

    def test_sensor_graph_real_mode(self, config, mocker):
        """DUMMY_MODE=false での動作確認"""
        import os

        import weather_display.panel.sensor_graph

        mocker.patch.dict(os.environ, {"DUMMY_MODE": "false"})

        result = weather_display.panel.sensor_graph.create(config)

        assert len(result) >= 2


class TestSensorGraphUtilsNonDummyMode:
    """DUMMY_MODE=false での sensor_graph_utils テスト"""

    def test_get_aircon_power_requests_real_mode(self, config, mocker):
        """DUMMY_MODE=false での get_aircon_power_requests"""
        import os

        from weather_display.panel.sensor_graph_utils import get_aircon_power_requests

        mocker.patch.dict(os.environ, {"DUMMY_MODE": "false"})

        requests, _ = get_aircon_power_requests(config.sensor.room_list)

        # リクエストが生成されること
        assert isinstance(requests, list)
