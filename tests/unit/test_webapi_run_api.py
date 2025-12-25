#!/usr/bin/env python3
# ruff: noqa: S101
"""
runner/webapi/run.py の API エンドポイントテスト
"""
import queue
import threading
import time

import flask
import pytest


@pytest.fixture
def run_app(mocker):
    """テスト用の Flask アプリケーションを作成"""
    import my_lib.webapp.config

    from weather_display.runner.webapi import run

    # URL_PREFIX を設定
    my_lib.webapp.config.URL_PREFIX = "/panel"

    run.init("/path/to/create_image.py")

    app = flask.Flask("test")
    app.config["CONFIG_FILE_NORMAL"] = "config.yaml"
    app.config["CONFIG_FILE_SMALL"] = "config-small.yaml"
    app.config["DUMMY_MODE"] = True

    app.register_blueprint(run.blueprint, url_prefix="/panel")

    yield app

    run.term()


@pytest.fixture
def run_client(run_app):
    """テストクライアントを作成"""
    return run_app.test_client()


class TestApiRun:
    """api_run エンドポイントのテスト"""

    def test_api_run_returns_token(self, run_client, mocker):
        """api_run がトークンを返すこと"""
        from weather_display.runner.webapi import run

        mocker.patch.object(run.thread_pool, "submit")

        response = run_client.get("/panel/api/run")

        assert response.status_code == 200
        data = response.get_json()
        assert "token" in data
        assert len(data["token"]) == 36  # UUID format

    def test_api_run_with_small_mode(self, run_client, mocker):
        """small モードで api_run が動作すること"""
        from weather_display.runner.webapi import run

        mocker.patch.object(run.thread_pool, "submit")

        response = run_client.get("/panel/api/run?mode=small")

        assert response.status_code == 200
        data = response.get_json()
        assert "token" in data

    def test_api_run_with_test_mode(self, run_client, mocker):
        """test モードで api_run が動作すること"""
        from weather_display.runner.webapi import run

        mocker.patch.object(run.thread_pool, "submit")

        response = run_client.get("/panel/api/run?test=true")

        assert response.status_code == 200
        data = response.get_json()
        assert "token" in data

    def test_api_run_exception(self, run_client, mocker):
        """例外発生時にエラーを返すこと"""
        from weather_display.runner.webapi import run

        mocker.patch.object(run, "generate_image", side_effect=RuntimeError("Test error"))

        response = run_client.get("/panel/api/run")

        assert response.status_code == 200
        data = response.get_json()
        assert data["token"] == ""
        assert "error" in data


class TestApiImage:
    """api_image エンドポイントのテスト"""

    def test_api_image_returns_image(self, run_client, mocker):
        """api_image が画像を返すこと"""
        from weather_display.runner.webapi import run

        token = "test-token-12345678-1234-1234-1234"
        run.panel_data_map[token] = {
            "lock": threading.Lock(),
            "log": queue.Queue(),
            "image": b"\x89PNG\r\n\x1a\n",  # PNG header
            "time": time.time(),
        }

        response = run_client.post("/panel/api/image", data={"token": token})

        assert response.status_code == 200
        assert response.data == b"\x89PNG\r\n\x1a\n"

        # クリーンアップ
        del run.panel_data_map[token]

    def test_api_image_invalid_token(self, run_client):
        """無効なトークンでエラーを返すこと"""
        response = run_client.post("/panel/api/image", data={"token": "invalid-token"})

        assert response.status_code == 200
        assert b"Invalid token" in response.data


class TestApiLog:
    """api_log エンドポイントのテスト"""

    def test_api_log_invalid_token(self, run_client):
        """無効なトークンでエラーを返すこと"""
        response = run_client.post("/panel/api/log", data={"token": "invalid-token"})

        assert response.status_code == 200
        assert b"Invalid token" in response.data

    def test_api_log_returns_log_lines(self, run_client, mocker):
        """api_log がログ行を返すこと"""
        from weather_display.runner.webapi import run

        token = "test-log-token-1234-1234-1234-1234"
        log_queue = queue.Queue()
        log_queue.put(b"log line 1\n")
        log_queue.put(b"log line 2\n")
        log_queue.put(None)  # 完了通知

        run.panel_data_map[token] = {
            "lock": threading.Lock(),
            "log": log_queue,
            "image": None,
            "time": time.time(),
        }

        mocker.patch("time.sleep")

        response = run_client.post("/panel/api/log", data={"token": token})

        assert response.status_code == 200
        assert b"log line 1" in response.data
        assert b"log line 2" in response.data

        # クリーンアップ
        del run.panel_data_map[token]

    def test_api_log_waits_for_data(self, run_client, mocker):
        """api_log がデータを待機すること"""
        from weather_display.runner.webapi import run

        token = "test-wait-token-1234-1234-1234-1234"
        log_queue = queue.Queue()
        # 最初は空、後でNoneを追加（完了通知）
        log_queue.put(None)

        run.panel_data_map[token] = {
            "lock": threading.Lock(),
            "log": log_queue,
            "image": None,
            "time": time.time(),
        }

        mocker.patch("time.sleep")

        response = run_client.post("/panel/api/log", data={"token": token})

        assert response.status_code == 200

        # クリーンアップ
        del run.panel_data_map[token]

    def test_api_log_empty_queue_continues(self, run_client, mocker):
        """空のキューで continue が実行されること (line 205)"""
        from weather_display.runner.webapi import run

        token = "test-empty-queue-1234-1234-1234"
        log_queue = queue.Queue()

        run.panel_data_map[token] = {
            "lock": threading.Lock(),
            "log": log_queue,
            "image": None,
            "time": time.time(),
        }

        # 別スレッドで少し待ってから None を追加（完了通知）
        def delayed_put():
            time.sleep(0.2)  # queue.Empty が発生する時間を確保
            log_queue.put(None)

        thread = threading.Thread(target=delayed_put)
        thread.start()

        response = run_client.post("/panel/api/log", data={"token": token})

        thread.join()

        assert response.status_code == 200

        # クリーンアップ
        del run.panel_data_map[token]

    def test_api_log_handles_exception(self, run_client, mocker):
        """api_log が例外を処理すること"""
        from weather_display.runner.webapi import run

        token = "test-exc-token-1234-1234-1234-1234"
        log_queue = mocker.MagicMock()
        log_queue.empty.return_value = False
        log_queue.get.side_effect = RuntimeError("Queue error")

        run.panel_data_map[token] = {
            "lock": threading.Lock(),
            "log": log_queue,
            "image": None,
            "time": time.time(),
        }

        response = run_client.post("/panel/api/log", data={"token": token})

        # 例外が発生しても200を返すこと
        assert response.status_code == 200

        # クリーンアップ
        del run.panel_data_map[token]
