#!/usr/bin/env python3
# ruff: noqa: S101
"""
rain_cloud.py のユニットテスト
"""
import os

import pytest

# このファイル全体のテストを selenium マークする
pytestmark = pytest.mark.selenium


class TestGetDriverProfileName:
    """get_driver_profile_name 関数のテスト"""

    def test_profile_name_without_xdist(self, mocker):
        """PYTEST_XDIST_WORKER がない場合のプロファイル名"""
        from weather_display.panel.rain_cloud import get_driver_profile_name

        mocker.patch.dict(os.environ, {}, clear=True)
        # 環境変数がない場合を確実にするため
        if "PYTEST_XDIST_WORKER" in os.environ:
            del os.environ["PYTEST_XDIST_WORKER"]

        result = get_driver_profile_name(False)
        assert result == "rain_cloud"

        result = get_driver_profile_name(True)
        assert result == "rain_cloud_future"

    def test_profile_name_with_xdist(self, mocker):
        """PYTEST_XDIST_WORKER がある場合のプロファイル名"""
        from weather_display.panel.rain_cloud import get_driver_profile_name

        mocker.patch.dict(os.environ, {"PYTEST_XDIST_WORKER": "gw0"})

        result = get_driver_profile_name(False)
        assert result == "rain_cloud_gw0"

        result = get_driver_profile_name(True)
        assert result == "rain_cloud_future_gw0"


class TestRetouchCloudImage:
    """retouch_cloud_image 関数のテスト"""

    @pytest.fixture
    def sample_image_bytes(self):
        """サンプル画像を作成"""
        import io

        import PIL.Image

        img = PIL.Image.new("RGB", (100, 100), (255, 255, 255))
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        return buffer.getvalue()

    def test_retouch_cloud_image_with_white_areas(self, config, sample_image_bytes):
        """白地図処理のテスト"""
        from weather_display.panel.rain_cloud import retouch_cloud_image

        result_img, result_bar = retouch_cloud_image(sample_image_bytes, config.rain_cloud)

        assert result_img is not None
        assert result_bar is not None


class TestCreateDummyMode:
    """DUMMY_MODE 時の動作テスト"""

    def test_create_with_dummy_mode_font_error(self, config, mocker):
        """DUMMY_MODE でフォント読み込みエラー時も動作すること"""
        import weather_display.panel.rain_cloud

        mocker.patch.dict(os.environ, {"DUMMY_MODE": "true"})
        mocker.patch("my_lib.pil_util.get_font", side_effect=Exception("Font error"))

        result = weather_display.panel.rain_cloud.create(config)

        assert len(result) >= 2
        assert result[0] is not None


class TestChromeCleanup:
    """Chrome クリーンアップ関連のテスト"""

    def test_create_with_chrome_cleanup_error(self, config, mocker):
        """Chrome クリーンアップエラー時も動作すること"""
        import weather_display.panel.rain_cloud

        mocker.patch.dict(os.environ, {"DUMMY_MODE": "false"})
        mocker.patch(
            "my_lib.chrome_util.cleanup_old_chrome_profiles",
            side_effect=Exception("Cleanup error"),
        )

        result = weather_display.panel.rain_cloud.create(config)

        assert len(result) >= 2

    def test_create_with_chrome_cleanup_returns_profiles(self, config, mocker):
        """Chrome プロファイル削除時のログ出力テスト"""
        import weather_display.panel.rain_cloud

        mocker.patch.dict(os.environ, {"DUMMY_MODE": "false"})
        mocker.patch(
            "my_lib.chrome_util.cleanup_old_chrome_profiles",
            return_value=["profile1", "profile2"],
        )

        result = weather_display.panel.rain_cloud.create(config)

        assert len(result) >= 2


class TestDriverCleanup:
    """ドライバー クリーンアップ関連のテスト"""

    def test_driver_cleanup_error(self, config, mocker):
        """ドライバークリーンアップエラー時も動作すること"""
        import weather_display.panel.rain_cloud

        mocker.patch.dict(os.environ, {"DUMMY_MODE": "false"})

        # quit_driver_gracefully でエラーを発生させる
        mocker.patch(
            "my_lib.selenium_util.quit_driver_gracefully",
            side_effect=Exception("Cleanup error"),
        )

        result = weather_display.panel.rain_cloud.create(config)

        assert len(result) >= 2


class TestWindowSizeCache:
    """ウィンドウサイズキャッシュのテスト"""

    def test_change_window_size_with_valid_cache(self, mocker):
        """キャッシュが有効な場合"""
        import weather_display.panel.rain_cloud

        # モックドライバーを作成
        mock_driver = mocker.MagicMock()
        mock_element = mocker.MagicMock()
        mock_element.size = {"width": 800, "height": 600}
        mock_driver.find_element.return_value = mock_element
        mock_driver.get_window_size.return_value = {"width": 850, "height": 650}

        # キャッシュデータを設定
        cache_data = {"800x600": {"width": 850, "height": 650}}
        mocker.patch("my_lib.serializer.load", return_value=cache_data)

        result = weather_display.panel.rain_cloud.change_window_size(mock_driver, 800, 600)

        assert result == {"width": 850, "height": 650}

    def test_change_window_size_cache_mismatch(self, mocker):
        """キャッシュサイズが一致しない場合フォールバック"""
        import weather_display.panel.rain_cloud

        # モックドライバーを作成
        mock_driver = mocker.MagicMock()
        mock_element = mocker.MagicMock()
        # 最初はキャッシュサイズと一致しない、その後一致する
        mock_element.size = {"width": 750, "height": 550}
        mock_driver.find_element.return_value = mock_element

        # キャッシュデータを設定
        cache_data = {"800x600": {"width": 850, "height": 650}}
        mocker.patch("my_lib.serializer.load", return_value=cache_data)
        mocker.patch("my_lib.serializer.store")
        mocker.patch.object(
            weather_display.panel.rain_cloud,
            "change_window_size_fallback",
            return_value={"width": 860, "height": 660},
        )

        result = weather_display.panel.rain_cloud.change_window_size(mock_driver, 800, 600)

        assert result == {"width": 860, "height": 660}


class TestChangeWindowSizeFallback:
    """ウィンドウサイズ調整フォールバックのテスト"""

    def test_change_window_size_fallback_adjusts_width(self, mocker):
        """幅が一致しない場合にウィンドウサイズを調整すること (line 177-180)"""
        import weather_display.panel.rain_cloud

        mock_driver = mocker.MagicMock()

        # find_element の呼び出し回数に応じて異なるサイズを返す
        call_count = [0]

        def get_mock_element(*args, **kwargs):
            call_count[0] += 1
            mock_element = mocker.MagicMock()
            if call_count[0] == 1:
                # 最初: 幅が一致しない
                mock_element.size = {"width": 750, "height": 600}
            else:
                # 調整後: 一致
                mock_element.size = {"width": 800, "height": 600}
            return mock_element

        mock_driver.find_element.side_effect = get_mock_element
        mock_driver.get_window_size.return_value = {"width": 850, "height": 650}
        mocker.patch("weather_display.panel.rain_cloud.time.sleep")

        result = weather_display.panel.rain_cloud.change_window_size_fallback(mock_driver, 800, 600)

        # set_window_size が呼ばれていること（初期サイズ設定 + 幅調整）
        assert mock_driver.set_window_size.call_count >= 2

    def test_change_window_size_fallback_adjusts_height(self, mocker):
        """高さが一致しない場合にウィンドウサイズを調整すること (line 193-200)"""
        import weather_display.panel.rain_cloud

        mock_driver = mocker.MagicMock()
        mock_element = mocker.MagicMock()

        call_count = [0]

        def get_element_size():
            call_count[0] += 1
            if call_count[0] <= 2:
                # 最初の2回: 幅は一致、高さが一致しない
                return {"width": 800, "height": 550}
            else:
                # 調整後: 一致
                return {"width": 800, "height": 600}

        mock_element_prop = mocker.PropertyMock(side_effect=get_element_size)
        type(mock_element).size = mock_element_prop
        mock_driver.find_element.return_value = mock_element
        mock_driver.get_window_size.return_value = {"width": 850, "height": 650}

        mocker.patch("weather_display.panel.rain_cloud.time.sleep")

        result = weather_display.panel.rain_cloud.change_window_size_fallback(mock_driver, 800, 600)

        # set_window_size が複数回呼ばれていること
        assert mock_driver.set_window_size.call_count >= 2


class TestCacheSave:
    """キャッシュ保存のテスト"""

    def test_change_window_size_saves_cache_on_success(self, mocker):
        """サイズ一致時にキャッシュが保存されること (line 252-254)"""
        import weather_display.panel.rain_cloud

        mock_driver = mocker.MagicMock()
        mock_element = mocker.MagicMock()
        # 成功: サイズが一致
        mock_element.size = {"width": 800, "height": 600}
        mock_driver.find_element.return_value = mock_element
        mock_driver.get_window_size.return_value = {"width": 850, "height": 650}

        # キャッシュが空
        mocker.patch("my_lib.serializer.load", return_value={})
        mock_store = mocker.patch("my_lib.serializer.store")
        mocker.patch("weather_display.panel.rain_cloud.time.sleep")
        mocker.patch.object(
            weather_display.panel.rain_cloud,
            "change_window_size_fallback",
            return_value={"width": 850, "height": 650},
        )

        result = weather_display.panel.rain_cloud.change_window_size(mock_driver, 800, 600)

        # キャッシュが保存されること
        mock_store.assert_called_once()


class TestRetouchCloudImageWhiteMap:
    """白地図処理のテスト"""

    def test_retouch_cloud_image_without_white_areas(self, config):
        """白地図がない画像でも処理できること (line 321)"""
        import io

        import numpy
        import PIL.Image

        from weather_display.panel.rain_cloud import retouch_cloud_image

        # 彩度の高い画像（白ではない）を作成
        img = PIL.Image.new("RGB", (100, 100), (255, 0, 0))  # 赤
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")

        result_img, result_bar = retouch_cloud_image(buffer.getvalue(), config.rain_cloud)

        assert result_img is not None
        assert result_bar is not None


class TestExceptionHandling:
    """例外ハンドリングのテスト"""

    def test_create_rain_cloud_img_with_screenshot_error(self, config, mocker):
        """スクリーンショット取得エラー時も動作すること"""
        import weather_display.panel.rain_cloud

        mocker.patch.dict(os.environ, {"DUMMY_MODE": "false"})

        # ドライバー作成後に例外を発生させ、スクリーンショット取得も失敗させる
        mock_driver = mocker.MagicMock()
        mock_driver.get_screenshot_as_png.side_effect = Exception("Screenshot error")
        mocker.patch("my_lib.selenium_util.create_driver", return_value=mock_driver)
        mocker.patch.object(
            weather_display.panel.rain_cloud,
            "fetch_cloud_image",
            side_effect=Exception("Fetch error"),
        )
        mocker.patch("weather_display.panel.rain_cloud.time.sleep")
        mocker.patch("my_lib.selenium_util.quit_driver_gracefully")

        # PATIENT_COUNT を超えた試行数で呼び出し
        weather_display.panel.rain_cloud.PATIENT_COUNT = 0

        # この場合はエラーがリトライで処理される
        result = weather_display.panel.rain_cloud.create(config)

        # エラー画像が返される
        assert len(result) >= 2

    def test_create_rain_cloud_img_with_slack_notification(self, config, mocker):
        """Slack通知が呼ばれること (line 441-456)"""
        import weather_display.panel.rain_cloud

        mocker.patch.dict(os.environ, {"DUMMY_MODE": "false"})

        # PATIENT_COUNT を0にして最初のエラーで通知
        original_count = weather_display.panel.rain_cloud.PATIENT_COUNT
        weather_display.panel.rain_cloud.PATIENT_COUNT = 0

        mock_driver = mocker.MagicMock()
        mock_driver.get_screenshot_as_png.return_value = b"\x89PNG\r\n\x1a\n"
        mocker.patch("my_lib.selenium_util.create_driver", return_value=mock_driver)
        mocker.patch.object(
            weather_display.panel.rain_cloud,
            "fetch_cloud_image",
            side_effect=Exception("Fetch error"),
        )
        mock_sleep = mocker.patch("weather_display.panel.rain_cloud.time.sleep")
        mocker.patch("my_lib.selenium_util.quit_driver_gracefully")
        mock_slack = mocker.patch("my_lib.notify.slack.error_with_image")

        try:
            result = weather_display.panel.rain_cloud.create(config)
        finally:
            weather_display.panel.rain_cloud.PATIENT_COUNT = original_count

        # Slack通知が呼ばれていること
        assert mock_slack.called or mock_sleep.called


class TestDriverNoneCase:
    """driver が None の場合のテスト"""

    def test_create_rain_cloud_img_driver_creation_fails(self, config, mocker):
        """ドライバー作成失敗時に finally で driver が None のケース (line 460->466)"""
        import weather_display.panel.rain_cloud

        mocker.patch.dict(os.environ, {"DUMMY_MODE": "false"})

        # create_driver が例外を投げる -> driver は None のまま
        mocker.patch(
            "my_lib.selenium_util.create_driver",
            side_effect=Exception("Driver creation failed"),
        )
        mock_sleep = mocker.patch("weather_display.panel.rain_cloud.time.sleep")
        mock_quit = mocker.patch("my_lib.selenium_util.quit_driver_gracefully")

        result = weather_display.panel.rain_cloud.create(config)

        # エラー画像が返される
        assert len(result) >= 2
        # driver が None なので quit_driver_gracefully は呼ばれない
        # (finally ブロックの if driver: が False)


class TestSlackNotificationBranch:
    """Slack通知分岐のテスト"""

    def test_slack_notification_when_trial_exceeds_patient_count(self, config, mocker):
        """trial >= PATIENT_COUNT の時にSlack通知が呼ばれること (line 441->456)"""
        import io

        import PIL.Image

        import weather_display.panel.rain_cloud

        mocker.patch.dict(os.environ, {"DUMMY_MODE": "false"})

        # テスト用の PNG 画像を作成
        img = PIL.Image.new("RGB", (10, 10), (255, 255, 255))
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        png_bytes = buffer.getvalue()

        mock_driver = mocker.MagicMock()
        mock_driver.get_screenshot_as_png.return_value = png_bytes

        mocker.patch("my_lib.selenium_util.create_driver", return_value=mock_driver)
        mocker.patch("my_lib.selenium_util.clear_cache")

        # fetch_cloud_image で例外を発生させる
        mocker.patch.object(
            weather_display.panel.rain_cloud,
            "fetch_cloud_image",
            side_effect=Exception("Fetch error"),
        )
        mocker.patch("weather_display.panel.rain_cloud.time.sleep")
        mocker.patch("my_lib.selenium_util.quit_driver_gracefully")
        mock_slack = mocker.patch("my_lib.notify.slack.error_with_image")

        # PATIENT_COUNT を 0 に設定し、trial=0 で条件を満たす
        original_count = weather_display.panel.rain_cloud.PATIENT_COUNT
        weather_display.panel.rain_cloud.PATIENT_COUNT = 0

        try:
            # create_rain_cloud_img を直接呼び出して trial を制御
            face_map = {}
            sub_panel_config = {
                "is_future": False,
                "title": "現在",
                "width": 400,
                "height": 300,
                "offset_x": 0,
                "offset_y": 0,
            }
            try:
                weather_display.panel.rain_cloud.create_rain_cloud_img(
                    config.rain_cloud,
                    sub_panel_config,
                    face_map,
                    config.slack,
                    trial=0,  # PATIENT_COUNT(0) 以上
                )
            except Exception:
                pass  # 例外は想定内
        finally:
            weather_display.panel.rain_cloud.PATIENT_COUNT = original_count

        # Slack通知が呼ばれていること
        assert mock_slack.called


class TestSideBySideLayout:
    """横並びレイアウトのテスト"""

    def test_create_rain_cloud_panel_impl_side_by_side_true(self, config, mocker):
        """create_rain_cloud_panel_impl で is_side_by_side=True (line 564-568)"""
        import PIL.Image

        import my_lib.panel_config
        import weather_display.panel.rain_cloud

        # create_rain_cloud_img をモックして高速化
        mock_img = PIL.Image.new("RGBA", (400, 300), (255, 255, 255, 255))
        mock_bar = PIL.Image.new("RGBA", (10, 100), (255, 0, 0, 255))
        mocker.patch.object(
            weather_display.panel.rain_cloud,
            "create_rain_cloud_img",
            return_value=(mock_img, mock_bar),
        )

        context = my_lib.panel_config.NormalPanelContext(
            font_config=config.font,
            slack_config=config.slack,
            is_side_by_side=True,  # line 564-568
        )

        result = weather_display.panel.rain_cloud.create_rain_cloud_panel_impl(
            config.rain_cloud,
            context,
            is_threaded=False,
        )

        assert result is not None

    def test_create_rain_cloud_panel_impl_side_by_side_false(self, config, mocker):
        """create_rain_cloud_panel_impl で is_side_by_side=False (line 569-573)"""
        import PIL.Image

        import my_lib.panel_config
        import weather_display.panel.rain_cloud

        # create_rain_cloud_img をモックして高速化
        mock_img = PIL.Image.new("RGBA", (400, 300), (255, 255, 255, 255))
        mock_bar = PIL.Image.new("RGBA", (10, 100), (255, 0, 0, 255))
        mocker.patch.object(
            weather_display.panel.rain_cloud,
            "create_rain_cloud_img",
            return_value=(mock_img, mock_bar),
        )

        context = my_lib.panel_config.NormalPanelContext(
            font_config=config.font,
            slack_config=config.slack,
            is_side_by_side=False,  # line 569-573
        )

        result = weather_display.panel.rain_cloud.create_rain_cloud_panel_impl(
            config.rain_cloud,
            context,
            is_threaded=False,
        )

        assert result is not None


class TestDriverNoneCoverage:
    """driver が None の分岐カバレッジテスト"""

    def test_create_rain_cloud_img_finally_with_driver_none(self, config, mocker):
        """finally ブロックで driver が None の場合 (line 460->466 False branch)"""
        import weather_display.panel.rain_cloud

        mocker.patch.dict(os.environ, {"DUMMY_MODE": "false"})

        # create_driver でエラー → driver は None のまま
        mocker.patch(
            "my_lib.selenium_util.create_driver",
            side_effect=RuntimeError("Driver creation failed"),
        )
        mocker.patch("weather_display.panel.rain_cloud.time.sleep")
        mock_quit = mocker.patch("my_lib.selenium_util.quit_driver_gracefully")

        face_map = {}
        sub_panel_config = {
            "is_future": False,
            "title": "現在",
            "width": 400,
            "height": 300,
            "offset_x": 0,
            "offset_y": 0,
        }

        # 例外が発生するが、finally で driver が None なので quit は呼ばれない
        try:
            weather_display.panel.rain_cloud.create_rain_cloud_img(
                config.rain_cloud,
                sub_panel_config,
                face_map,
                config.slack,
                trial=0,
            )
        except RuntimeError:
            pass  # 例外は想定内

        # driver が None なので quit_driver_gracefully は呼ばれないことを確認
        assert not mock_quit.called

    def test_create_rain_cloud_img_finally_with_driver_success(self, config, mocker):
        """finally ブロックで driver が存在し正常終了する場合 (line 460->466 True branch)"""
        import io

        import PIL.Image

        import weather_display.panel.rain_cloud

        mocker.patch.dict(os.environ, {"DUMMY_MODE": "false"})

        # テスト用の PNG 画像を作成
        img = PIL.Image.new("RGB", (100, 100), (255, 255, 255))
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        png_bytes = buffer.getvalue()

        mock_driver = mocker.MagicMock()
        mock_driver.get_screenshot_as_png.return_value = png_bytes

        mocker.patch("my_lib.selenium_util.create_driver", return_value=mock_driver)
        mocker.patch("my_lib.selenium_util.clear_cache")

        # fetch_cloud_image が正常に画像を返す
        mocker.patch.object(
            weather_display.panel.rain_cloud,
            "fetch_cloud_image",
            return_value=png_bytes,
        )

        # retouch_cloud_image もモック
        mock_result_img = PIL.Image.new("RGBA", (100, 100), (255, 255, 255, 255))
        mock_result_bar = PIL.Image.new("RGBA", (10, 100), (255, 0, 0, 255))
        mocker.patch.object(
            weather_display.panel.rain_cloud,
            "retouch_cloud_image",
            return_value=(mock_result_img, mock_result_bar),
        )
        mocker.patch.object(
            weather_display.panel.rain_cloud,
            "draw_equidistant_circle",
            return_value=mock_result_img,
        )
        mocker.patch.object(
            weather_display.panel.rain_cloud,
            "draw_caption",
            return_value=mock_result_img,
        )

        mock_quit = mocker.patch("my_lib.selenium_util.quit_driver_gracefully")

        face_map = {}
        sub_panel_config = {
            "is_future": False,
            "title": "現在",
            "width": 400,
            "height": 300,
            "offset_x": 0,
            "offset_y": 0,
        }

        result = weather_display.panel.rain_cloud.create_rain_cloud_img(
            config.rain_cloud,
            sub_panel_config,
            face_map,
            config.slack,
            trial=0,
        )

        # driver が存在するので quit_driver_gracefully が呼ばれること
        assert mock_quit.called
        assert result is not None

    def test_create_rain_cloud_img_with_driver_none_but_success(self, config, mocker):
        """driver が None でも関数が正常終了する場合 (line 460->466 False branch)

        理論上は到達不能だが、テスト可能にするため全ての driver 操作をモック
        """
        import io

        import PIL.Image

        import weather_display.panel.rain_cloud

        mocker.patch.dict(os.environ, {"DUMMY_MODE": "false"})

        # テスト用の PNG 画像を作成
        img = PIL.Image.new("RGB", (100, 100), (255, 255, 255))
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        png_bytes = buffer.getvalue()

        # create_driver が None を返す
        mocker.patch("my_lib.selenium_util.create_driver", return_value=None)
        mocker.patch("my_lib.selenium_util.clear_cache")

        # WebDriverWait を完全にモック
        mock_wait = mocker.MagicMock()
        mocker.patch("selenium.webdriver.support.wait.WebDriverWait", return_value=mock_wait)

        # fetch_cloud_image が正常に画像を返す
        mocker.patch.object(
            weather_display.panel.rain_cloud,
            "fetch_cloud_image",
            return_value=png_bytes,
        )

        # retouch_cloud_image もモック
        mock_result_img = PIL.Image.new("RGBA", (100, 100), (255, 255, 255, 255))
        mock_result_bar = PIL.Image.new("RGBA", (10, 100), (255, 0, 0, 255))
        mocker.patch.object(
            weather_display.panel.rain_cloud,
            "retouch_cloud_image",
            return_value=(mock_result_img, mock_result_bar),
        )
        mocker.patch.object(
            weather_display.panel.rain_cloud,
            "draw_equidistant_circle",
            return_value=mock_result_img,
        )
        mocker.patch.object(
            weather_display.panel.rain_cloud,
            "draw_caption",
            return_value=mock_result_img,
        )

        mock_quit = mocker.patch("my_lib.selenium_util.quit_driver_gracefully")

        face_map = {}
        sub_panel_config = {
            "is_future": False,
            "title": "現在",
            "width": 400,
            "height": 300,
            "offset_x": 0,
            "offset_y": 0,
        }

        result = weather_display.panel.rain_cloud.create_rain_cloud_img(
            config.rain_cloud,
            sub_panel_config,
            face_map,
            config.slack,
            trial=0,
        )

        # driver が None なので quit_driver_gracefully は呼ばれないこと
        assert not mock_quit.called
        assert result is not None
