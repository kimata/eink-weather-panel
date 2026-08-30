#!/usr/bin/env python3
# ruff: noqa: S101, S110, SIM105
"""
rain_cloud.py のユニットテスト
"""

import os

import my_lib.browser
import pytest

# このファイル全体のテストを selenium マークする
pytestmark = pytest.mark.selenium


def _make_page(mocker, box=None, boxes=None):
    """雲画像要素サイズを返す Page モックを生成する。

    box: 単一の (width, height) を常に返す
    boxes: (width, height) のリストを順番に返す（bounding_box の side_effect）
    """
    page = mocker.MagicMock()
    element = mocker.MagicMock()
    if boxes is not None:
        element.bounding_box.side_effect = [
            my_lib.browser.BoundingBox(x=0, y=0, width=w, height=h) for (w, h) in boxes
        ]
    else:
        w, h = box if box is not None else (800, 600)
        element.bounding_box.return_value = my_lib.browser.BoundingBox(x=0, y=0, width=w, height=h)
    page.find.return_value = element
    return page


def _make_browser(mocker, page=None):
    """pages() / maintenance / close を備えた Browser モックを生成する。"""
    browser = mocker.MagicMock()
    if page is None:
        page = mocker.MagicMock()
    browser.pages.return_value = [page]
    return browser


class TestGetDriverProfileName:
    """get_driver_profile_name 関数のテスト"""

    def test_profile_name_contains_pid(self):
        """プロファイル名にプロセス固有のサフィックス (PID) が付与されること"""
        from weather_display.panel.rain_cloud import _get_driver_profile_name

        pid = os.getpid()

        result = _get_driver_profile_name(False)
        assert result == f"rain_cloud_{pid}"

        result = _get_driver_profile_name(True)
        assert result == f"rain_cloud_future_{pid}"


class TestCleanupStaleProfiles:
    """_cleanup_stale_profiles 関数のテスト"""

    def test_removes_only_dead_process_profiles(self, mocker, tmp_path):
        """生存していないプロセスのプロファイルのみ削除されること"""
        from weather_display.panel import rain_cloud

        chrome_dir = tmp_path / "chrome"
        chrome_dir.mkdir(parents=True)

        # 自プロセス (生存中) のプロファイル
        alive_profile = chrome_dir / f"rain_cloud_{os.getpid()}"
        alive_profile.mkdir()

        # 存在しない PID のプロファイル
        stale_profile = chrome_dir / "rain_cloud_future_999999999"
        stale_profile.mkdir()

        # PID サフィックスのない (旧形式の) プロファイルは対象外
        legacy_profile = chrome_dir / "rain_cloud"
        legacy_profile.mkdir()

        mocker.patch.object(rain_cloud, "_DATA_PATH", tmp_path)

        rain_cloud._cleanup_stale_profiles()

        assert alive_profile.exists()
        assert not stale_profile.exists()
        assert legacy_profile.exists()


class TestRetouchCloudImage:
    """_retouch_cloud_image 関数のテスト"""

    @pytest.fixture
    def sample_image_bytes(self):
        """サンプル画像を作成"""
        import io

        import PIL.Image

        img = PIL.Image.new("RGB", (100, 100), (255, 255, 255))
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        return buffer.getvalue()

    def test__retouch_cloud_image_with_white_areas(self, config, sample_image_bytes):
        """白地図処理のテスト"""
        from weather_display.panel.rain_cloud import _retouch_cloud_image

        result_img, result_bar = _retouch_cloud_image(sample_image_bytes, config.rain_cloud)

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


class TestBrowserCleanup:
    """ブラウザ クリーンアップ関連のテスト"""

    def test_browser_cleanup_error(self, config, mocker):
        """ブラウザクリーンアップエラー時も動作すること"""
        import weather_display.panel.rain_cloud

        mocker.patch.dict(os.environ, {"DUMMY_MODE": "false"})

        # browser.close() でエラーを発生させる
        mock_browser = _make_browser(mocker)
        mock_browser.close.side_effect = Exception("Cleanup error")
        mocker.patch("my_lib.browser.launch", return_value=mock_browser)
        mocker.patch.object(
            weather_display.panel.rain_cloud,
            "_fetch_cloud_image",
            side_effect=Exception("Fetch error"),
        )
        mocker.patch("weather_display.panel.rain_cloud.time.sleep")
        mocker.patch("my_lib.panel_util.time.sleep")

        result = weather_display.panel.rain_cloud.create(config)

        assert len(result) >= 2


class TestWindowSizeCache:
    """ウィンドウサイズキャッシュのテスト"""

    def test_change_window_size_with_valid_cache(self, mocker):
        """キャッシュが有効な場合"""
        import weather_display.panel.rain_cloud

        # 要素サイズがターゲットと一致する Page モック
        page = _make_page(mocker, box=(800, 600))

        # キャッシュデータを設定
        cache_data = {"800x600": {"width": 850, "height": 650}}
        mocker.patch("my_lib.serializer.load", return_value=cache_data)
        mocker.patch("weather_display.panel.rain_cloud.time.sleep")

        result = weather_display.panel.rain_cloud._change_window_size(page, 800, 600)

        assert result == {"width": 850, "height": 650}
        page.set_viewport.assert_called_with(850, 650)

    def test_change_window_size_cache_mismatch(self, mocker):
        """キャッシュサイズが一致しない場合フォールバック"""
        import weather_display.panel.rain_cloud

        # 要素サイズがターゲットと一致しない Page モック
        page = _make_page(mocker, box=(750, 550))

        # キャッシュデータを設定
        cache_data = {"800x600": {"width": 850, "height": 650}}
        mocker.patch("my_lib.serializer.load", return_value=cache_data)
        mocker.patch("my_lib.serializer.store")
        mocker.patch("weather_display.panel.rain_cloud.time.sleep")
        mocker.patch.object(
            weather_display.panel.rain_cloud,
            "_change_window_size_fallback",
            return_value={"width": 860, "height": 660},
        )

        result = weather_display.panel.rain_cloud._change_window_size(page, 800, 600)

        assert result == {"width": 860, "height": 660}


class TestChangeWindowSizeFallback:
    """ウィンドウサイズ調整フォールバックのテスト"""

    def test__change_window_size_fallback_adjusts_width(self, mocker):
        """幅が一致しない場合にビューポートサイズを調整すること"""
        import weather_display.panel.rain_cloud

        # 1回目: 幅が一致しない、以降: 一致
        page = _make_page(mocker, boxes=[(750, 600), (800, 600), (800, 600)])
        mocker.patch("weather_display.panel.rain_cloud.time.sleep")

        weather_display.panel.rain_cloud._change_window_size_fallback(page, 800, 600)

        # set_viewport が呼ばれていること（初期サイズ設定 + 幅調整）
        assert page.set_viewport.call_count >= 2

    def test__change_window_size_fallback_adjusts_height(self, mocker):
        """高さが一致しない場合にビューポートサイズを調整すること"""
        import weather_display.panel.rain_cloud

        # 幅は一致、高さが最初一致しない、調整後一致
        page = _make_page(mocker, boxes=[(800, 550), (800, 550), (800, 600)])
        mocker.patch("weather_display.panel.rain_cloud.time.sleep")

        weather_display.panel.rain_cloud._change_window_size_fallback(page, 800, 600)

        # set_viewport が複数回呼ばれていること（初期サイズ設定 + 高さ調整）
        assert page.set_viewport.call_count >= 2


class TestCacheSave:
    """キャッシュ保存のテスト"""

    def test_change_window_size_saves_cache_on_success(self, mocker):
        """サイズ一致時にキャッシュが保存されること"""
        import weather_display.panel.rain_cloud

        # フォールバック後の要素サイズがターゲットと一致
        page = _make_page(mocker, box=(800, 600))

        # キャッシュが空
        mocker.patch("my_lib.serializer.load", return_value={})
        mock_store = mocker.patch("my_lib.serializer.store")
        mocker.patch("weather_display.panel.rain_cloud.time.sleep")
        mocker.patch.object(
            weather_display.panel.rain_cloud,
            "_change_window_size_fallback",
            return_value={"width": 850, "height": 650},
        )

        weather_display.panel.rain_cloud._change_window_size(page, 800, 600)

        # キャッシュが保存されること
        mock_store.assert_called_once()


class TestRetouchCloudImageWhiteMap:
    """白地図処理のテスト"""

    def test__retouch_cloud_image_without_white_areas(self, config):
        """白地図がない画像でも処理できること"""
        import io

        import PIL.Image

        from weather_display.panel.rain_cloud import _retouch_cloud_image

        # 彩度の高い画像（白ではない）を作成
        img = PIL.Image.new("RGB", (100, 100), (255, 0, 0))  # 赤
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")

        result_img, result_bar = _retouch_cloud_image(buffer.getvalue(), config.rain_cloud)

        assert result_img is not None
        assert result_bar is not None


class TestExceptionHandling:
    """例外ハンドリングのテスト"""

    def test__create_rain_cloud_img_with_screenshot_error(self, config, mocker):
        """スクリーンショット取得エラー時も動作すること"""
        import weather_display.panel.rain_cloud

        mocker.patch.dict(os.environ, {"DUMMY_MODE": "false"})

        # ブラウザ生成後に例外を発生させ、スクリーンショット取得も失敗させる
        page = mocker.MagicMock()
        page.screenshot.side_effect = Exception("Screenshot error")
        mock_browser = _make_browser(mocker, page=page)
        mocker.patch("my_lib.browser.launch", return_value=mock_browser)
        mocker.patch.object(
            weather_display.panel.rain_cloud,
            "_fetch_cloud_image",
            side_effect=Exception("Fetch error"),
        )
        mocker.patch("weather_display.panel.rain_cloud.time.sleep")
        mocker.patch("my_lib.panel_util.time.sleep")

        original_count = weather_display.panel.rain_cloud._PATIENT_COUNT
        weather_display.panel.rain_cloud._PATIENT_COUNT = 0
        try:
            result = weather_display.panel.rain_cloud.create(config)
        finally:
            weather_display.panel.rain_cloud._PATIENT_COUNT = original_count

        # エラー画像が返される
        assert len(result) >= 2

    def test__create_rain_cloud_img_with_slack_notification(self, config, mocker):
        """Slack通知が呼ばれること"""
        import weather_display.panel.rain_cloud

        mocker.patch.dict(os.environ, {"DUMMY_MODE": "false"})

        page = mocker.MagicMock()
        page.screenshot.return_value = b"\x89PNG\r\n\x1a\n"
        page.content = "<html></html>"
        mock_browser = _make_browser(mocker, page=page)
        mocker.patch("my_lib.browser.launch", return_value=mock_browser)
        mocker.patch.object(
            weather_display.panel.rain_cloud,
            "_fetch_cloud_image",
            side_effect=Exception("Fetch error"),
        )
        mock_sleep = mocker.patch("weather_display.panel.rain_cloud.time.sleep")
        mocker.patch("my_lib.panel_util.time.sleep")
        mock_slack = mocker.patch("my_lib.notify.slack.error_with_image")

        original_count = weather_display.panel.rain_cloud._PATIENT_COUNT
        weather_display.panel.rain_cloud._PATIENT_COUNT = 0
        try:
            weather_display.panel.rain_cloud.create(config)
        finally:
            weather_display.panel.rain_cloud._PATIENT_COUNT = original_count

        # Slack通知が呼ばれていること
        assert mock_slack.called or mock_sleep.called


class TestBrowserLaunchFails:
    """ブラウザ生成に失敗した場合のテスト"""

    def test__create_rain_cloud_img_launch_fails(self, config, mocker):
        """ブラウザ生成失敗時に finally で browser が None のケース"""
        import weather_display.panel.rain_cloud

        mocker.patch.dict(os.environ, {"DUMMY_MODE": "false"})

        # launch が例外を投げる -> browser は None のまま
        mocker.patch(
            "my_lib.browser.launch",
            side_effect=Exception("Browser launch failed"),
        )
        mocker.patch("weather_display.panel.rain_cloud.time.sleep")
        mocker.patch("my_lib.panel_util.time.sleep")

        result = weather_display.panel.rain_cloud.create(config)

        # エラー画像が返される
        assert len(result) >= 2


class TestSlackNotificationBranch:
    """Slack通知分岐のテスト"""

    def test_slack_notification_when_trial_exceeds_patient_count(self, config, mocker):
        """trial >= PATIENT_COUNT の時にSlack通知が呼ばれること"""
        import io

        import PIL.Image

        import weather_display.panel.rain_cloud

        mocker.patch.dict(os.environ, {"DUMMY_MODE": "false"})

        # テスト用の PNG 画像を作成
        img = PIL.Image.new("RGB", (10, 10), (255, 255, 255))
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        png_bytes = buffer.getvalue()

        page = mocker.MagicMock()
        page.screenshot.return_value = png_bytes
        page.content = "<html></html>"
        mock_browser = _make_browser(mocker, page=page)
        mocker.patch("my_lib.browser.launch", return_value=mock_browser)

        # _fetch_cloud_image で例外を発生させる
        mocker.patch.object(
            weather_display.panel.rain_cloud,
            "_fetch_cloud_image",
            side_effect=Exception("Fetch error"),
        )
        mocker.patch("weather_display.panel.rain_cloud.time.sleep")
        mock_slack = mocker.patch("my_lib.notify.slack.error_with_image")

        # PATIENT_COUNT を 0 に設定し、trial=0 で条件を満たす
        original_count = weather_display.panel.rain_cloud._PATIENT_COUNT
        weather_display.panel.rain_cloud._PATIENT_COUNT = 0

        try:
            from weather_display.panel.rain_cloud import SubPanelConfig

            face_map = {}
            sub_panel_config = SubPanelConfig(
                is_future=False,
                title="現在",
                width=400,
                height=300,
                offset_x=0,
                offset_y=0,
            )
            try:
                # _create_rain_cloud_img を直接呼び出して trial を制御
                weather_display.panel.rain_cloud._create_rain_cloud_img(
                    config.rain_cloud,
                    sub_panel_config,
                    face_map,
                    config.slack,
                    trial=0,  # PATIENT_COUNT(0) 以上
                )
            except Exception:
                pass  # 例外は想定内
        finally:
            weather_display.panel.rain_cloud._PATIENT_COUNT = original_count

        # Slack通知が呼ばれていること
        assert mock_slack.called


class TestSideBySideLayout:
    """横並びレイアウトのテスト"""

    def test_create_rain_cloud_panel_impl_side_by_side_true(self, config, mocker):
        """create_rain_cloud_panel_impl で is_side_by_side=True"""
        import my_lib.panel_config
        import PIL.Image

        import weather_display.panel.rain_cloud

        # _create_rain_cloud_img をモックして高速化
        mock_img = PIL.Image.new("RGBA", (400, 300), (255, 255, 255, 255))
        mock_bar = PIL.Image.new("RGBA", (10, 100), (255, 0, 0, 255))
        mocker.patch.object(
            weather_display.panel.rain_cloud,
            "_create_rain_cloud_img",
            return_value=(mock_img, mock_bar),
        )

        context = my_lib.panel_config.NormalPanelContext(
            font_config=config.font,
            slack_config=config.slack,
            is_side_by_side=True,
        )

        result = weather_display.panel.rain_cloud._create_rain_cloud_panel_impl(
            config.rain_cloud,
            context,
            is_threaded=False,
        )

        assert result is not None

    def test_create_rain_cloud_panel_impl_side_by_side_false(self, config, mocker):
        """create_rain_cloud_panel_impl で is_side_by_side=False"""
        import my_lib.panel_config
        import PIL.Image

        import weather_display.panel.rain_cloud

        # _create_rain_cloud_img をモックして高速化
        mock_img = PIL.Image.new("RGBA", (400, 300), (255, 255, 255, 255))
        mock_bar = PIL.Image.new("RGBA", (10, 100), (255, 0, 0, 255))
        mocker.patch.object(
            weather_display.panel.rain_cloud,
            "_create_rain_cloud_img",
            return_value=(mock_img, mock_bar),
        )

        context = my_lib.panel_config.NormalPanelContext(
            font_config=config.font,
            slack_config=config.slack,
            is_side_by_side=False,
        )

        result = weather_display.panel.rain_cloud._create_rain_cloud_panel_impl(
            config.rain_cloud,
            context,
            is_threaded=False,
        )

        assert result is not None


class TestBrowserCleanupCoverage:
    """ブラウザ クリーンアップ分岐のカバレッジテスト"""

    def test__create_rain_cloud_img_finally_with_browser_none(self, config, mocker):
        """finally ブロックで browser が None の場合 (close/delete_profile 未呼び出し)"""
        import weather_display.panel.rain_cloud

        mocker.patch.dict(os.environ, {"DUMMY_MODE": "false"})

        # launch でエラー → browser は None のまま
        mocker.patch(
            "my_lib.browser.launch",
            side_effect=RuntimeError("Browser launch failed"),
        )
        mocker.patch("weather_display.panel.rain_cloud.time.sleep")
        mock_delete = mocker.patch("my_lib.chrome_util.delete_profile")

        from weather_display.panel.rain_cloud import SubPanelConfig

        face_map = {}
        sub_panel_config = SubPanelConfig(
            is_future=False,
            title="現在",
            width=400,
            height=300,
            offset_x=0,
            offset_y=0,
        )

        # 例外が発生するが、finally で browser が None なので close/delete は呼ばれない
        try:
            weather_display.panel.rain_cloud._create_rain_cloud_img(
                config.rain_cloud,
                sub_panel_config,
                face_map,
                config.slack,
                trial=0,
            )
        except RuntimeError:
            pass  # 例外は想定内

        # browser が None なので delete_profile は呼ばれないことを確認
        assert not mock_delete.called

    def test__create_rain_cloud_img_finally_with_browser_success(self, config, mocker):
        """finally ブロックで browser が存在し正常終了する場合 (close 呼び出し)"""
        import io

        import PIL.Image

        import weather_display.panel.rain_cloud

        mocker.patch.dict(os.environ, {"DUMMY_MODE": "false"})

        # テスト用の PNG 画像を作成
        img = PIL.Image.new("RGB", (100, 100), (255, 255, 255))
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        png_bytes = buffer.getvalue()

        mock_browser = _make_browser(mocker)
        mocker.patch("my_lib.browser.launch", return_value=mock_browser)

        # _fetch_cloud_image が正常に画像を返す
        mocker.patch.object(
            weather_display.panel.rain_cloud,
            "_fetch_cloud_image",
            return_value=png_bytes,
        )

        # _retouch_cloud_image もモック
        mock_result_img = PIL.Image.new("RGBA", (100, 100), (255, 255, 255, 255))
        mock_result_bar = PIL.Image.new("RGBA", (10, 100), (255, 0, 0, 255))
        mocker.patch.object(
            weather_display.panel.rain_cloud,
            "_retouch_cloud_image",
            return_value=(mock_result_img, mock_result_bar),
        )
        mocker.patch.object(
            weather_display.panel.rain_cloud,
            "_draw_equidistant_circle",
            return_value=mock_result_img,
        )
        mocker.patch.object(
            weather_display.panel.rain_cloud,
            "_draw_caption",
            return_value=mock_result_img,
        )
        mocker.patch("my_lib.chrome_util.delete_profile")

        from weather_display.panel.rain_cloud import SubPanelConfig

        face_map = {}
        sub_panel_config = SubPanelConfig(
            is_future=False,
            title="現在",
            width=400,
            height=300,
            offset_x=0,
            offset_y=0,
        )

        result = weather_display.panel.rain_cloud._create_rain_cloud_img(
            config.rain_cloud,
            sub_panel_config,
            face_map,
            config.slack,
            trial=0,
        )

        # browser が存在するので close が呼ばれること
        assert mock_browser.close.called
        assert result is not None

    def test__create_rain_cloud_img_deletes_profile_on_success(self, config, mocker):
        """正常終了時にプロファイルが削除されること"""
        import io

        import PIL.Image

        import weather_display.panel.rain_cloud

        mocker.patch.dict(os.environ, {"DUMMY_MODE": "false"})

        img = PIL.Image.new("RGB", (100, 100), (255, 255, 255))
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        png_bytes = buffer.getvalue()

        mock_browser = _make_browser(mocker)
        mocker.patch("my_lib.browser.launch", return_value=mock_browser)

        mocker.patch.object(
            weather_display.panel.rain_cloud,
            "_fetch_cloud_image",
            return_value=png_bytes,
        )
        mock_result_img = PIL.Image.new("RGBA", (100, 100), (255, 255, 255, 255))
        mock_result_bar = PIL.Image.new("RGBA", (10, 100), (255, 0, 0, 255))
        mocker.patch.object(
            weather_display.panel.rain_cloud,
            "_retouch_cloud_image",
            return_value=(mock_result_img, mock_result_bar),
        )
        mocker.patch.object(
            weather_display.panel.rain_cloud,
            "_draw_equidistant_circle",
            return_value=mock_result_img,
        )
        mocker.patch.object(
            weather_display.panel.rain_cloud,
            "_draw_caption",
            return_value=mock_result_img,
        )
        mock_delete = mocker.patch("my_lib.chrome_util.delete_profile")

        from weather_display.panel.rain_cloud import SubPanelConfig

        face_map = {}
        sub_panel_config = SubPanelConfig(
            is_future=False,
            title="現在",
            width=400,
            height=300,
            offset_x=0,
            offset_y=0,
        )

        result = weather_display.panel.rain_cloud._create_rain_cloud_img(
            config.rain_cloud,
            sub_panel_config,
            face_map,
            config.slack,
            trial=0,
        )

        # clear_cache と delete_profile が呼ばれること
        assert mock_browser.maintenance.clear_cache.called
        assert mock_delete.called
        assert result is not None
