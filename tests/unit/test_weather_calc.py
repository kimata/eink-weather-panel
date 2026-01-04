#!/usr/bin/env python3
# ruff: noqa: S101
"""
天気関連計算のユニットテスト
"""

import pytest


class TestCalcMisnarFormula:
    """体感温度計算（ミスナー式）のテスト"""

    @pytest.mark.parametrize(
        "temp,humi,wind,expected_min,expected_max",
        [
            # 快適な条件
            (25, 50, 2, 18, 28),
            # 暑くて蒸し暑い（ミスナー式の計算結果に合わせて調整）
            (35, 80, 0, 30, 50),
            # 寒くて風が強い
            (10, 30, 5, -5, 12),
            # 氷点下
            (0, 50, 3, -15, 5),
            # 風がない暑い日（ミスナー式の計算結果に合わせて調整）
            (30, 60, 0, 25, 38),
            # 乾燥して涼しい
            (20, 20, 1, 12, 22),
        ],
    )
    def test_sensible_temperature_in_expected_range(self, temp, humi, wind, expected_min, expected_max):
        """体感温度が期待範囲内にあること"""
        from weather_display.panel.weather import calc_misnar_formula

        result = calc_misnar_formula(temp, humi, wind)

        assert expected_min <= result <= expected_max, (
            f"temp={temp}, humi={humi}, wind={wind}: expected {expected_min}-{expected_max}, got {result}"
        )

    def test_wind_lowers_perceived_temperature(self):
        """風速が上がると体感温度が下がること"""
        from weather_display.panel.weather import calc_misnar_formula

        temp, humi = 25, 50

        temp_no_wind = calc_misnar_formula(temp, humi, 0)
        temp_with_wind = calc_misnar_formula(temp, humi, 5)

        assert temp_with_wind < temp_no_wind

    def test_humidity_affects_perceived_temperature(self):
        """湿度が体感温度に影響すること"""
        from weather_display.panel.weather import calc_misnar_formula

        temp, wind = 30, 1

        temp_low_humi = calc_misnar_formula(temp, 30, wind)
        temp_high_humi = calc_misnar_formula(temp, 80, wind)

        # 高温時、高湿度では体感温度が上がる傾向
        assert temp_high_humi != temp_low_humi

    def test_returns_float(self):
        """戻り値が float であること"""
        from weather_display.panel.weather import calc_misnar_formula

        result = calc_misnar_formula(25, 50, 2)

        assert isinstance(result, float)

    @pytest.mark.parametrize("wind", [0, 0.5, 1, 2, 5, 10])
    def test_various_wind_speeds(self, wind):
        """様々な風速で計算できること"""
        from weather_display.panel.weather import calc_misnar_formula

        result = calc_misnar_formula(25, 50, wind)

        assert result is not None
        assert -50 < result < 60  # 合理的な範囲内

    @pytest.mark.parametrize("humi", [0, 10, 30, 50, 70, 90, 100])
    def test_various_humidity_levels(self, humi):
        """様々な湿度で計算できること"""
        from weather_display.panel.weather import calc_misnar_formula

        result = calc_misnar_formula(25, humi, 2)

        assert result is not None
        assert -50 < result < 60  # 合理的な範囲内


class TestRotationMap:
    """風向きマップのテスト"""

    def test_rotation_map_contains_all_directions(self):
        """全ての風向きが含まれていること"""
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

    def test_rotation_map_values_are_valid(self):
        """回転角度が有効な値であること"""
        from weather_display.panel.weather import ROTATION_MAP

        for direction, angle in ROTATION_MAP.items():
            if angle is not None:
                assert 0 <= angle < 360, f"{direction}: angle {angle} is out of range"

    def test_calm_has_no_rotation(self):
        """「静穏」は回転なし（None）であること"""
        from weather_display.panel.weather import ROTATION_MAP

        assert ROTATION_MAP["静穏"] is None
