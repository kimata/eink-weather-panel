#!/usr/bin/env python3
# ruff: noqa: S101
"""
雨雲パネルの統合テスト
"""
import pytest

# このファイル全体のテストを selenium マークする
pytestmark = pytest.mark.selenium


class TestRainCloudPanel:
    """雨雲パネルのテスト"""

    def test_rain_cloud_panel_create(self, config, image_checker):
        """雨雲パネルを生成できること"""
        import weather_display.panel.rain_cloud

        result = weather_display.panel.rain_cloud.create(config)

        assert len(result) >= 2
        img = result[0]
        assert img is not None
        image_checker.check(img, config.rain_cloud.panel, 0)

    def test_rain_cloud_panel_create_not_side_by_side(self, config, image_checker):
        """横並びでない雨雲パネルを生成できること"""
        import weather_display.panel.rain_cloud

        result = weather_display.panel.rain_cloud.create(config, is_side_by_side=False)

        assert len(result) >= 2
        img = result[0]
        assert img is not None
        image_checker.check(img, config.rain_cloud.panel, 1)


class TestRainCloudPanelCache:
    """雨雲パネルのキャッシュテスト"""

    def test_rain_cloud_panel_with_cache_error(self, config, image_checker, mocker):
        """キャッシュエラー時にも正常に動作すること"""
        import weather_display.panel.rain_cloud

        mocker.patch("pickle.load", side_effect=RuntimeError())

        result = weather_display.panel.rain_cloud.create(config)

        assert len(result) >= 2
        img = result[0]
        assert img is not None


class TestRainCloudPanelError:
    """雨雲パネルのエラーハンドリングテスト"""

    def test_rain_cloud_panel_click_xpath_error(self, config, image_checker, mocker):
        """click_xpathエラー時にリトライされること"""
        from my_lib.selenium_util import click_xpath as click_xpath_orig

        import weather_display.panel.rain_cloud

        # 2回だけエラーにする
        def click_xpath_mock(driver, xpath, wait=None, is_warn=True):
            click_xpath_mock.i += 1
            if click_xpath_mock.i <= 2:
                raise RuntimeError()
            return click_xpath_orig(driver, xpath, wait, is_warn)

        click_xpath_mock.i = 0

        weather_display.panel.rain_cloud.PATIENT_COUNT = 1
        mocker.patch("weather_display.panel.rain_cloud.click_xpath", side_effect=click_xpath_mock)
        mocker.patch("weather_display.panel.rain_cloud.time.sleep")
        mocker.patch.dict("os.environ", {"DUMMY_MODE": "false"})

        result = weather_display.panel.rain_cloud.create(config, True, False)

        assert len(result) >= 2

    def test_rain_cloud_panel_xpath_exists_error(self, config, image_checker, mocker):
        """xpath_existsエラー時のハンドリング"""
        from my_lib.selenium_util import xpath_exists

        import weather_display.panel.rain_cloud

        # 1回だけ False を返す
        def xpath_exists_mock(driver, xpath):
            xpath_exists_mock.i += 1
            if xpath_exists_mock.i == 1:
                return False
            return xpath_exists(driver, xpath)

        xpath_exists_mock.i = 0

        mocker.patch("my_lib.selenium_util.xpath_exists", side_effect=xpath_exists_mock)

        result = weather_display.panel.rain_cloud.create(config)

        assert len(result) >= 2

    def test_rain_cloud_panel_selenium_error(self, config, image_checker, mocker):
        """Seleniumエラー時のハンドリング"""
        from my_lib.selenium_util import create_driver_impl

        import weather_display.panel.rain_cloud

        # 1回だけエラーにする
        def create_driver_impl_mock(profile_name, data_path):
            create_driver_impl_mock.i += 1
            if create_driver_impl_mock.i == 1:
                raise RuntimeError()
            return create_driver_impl(profile_name, data_path)

        create_driver_impl_mock.i = 0

        mocker.patch("my_lib.selenium_util.create_driver_impl", side_effect=create_driver_impl_mock)

        result = weather_display.panel.rain_cloud.create(config)

        assert len(result) >= 2

    def test_rain_cloud_panel_threaded_false(self, config, image_checker):
        """スレッド無効モードで動作すること"""
        import weather_display.panel.rain_cloud

        result = weather_display.panel.rain_cloud.create(config, is_threaded=False)

        assert len(result) >= 2
