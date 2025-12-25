#!/usr/bin/env python3
# ruff: noqa: S101
"""
降雨表示ユーティリティのユニットテスト
"""
import datetime
import re

import pytest
import pytz


class TestGenAmountText:
    """降水量テキスト生成のテスト"""

    @pytest.mark.parametrize(
        "amount,expected",
        [
            (0.0, "0.0"),
            (0.05, "0.05"),
            (0.12, "0.12"),
            (0.5, "0.5"),
            (0.9, "0.9"),
            (1.0, "1.0"),
            (5.5, "5.5"),
            (9.9, "9.9"),
            (10, "10"),
            (15.7, "15"),
            (100, "100"),
        ],
    )
    def test_format_based_on_amount(self, amount, expected):
        """降水量に応じた表示形式"""
        from weather_display.panel.rain_fall import gen_amount_text

        result = gen_amount_text(amount)

        assert result == expected

    def test_large_amount_is_integer(self):
        """10以上の値は整数表示であること"""
        from weather_display.panel.rain_fall import gen_amount_text

        result = gen_amount_text(25.8)

        assert result == "25"
        assert "." not in result

    def test_small_amount_with_two_decimals(self):
        """1未満で小数第2位が0でない場合は小数2桁表示"""
        from weather_display.panel.rain_fall import gen_amount_text

        result = gen_amount_text(0.15)

        assert result == "0.15"

    def test_small_amount_with_one_decimal(self):
        """1未満で小数第2位が0の場合は小数1桁表示"""
        from weather_display.panel.rain_fall import gen_amount_text

        result = gen_amount_text(0.10)

        assert result == "0.1"


class TestGenStartText:
    """降雨開始時刻テキスト生成のテスト"""

    def _create_time_ago(self, minutes):
        """指定分前の時刻を作成"""
        return datetime.datetime.now(pytz.utc) - datetime.timedelta(minutes=minutes)

    @pytest.mark.parametrize(
        "minutes_ago,expected_pattern",
        [
            (5, r"\(5分前〜\)"),
            (30, r"\(30分前〜\)"),
            (59, r"\(59分前〜\)"),
            (60, r"\(1時間0分前〜\)"),
            (90, r"\(1時間30分前〜\)"),
            (119, r"\(1時間59分前〜\)"),
            (120, r"\(2時間前〜\)"),
            (180, r"\(3時間前〜\)"),
            (240, r"\(4時間前〜\)"),
        ],
    )
    def test_format_based_on_elapsed_time(self, minutes_ago, expected_pattern):
        """経過時間に応じた表示形式"""
        from weather_display.panel.rain_fall import gen_start_text

        start_time = self._create_time_ago(minutes_ago)
        result = gen_start_text(start_time)

        assert re.match(expected_pattern, result), f"Expected pattern {expected_pattern}, got {result}"

    def test_less_than_one_hour_shows_minutes(self):
        """1時間未満は分で表示"""
        from weather_display.panel.rain_fall import gen_start_text

        start_time = self._create_time_ago(45)
        result = gen_start_text(start_time)

        assert "分前" in result
        assert "時間" not in result

    def test_between_one_and_two_hours_shows_hour_and_minutes(self):
        """1-2時間は「1時間○分前」で表示"""
        from weather_display.panel.rain_fall import gen_start_text

        start_time = self._create_time_ago(75)
        result = gen_start_text(start_time)

        assert "1時間" in result
        assert "分前" in result

    def test_two_hours_or_more_shows_hours_only(self):
        """2時間以上は「○時間前」で表示"""
        from weather_display.panel.rain_fall import gen_start_text

        start_time = self._create_time_ago(150)
        result = gen_start_text(start_time)

        assert "時間前" in result
        # 分は含まれない
        assert "分" not in result or result.endswith("時間前〜)")

    def test_result_format_has_parentheses(self):
        """結果は括弧で囲まれていること"""
        from weather_display.panel.rain_fall import gen_start_text

        start_time = self._create_time_ago(30)
        result = gen_start_text(start_time)

        assert result.startswith("(")
        assert result.endswith(")")
