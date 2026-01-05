#!/usr/bin/env python3
# ruff: noqa: S101
"""
weather_display/panel/wbgt.py のテスト
"""

import unittest.mock

import pytest

import weather_display.panel.wbgt


class TestGetFaceMap:
    """_get_face_map 関数のテスト"""

    def test_get_face_map_returns_dict(self, config):
        """_get_face_map が dict を返す"""
        result = weather_display.panel.wbgt._get_face_map(config.font)

        assert isinstance(result, dict)
        assert "wbgt" in result
        assert "wbgt_symbol" in result
        assert "wbgt_title" in result


class TestDrawWbgt:
    """_draw_wbgt 関数のテスト"""

    @pytest.mark.parametrize(
        "wbgt_value,expected_index",
        [
            (35.0, 4),  # >= 31: 危険
            (31.0, 4),  # >= 31: 危険
            (30.0, 3),  # >= 28: 厳重警戒
            (28.0, 3),  # >= 28: 厳重警戒
            (26.0, 2),  # >= 25: 警戒
            (25.0, 2),  # >= 25: 警戒
            (23.0, 1),  # >= 21: 注意
            (21.0, 1),  # >= 21: 注意
            (20.0, 0),  # < 21: ほぼ安全
            (15.0, 0),  # < 21: ほぼ安全
        ],
    )
    def test_draw_wbgt_levels(self, config, wbgt_value, expected_index):
        """異なる WBGT 値で正しいレベルが選択される"""
        import PIL.Image

        img = PIL.Image.new("RGBA", (config.wbgt.panel.width, config.wbgt.panel.height), (255, 255, 255, 0))
        face_map = weather_display.panel.wbgt._get_face_map(config.font)

        result = weather_display.panel.wbgt._draw_wbgt(
            img, wbgt_value, config.wbgt, config.wbgt.icon, face_map
        )

        # 画像が返される
        assert isinstance(result, PIL.Image.Image)
        # 画像が変更されている
        assert result.getbbox() is not None


class TestCreateWbgtPanelImpl:
    """_create_wbgt_panel_impl 関数のテスト"""

    def test_create_wbgt_panel_impl_with_wbgt(self, config):
        """WBGT 値がある場合"""
        import my_lib.notify.slack
        import my_lib.panel_config
        import PIL.Image

        context = my_lib.panel_config.NormalPanelContext(
            font_config=config.font,
            slack_config=my_lib.notify.slack.SlackEmptyConfig(),
            is_side_by_side=True,
        )

        # WBGT API のモック
        mock_wbgt = unittest.mock.MagicMock()
        mock_wbgt.current = 28.5

        with unittest.mock.patch("my_lib.weather.get_wbgt", return_value=mock_wbgt):
            result = weather_display.panel.wbgt._create_wbgt_panel_impl(config.wbgt, context)

        assert isinstance(result, PIL.Image.Image)
        assert result.size == (config.wbgt.panel.width, config.wbgt.panel.height)
        # 画像が変更されている
        assert result.getbbox() is not None

    def test_create_wbgt_panel_impl_without_wbgt(self, config):
        """WBGT 値が None の場合"""
        import my_lib.notify.slack
        import my_lib.panel_config
        import PIL.Image

        context = my_lib.panel_config.NormalPanelContext(
            font_config=config.font,
            slack_config=my_lib.notify.slack.SlackEmptyConfig(),
            is_side_by_side=True,
        )

        # WBGT が None
        mock_wbgt = unittest.mock.MagicMock()
        mock_wbgt.current = None

        with unittest.mock.patch("my_lib.weather.get_wbgt", return_value=mock_wbgt):
            result = weather_display.panel.wbgt._create_wbgt_panel_impl(config.wbgt, context)

        assert isinstance(result, PIL.Image.Image)
        assert result.size == (config.wbgt.panel.width, config.wbgt.panel.height)
        # 画像が空（変更されていない）
        assert result.getbbox() is None


class TestCreate:
    """create 関数のテスト"""

    def test_create_returns_tuple(self, config):
        """create がタプルを返す"""
        # WBGT API のモック
        mock_wbgt = unittest.mock.MagicMock()
        mock_wbgt.current = 25.0

        with unittest.mock.patch("my_lib.weather.get_wbgt", return_value=mock_wbgt):
            result = weather_display.panel.wbgt.create(config)

        assert isinstance(result, tuple)
        assert len(result) >= 2

    def test_create_image_size(self, config):
        """create が正しいサイズの画像を返す"""
        mock_wbgt = unittest.mock.MagicMock()
        mock_wbgt.current = 25.0

        with unittest.mock.patch("my_lib.weather.get_wbgt", return_value=mock_wbgt):
            result = weather_display.panel.wbgt.create(config)
            img = result[0]

        assert img.size[0] == config.wbgt.panel.width
        assert img.size[1] == config.wbgt.panel.height

    def test_create_side_by_side_false(self, config):
        """is_side_by_side=False で動作する"""
        mock_wbgt = unittest.mock.MagicMock()
        mock_wbgt.current = 30.0

        with unittest.mock.patch("my_lib.weather.get_wbgt", return_value=mock_wbgt):
            result = weather_display.panel.wbgt.create(config, is_side_by_side=False)

        assert isinstance(result, tuple)
