#!/usr/bin/env python3
# ruff: noqa: S101
"""
webui.py のユニットテスト
"""

import os


class TestCreateApp:
    """create_app 関数のテスト"""

    def test_create_app_returns_flask_app(self, mocker):
        """Flask アプリケーションを返すこと"""
        import webui

        # 必要なモジュールをモック
        mocker.patch.dict("os.environ", {"WERKZEUG_RUN_MAIN": "true"})
        mocker.patch("weather_display.runner.webapi.run.init")
        mocker.patch("atexit.register")

        app = webui.create_app("config.example.yaml", "config.example.yaml", dummy_mode=True)

        assert app is not None
        assert app.config["CONFIG_FILE_NORMAL"] == "config.example.yaml"
        assert app.config["CONFIG_FILE_SMALL"] == "config.example.yaml"
        assert app.config["DUMMY_MODE"] is True

    def test_create_app_without_werkzeug_main(self, mocker):
        """WERKZEUG_RUN_MAIN が設定されていない場合も動作すること"""
        import webui

        mocker.patch.dict("os.environ", {}, clear=False)
        if "WERKZEUG_RUN_MAIN" in os.environ:
            del os.environ["WERKZEUG_RUN_MAIN"]

        app = webui.create_app("config.example.yaml", "config.example.yaml")

        assert app is not None


class TestSpec:
    """WebAppSpec 定義のテスト

    graceful shutdown・シグナル処理は my_lib.webapp.runner 側でテストされる。
    """

    def test_logger_name(self):
        """ロガー名が設定されている"""
        import webui

        assert webui.SPEC.logger_name == "panel.e-ink.weather"

    def test_term_hook_wired(self):
        """term_hooks に runner.webapi.run.term が配線されている"""
        import weather_display.runner.webapi.run
        import webui

        assert weather_display.runner.webapi.run.term in webui.SPEC.term_hooks
