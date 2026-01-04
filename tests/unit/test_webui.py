#!/usr/bin/env python3
# ruff: noqa: S101
"""
webui.py のユニットテスト
"""

import os
import signal


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


class TestTerm:
    """term 関数のテスト"""

    def test_term_calls_cleanup(self, mocker):
        """term がクリーンアップ処理を呼ぶこと"""
        import webui

        mock_run_term = mocker.patch("weather_display.runner.webapi.run.term")
        mock_kill_child = mocker.patch("my_lib.proc_util.kill_child")
        mock_exit = mocker.patch("sys.exit")

        webui.term()

        mock_run_term.assert_called_once()
        mock_kill_child.assert_called_once()
        mock_exit.assert_called_once_with(0)


class TestSigHandler:
    """sig_handler 関数のテスト"""

    def test_sig_handler_sigterm(self, mocker):
        """SIGTERM シグナルを処理できること"""
        import webui

        mock_term = mocker.patch.object(webui, "term")

        webui.sig_handler(signal.SIGTERM, None)

        mock_term.assert_called_once()

    def test_sig_handler_sigint(self, mocker):
        """SIGINT シグナルを処理できること"""
        import webui

        mock_term = mocker.patch.object(webui, "term")

        webui.sig_handler(signal.SIGINT, None)

        mock_term.assert_called_once()

    def test_sig_handler_other_signal(self, mocker):
        """他のシグナルでは term を呼ばないこと"""
        import webui

        mock_term = mocker.patch.object(webui, "term")

        webui.sig_handler(signal.SIGUSR1, None)

        mock_term.assert_not_called()
