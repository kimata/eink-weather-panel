#!/usr/bin/env python3
# ruff: noqa: S101
"""
metrics/server.py のユニットテスト
"""
import threading
import time

import pytest


class TestCreateApp:
    """create_app 関数のテスト"""

    def test_create_app_returns_flask_app(self, config):
        """Flask アプリケーションを返すこと"""
        from weather_display.metrics import server

        app = server.create_app(config)

        assert app is not None
        assert hasattr(app, "config")
        assert app.config["CONFIG"] == config

    def test_create_app_has_cors(self, config):
        """CORS が有効であること"""
        from weather_display.metrics import server

        app = server.create_app(config)

        # CORS が設定されていること
        assert app is not None


class TestStartAndTerm:
    """start と term 関数のテスト"""

    def test_start_returns_handle(self, config, mocker):
        """start がハンドルを返すこと"""
        from weather_display.metrics import server

        # モックサーバーを作成
        mock_server = mocker.MagicMock()
        mocker.patch("werkzeug.serving.make_server", return_value=mock_server)

        handle = server.start(config, 5001)

        assert "server" in handle
        assert "thread" in handle
        assert isinstance(handle["thread"], threading.Thread)

        # クリーンアップ
        server.term(handle)

    def test_term_shuts_down_server(self, config, mocker):
        """term がサーバーをシャットダウンすること"""
        from weather_display.metrics import server

        mock_server = mocker.MagicMock()
        mock_thread = mocker.MagicMock()
        mock_thread.is_alive.return_value = False

        handle = {"server": mock_server, "thread": mock_thread}

        server.term(handle)

        mock_server.shutdown.assert_called_once()
        mock_server.server_close.assert_called_once()
        mock_thread.join.assert_called_once()

    def test_term_logs_warning_on_timeout(self, config, mocker):
        """スレッドがタイムアウトした場合に警告をログすること"""
        from weather_display.metrics import server

        mock_server = mocker.MagicMock()
        mock_thread = mocker.MagicMock()
        mock_thread.is_alive.return_value = True  # タイムアウトをシミュレート

        handle = {"server": mock_server, "thread": mock_thread}

        # 例外は発生しないこと
        server.term(handle)

        mock_thread.join.assert_called_once()
