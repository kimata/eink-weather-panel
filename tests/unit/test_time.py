#!/usr/bin/env python3
# ruff: noqa: S101
"""
weather_display/panel/time.py のテスト
"""

import weather_display.panel.time


class TestGetFaceMap:
    """_get_face_map 関数のテスト"""

    def test_get_face_map_returns_dict(self, config):
        """_get_face_map が dict を返す"""
        result = weather_display.panel.time._get_face_map(config.font)

        assert isinstance(result, dict)
        assert "time" in result
        assert "value" in result["time"]


class TestDrawTime:
    """_draw_time 関数のテスト"""

    def test_draw_time(self, config):
        """_draw_time が画像に描画する"""
        import PIL.Image

        img = PIL.Image.new("RGBA", (400, 200), (255, 255, 255, 0))
        face_map = weather_display.panel.time._get_face_map(config.font)

        weather_display.panel.time._draw_time(img, 300, 150, face_map["time"])

        # 画像が変更されたことを確認（透明でないピクセルが存在）
        assert img.getbbox() is not None


class TestDrawPanelTime:
    """_draw_panel_time 関数のテスト"""

    def test_draw_panel_time(self, config):
        """_draw_panel_time が画像に描画する"""
        import PIL.Image

        img = PIL.Image.new("RGBA", (config.time.panel.width, config.time.panel.height), (255, 255, 255, 0))

        weather_display.panel.time._draw_panel_time(img, config.time, config.font)

        # 画像が変更されたことを確認
        assert img.getbbox() is not None


class TestCreate:
    """create 関数のテスト"""

    def test_create_returns_image_and_duration(self, config, image_checker):
        """create が画像と処理時間を返す"""
        result = weather_display.panel.time.create(config)

        assert isinstance(result, tuple)
        assert len(result) == 2

        img, duration = result

        # 画像を検証
        image_checker.check(img, config.time.panel)

        # 処理時間が妥当
        assert isinstance(duration, float)
        assert duration >= 0

    def test_create_image_size(self, config):
        """create が正しいサイズの画像を返す"""
        img, _ = weather_display.panel.time.create(config)

        assert img.size[0] == config.time.panel.width
        assert img.size[1] == config.time.panel.height

    def test_create_image_mode(self, config):
        """create が RGBA 画像を返す"""
        img, _ = weather_display.panel.time.create(config)

        assert img.mode == "RGBA"
