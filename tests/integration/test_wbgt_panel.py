#!/usr/bin/env python3
# ruff: noqa: S101
"""
WBGT パネルの統合テスト
"""
import datetime
import zoneinfo

import my_lib.weather
import pytest


class TestWbgtPanel:
    """WBGT パネルのテスト"""

    def test_wbgt_panel_create(self, config, image_checker):
        """WBGT パネルを生成できること"""
        import weather_display.panel.wbgt

        result = weather_display.panel.wbgt.create(config)

        assert len(result) >= 2
        img = result[0]
        assert img is not None
        image_checker.check(img, config.wbgt.panel)

    def test_wbgt_panel_create_not_side_by_side(self, config, image_checker):
        """横並びでない WBGT パネルを生成できること"""
        import weather_display.panel.wbgt

        result = weather_display.panel.wbgt.create(config, is_side_by_side=False)

        assert len(result) >= 2
        img = result[0]
        assert img is not None


class TestWbgtPanelVariations:
    """WBGT パネルの各レベルテスト"""

    @pytest.fixture
    def mock_wbgt_data(self, mocker):
        """WBGTデータのモック"""

        class MockWbgtInfo:
            def __init__(self, current=32):
                self.current = current
                self.daily = type(
                    "obj",
                    (object,),
                    {"today": list(range(18, 34, 2)), "tommorow": list(range(18, 34, 2))},
                )()

        return MockWbgtInfo

    @pytest.mark.parametrize("wbgt_value", [20, 22, 24, 26, 28, 30, 32])
    def test_wbgt_panel_various_levels(self, config, image_checker, mocker, mock_wbgt_data, wbgt_value):
        """各WBGT値で正しくパネルを生成できること"""
        import weather_display.panel.wbgt

        mocker.patch.object(my_lib.weather, "get_wbgt", return_value=mock_wbgt_data(wbgt_value))

        result = weather_display.panel.wbgt.create(config)

        assert len(result) >= 2
        img = result[0]
        assert img is not None
        image_checker.check(img, config.wbgt.panel, wbgt_value)

    def test_wbgt_panel_level_0(self, config, image_checker, mocker, mock_wbgt_data):
        """WBGT 21未満（安全レベル）で正しく描画されること"""
        import weather_display.panel.wbgt

        mocker.patch.object(my_lib.weather, "get_wbgt", return_value=mock_wbgt_data(15))

        result = weather_display.panel.wbgt.create(config)
        assert result[0] is not None

    def test_wbgt_panel_level_1(self, config, image_checker, mocker, mock_wbgt_data):
        """WBGT 21-25（注意レベル）で正しく描画されること"""
        import weather_display.panel.wbgt

        mocker.patch.object(my_lib.weather, "get_wbgt", return_value=mock_wbgt_data(23))

        result = weather_display.panel.wbgt.create(config)
        assert result[0] is not None

    def test_wbgt_panel_level_2(self, config, image_checker, mocker, mock_wbgt_data):
        """WBGT 25-28（警戒レベル）で正しく描画されること"""
        import weather_display.panel.wbgt

        mocker.patch.object(my_lib.weather, "get_wbgt", return_value=mock_wbgt_data(26))

        result = weather_display.panel.wbgt.create(config)
        assert result[0] is not None

    def test_wbgt_panel_level_3(self, config, image_checker, mocker, mock_wbgt_data):
        """WBGT 28-31（厳重警戒レベル）で正しく描画されること"""
        import weather_display.panel.wbgt

        mocker.patch.object(my_lib.weather, "get_wbgt", return_value=mock_wbgt_data(29))

        result = weather_display.panel.wbgt.create(config)
        assert result[0] is not None

    def test_wbgt_panel_level_4(self, config, image_checker, mocker, mock_wbgt_data):
        """WBGT 31以上（危険レベル）で正しく描画されること"""
        import weather_display.panel.wbgt

        mocker.patch.object(my_lib.weather, "get_wbgt", return_value=mock_wbgt_data(35))

        result = weather_display.panel.wbgt.create(config)
        assert result[0] is not None


class TestWbgtPanelError:
    """WBGT パネルのエラーハンドリングテスト"""

    def test_wbgt_panel_fetch_error(self, config, image_checker, mocker, time_machine):
        """データ取得エラー時にエラー画像を返すこと"""
        import weather_display.panel.wbgt

        tz = zoneinfo.ZoneInfo("Asia/Tokyo")
        time_machine.move_to(datetime.datetime.now(tz).replace(month=8))

        mocker.patch("my_lib.weather.fetch_page", side_effect=RuntimeError())

        result = weather_display.panel.wbgt.create(config)

        assert len(result) == 3
        assert "Traceback" in result[2]

    def test_wbgt_panel_empty_data(self, config, image_checker, mocker):
        """空データ時に空画像を返すこと"""
        import weather_display.panel.wbgt

        mocker.patch("lxml.html.HtmlElement.xpath", return_value=[])

        result = weather_display.panel.wbgt.create(config)

        # ページフォーマットエラーでも処理が継続すること
        assert len(result) >= 2

    def test_wbgt_panel_none_wbgt(self, config, image_checker, mocker):
        """WBGT値がNoneの場合に空画像を返すこと"""
        import weather_display.panel.wbgt

        class MockWbgtInfo:
            current = None
            daily = type("obj", (object,), {"today": [], "tommorow": []})()

        mocker.patch.object(my_lib.weather, "get_wbgt", return_value=MockWbgtInfo())

        result = weather_display.panel.wbgt.create(config)

        assert result[0] is not None
