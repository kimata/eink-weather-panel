#!/usr/bin/env python3
# ruff: noqa: S101
"""
天気パネルの統合テスト
"""

import my_lib.weather
import pytest


class TestWeatherPanel:
    """天気パネルのテスト"""

    def test_weather_panel_create(self, config, image_checker):
        """天気パネルを生成できること"""
        import weather_display.panel.weather

        result = weather_display.panel.weather.create(config)

        assert len(result) >= 2
        img = result[0]
        assert img is not None
        image_checker.check(img, config.weather.panel)

    def test_weather_panel_create_not_side_by_side(self, config, image_checker):
        """横並びでない天気パネルを生成できること"""
        import weather_display.panel.weather

        result = weather_display.panel.weather.create(config, is_side_by_side=False)

        assert len(result) >= 2
        img = result[0]
        assert img is not None


class TestWeatherPanelCalculations:
    """天気パネルの計算テスト"""

    def test_calc_misnar_formula_normal(self):
        """Misnar式で体感温度が計算されること"""
        from weather_display.panel.weather import calc_misnar_formula

        result = calc_misnar_formula(25.0, 50.0, 3.0)

        # 妥当な範囲内であること
        assert 15 < result < 35

    @pytest.mark.parametrize(
        "temp,humi,wind",
        [
            (30.0, 80.0, 1.0),  # 高温多湿
            (10.0, 30.0, 5.0),  # 低温乾燥強風
            (20.0, 50.0, 0.0),  # 無風
            (35.0, 90.0, 0.5),  # 猛暑
            (0.0, 50.0, 2.0),  # 氷点
        ],
    )
    def test_calc_misnar_formula_various_conditions(self, temp, humi, wind):
        """様々な条件で体感温度が計算されること"""
        from weather_display.panel.weather import calc_misnar_formula

        result = calc_misnar_formula(temp, humi, wind)

        # 結果が数値であること
        assert isinstance(result, float)


class TestWeatherPanelWithMockedData:
    """モックデータを使用した天気パネルテスト"""

    @pytest.fixture
    def mock_weather_data(self, mocker):
        """天気データのモック"""
        from dataclasses import dataclass

        @dataclass
        class MockWeather:
            text: str = "晴れ"
            icon_url: str = "https://example.com/icon.png"

        @dataclass
        class MockWind:
            speed: int = 3
            dir: str = "北"

        @dataclass
        class MockHourInfo:
            hour: int = 12
            weather: MockWeather | None = None
            temp: float = 25.0
            precip: float = 0.0
            humi: float = 50.0
            wind: MockWind | None = None

            def __post_init__(self):
                if self.weather is None:
                    self.weather = MockWeather()
                if self.wind is None:
                    self.wind = MockWind()

        @dataclass
        class MockDayInfo:
            data: list | None = None

            def __post_init__(self):
                if self.data is None:
                    self.data = [MockHourInfo(hour=h) for h in [0, 3, 6, 9, 12, 15, 18, 21]]

        @dataclass
        class MockWeatherInfo:
            today: MockDayInfo | None = None
            tomorrow: MockDayInfo | None = None

            def __post_init__(self):
                if self.today is None:
                    self.today = MockDayInfo()
                if self.tomorrow is None:
                    self.tomorrow = MockDayInfo()

        @dataclass
        class MockClothingDay:
            data: int = 50

        @dataclass
        class MockClothingInfo:
            today: MockClothingDay | None = None
            tomorrow: MockClothingDay | None = None

            def __post_init__(self):
                if self.today is None:
                    self.today = MockClothingDay()
                if self.tomorrow is None:
                    self.tomorrow = MockClothingDay()

        @dataclass
        class MockSunsetInfo:
            today: str = "17:30"
            tomorrow: str = "17:31"

        @dataclass
        class MockWbgtDaily:
            today: list | None = None
            tomorrow: list | None = None

            def __post_init__(self):
                if self.today is None:
                    self.today = [None] * 8
                if self.tomorrow is None:
                    self.tomorrow = [None] * 8

        @dataclass
        class MockWbgtInfo:
            daily: MockWbgtDaily | None = None

            def __post_init__(self):
                if self.daily is None:
                    self.daily = MockWbgtDaily()

        return {
            "weather": MockWeatherInfo(),
            "clothing": MockClothingInfo(),
            "sunset": MockSunsetInfo(),
            "wbgt": MockWbgtInfo(),
        }

    def test_weather_panel_with_wbgt_data(self, config, image_checker, mocker, mock_weather_data):
        """WBGT データ付きで天気パネルを生成できること"""
        import weather_display.panel.weather

        # WBGTデータを設定
        wbgt_data = mock_weather_data["wbgt"]
        wbgt_data.daily.today = [25, 26, 27, 28, 29, 30, 31, 32]
        wbgt_data.daily.tomorrow = [24, 25, 26, 27, 28, 29, 30, 31]

        mocker.patch("my_lib.weather.get_weather_yahoo", return_value=mock_weather_data["weather"])
        mocker.patch("my_lib.weather.get_clothing_yahoo", return_value=mock_weather_data["clothing"])
        mocker.patch("my_lib.weather.get_sunset_nao", return_value=mock_weather_data["sunset"])
        mocker.patch("my_lib.weather.get_wbgt", return_value=wbgt_data)

        result = weather_display.panel.weather.create(config)

        assert len(result) >= 2


class TestWeatherPanelError:
    """天気パネルのエラーハンドリングテスト"""

    def test_weather_panel_api_error(self, config, image_checker, mocker):
        """API エラー時にエラー画像を返すこと"""
        import weather_display.panel.weather

        mocker.patch.object(my_lib.weather, "get_weather_yahoo", side_effect=RuntimeError("API Error"))

        result = weather_display.panel.weather.create(config)

        # エラー時は3要素のタプルを返す
        assert len(result) == 3
        assert "Traceback" in result[2]

    def test_weather_panel_timeout_error(self, config, image_checker, mocker):
        """タイムアウトエラー時にエラー画像を返すこと"""
        import weather_display.panel.weather

        mocker.patch.object(my_lib.weather, "get_weather_yahoo", side_effect=TimeoutError("Timeout"))

        result = weather_display.panel.weather.create(config)

        assert len(result) == 3


class TestRotationMap:
    """風向きの回転マップテスト"""

    def test_rotation_map_has_all_directions(self):
        """すべての風向きが定義されていること"""
        from weather_display.panel.weather import ROTATION_MAP

        expected_directions = [
            "静穏",
            "東",
            "西",
            "南",
            "北",
            "北東",
            "北西",
            "南東",
            "南西",
            "北北東",
            "北北西",
            "南南東",
            "南南西",
            "東北東",
            "東南東",
            "西北西",
            "西南西",
        ]

        for direction in expected_directions:
            assert direction in ROTATION_MAP

    def test_rotation_map_calm_is_none(self):
        """静穏は None であること"""
        from weather_display.panel.weather import ROTATION_MAP

        assert ROTATION_MAP["静穏"] is None

    @pytest.mark.parametrize(
        "direction,expected_range",
        [
            ("北", (170, 190)),
            ("南", (-10, 10)),
            ("東", (80, 100)),
            ("西", (260, 280)),
        ],
    )
    def test_rotation_map_values_in_range(self, direction, expected_range):
        """回転角度が正しい範囲内であること"""
        from weather_display.panel.weather import ROTATION_MAP

        value = ROTATION_MAP[direction]
        assert expected_range[0] <= value <= expected_range[1]


class TestDrawPrecipitation:
    """draw_precip 関数のテスト"""

    def test_draw_precip_various_levels(self, config):
        """様々な降水量レベルでエラーにならないこと"""
        import PIL.Image
        import PIL.ImageFont

        from weather_display.panel.weather import draw_precip

        img = PIL.Image.new("RGBA", (800, 600), (255, 255, 255, 255))

        # 各フォントをロード
        font_path = config.font.path
        face = {
            "value": PIL.ImageFont.truetype(f"{font_path}/migmix-1p-bold.ttf", 20),
            "unit": PIL.ImageFont.truetype(f"{font_path}/migmix-1p-regular.ttf", 12),
        }
        precip_icon = PIL.Image.new("RGBA", (20, 20), (0, 0, 255, 255))

        # 様々な降水量をテスト（各閾値をカバー）
        precip_levels = [0, 0.5, 1.5, 5, 15, 25]
        for i, precip in enumerate(precip_levels):
            draw_precip(
                img=img,
                precip=precip,
                is_first=(i == 0),
                pos_x=100 + i * 100,
                pos_y=100,
                precip_icon=precip_icon,
                face=face,
            )
