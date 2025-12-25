#!/usr/bin/env python3
# ruff: noqa: S101
"""
runner/webapi/run.py のユニットテスト
"""
import io
import queue
import threading
import time

import pytest


class TestInit:
    """init 関数のテスト"""

    def test_init_creates_thread_pool(self, mocker):
        """init がスレッドプールを作成すること"""
        from weather_display.runner.webapi import run

        run.init("/path/to/create_image.py")

        assert run.thread_pool is not None
        assert run.create_image_path == "/path/to/create_image.py"

        run.term()


class TestTerm:
    """term 関数のテスト"""

    def test_term_shuts_down_thread_pool(self, mocker):
        """term がスレッドプールをシャットダウンすること"""
        from weather_display.runner.webapi import run

        run.init("/path/to/create_image.py")
        run.term()

        # 再度termを呼んでも問題ないことを確認
        run.term()


class TestCleanMap:
    """clean_map 関数のテスト"""

    def test_clean_map_removes_old_entries(self):
        """古いエントリが削除されること"""
        from weather_display.runner.webapi import run

        run.panel_data_map = {
            "old_token": {"time": time.time() - 120},  # 2分前
            "new_token": {"time": time.time()},  # 現在
        }

        run.clean_map()

        assert "old_token" not in run.panel_data_map
        assert "new_token" in run.panel_data_map

    def test_clean_map_keeps_recent_entries(self):
        """最近のエントリが保持されること"""
        from weather_display.runner.webapi import run

        run.panel_data_map = {
            "token1": {"time": time.time() - 30},  # 30秒前
            "token2": {"time": time.time() - 50},  # 50秒前
        }

        run.clean_map()

        assert "token1" in run.panel_data_map
        assert "token2" in run.panel_data_map


class TestGenerateImage:
    """generate_image 関数のテスト"""

    def test_generate_image_raises_error_when_thread_pool_not_initialized(self):
        """thread_pool が初期化されていない場合に RuntimeError が発生すること"""
        from weather_display.runner.webapi import run

        # thread_pool を None に設定
        run.thread_pool = None

        with pytest.raises(RuntimeError, match="thread_pool is not initialized"):
            run.generate_image("config.yaml", False, False, True)

    def test_generate_image_creates_token(self, mocker):
        """generate_image がトークンを生成すること"""
        from weather_display.runner.webapi import run

        run.init("/path/to/create_image.py")

        mock_submit = mocker.patch.object(run.thread_pool, "submit")

        token = run.generate_image("config.yaml", False, False, True)

        assert token is not None
        assert len(token) == 36  # UUID format
        assert token in run.panel_data_map

        run.term()

    def test_generate_image_sets_up_panel_data(self, mocker):
        """generate_image がパネルデータを正しく設定すること"""
        from weather_display.runner.webapi import run

        run.init("/path/to/create_image.py")
        mocker.patch.object(run.thread_pool, "submit")

        token = run.generate_image("config.yaml", True, True, False)

        panel_data = run.panel_data_map[token]
        assert "lock" in panel_data
        assert "log" in panel_data
        assert "image" in panel_data
        assert panel_data["image"] is None
        assert "time" in panel_data

        run.term()


class TestImageReader:
    """image_reader 関数のテスト"""

    def test_image_reader_reads_stdout(self, mocker):
        """image_reader が stdout を読み取ること"""
        from weather_display.runner.webapi import run

        token = "test_token"
        run.panel_data_map[token] = {
            "lock": threading.Lock(),
            "log": queue.Queue(),
            "image": None,
            "time": time.time(),
        }

        mock_proc = mocker.MagicMock()
        mock_proc.poll.side_effect = [None, 0]
        mock_proc.stdout.read.side_effect = [b"image_data", b""]

        run.image_reader(mock_proc, token)

        assert run.panel_data_map[token]["image"] == b"image_data"


class TestLogReader:
    """log_reader 関数のテスト"""

    def test_log_reader_reads_stderr(self, mocker):
        """log_reader が stderr を読み取ること"""
        from weather_display.runner.webapi import run

        token = "test_token"
        log_queue = queue.Queue()
        run.panel_data_map[token] = {
            "lock": threading.Lock(),
            "log": log_queue,
            "image": None,
            "time": time.time(),
        }

        mock_proc = mocker.MagicMock()
        mock_proc.stderr.readline.side_effect = [b"log line 1\n", b"log line 2\n", b""]

        run.log_reader(mock_proc, token)

        assert log_queue.get() == b"log line 1\n"
        assert log_queue.get() == b"log line 2\n"

    def test_log_reader_handles_exception(self, mocker):
        """log_reader が例外を処理すること"""
        from weather_display.runner.webapi import run

        token = "test_token_exc"
        log_queue = queue.Queue()
        run.panel_data_map[token] = {
            "lock": threading.Lock(),
            "log": log_queue,
            "image": None,
            "time": time.time(),
        }

        mock_proc = mocker.MagicMock()
        mock_proc.stderr.readline.side_effect = RuntimeError("Read error")

        # 例外が発生しても関数が終了すること
        run.log_reader(mock_proc, token)


class TestImageReaderEdgeCases:
    """image_reader 関数のエッジケーステスト"""

    def test_image_reader_handles_oserror(self, mocker):
        """image_reader が OSError を処理すること"""
        from weather_display.runner.webapi import run

        token = "test_token_oserror"
        run.panel_data_map[token] = {
            "lock": threading.Lock(),
            "log": queue.Queue(),
            "image": None,
            "time": time.time(),
        }

        mock_proc = mocker.MagicMock()
        mock_proc.poll.side_effect = [None, None]
        mock_proc.stdout.read.side_effect = [b"data", OSError("Pipe closed")]

        run.image_reader(mock_proc, token)

        # 一部データが読み取られていること
        assert run.panel_data_map[token]["image"] == b"data"

    def test_image_reader_handles_exception(self, mocker):
        """image_reader が一般例外を処理すること"""
        from weather_display.runner.webapi import run

        token = "test_token_general_exc"
        run.panel_data_map[token] = {
            "lock": threading.Lock(),
            "log": queue.Queue(),
            "image": None,
            "time": time.time(),
        }

        mock_proc = mocker.MagicMock()
        mock_proc.poll.side_effect = RuntimeError("Unexpected error")

        # 例外が発生しても関数が終了すること
        run.image_reader(mock_proc, token)

    def test_image_reader_reads_remaining_after_process_ends(self, mocker):
        """プロセス終了後に残りのデータを読み取ること"""
        from weather_display.runner.webapi import run

        token = "test_token_remaining"
        run.panel_data_map[token] = {
            "lock": threading.Lock(),
            "log": queue.Queue(),
            "image": None,
            "time": time.time(),
        }

        mock_proc = mocker.MagicMock()
        mock_proc.poll.return_value = 0  # プロセスは既に終了
        mock_proc.stdout.read.return_value = b"remaining_data"

        run.image_reader(mock_proc, token)

        assert run.panel_data_map[token]["image"] == b"remaining_data"

    def test_image_reader_waits_when_no_data(self, mocker):
        """データがない場合に待機すること"""
        from weather_display.runner.webapi import run

        token = "test_token_wait"
        run.panel_data_map[token] = {
            "lock": threading.Lock(),
            "log": queue.Queue(),
            "image": None,
            "time": time.time(),
        }

        mock_proc = mocker.MagicMock()
        # 最初はデータなし、次はデータあり、次はプロセス終了
        mock_proc.poll.side_effect = [None, None, 0]
        mock_proc.stdout.read.side_effect = [b"", b"data", b""]

        mocker.patch("time.sleep")

        run.image_reader(mock_proc, token)

        assert run.panel_data_map[token]["image"] == b"data"


class TestTermEdgeCases:
    """term 関数のエッジケーステスト"""

    def test_term_when_thread_pool_is_none(self):
        """thread_pool が None の場合でも正常に終了すること"""
        from weather_display.runner.webapi import run

        run.thread_pool = None
        run.term()  # 例外が発生しないこと


class TestGenerateImageImpl:
    """generate_image_impl 関数のテスト"""

    def test_generate_image_impl_handles_none_create_image_path(self, mocker, caplog):
        """create_image_path が None の場合にエラーログが出力されること"""
        import logging

        from weather_display.runner.webapi import run

        token = "test_none_path_token"
        log_queue = queue.Queue()
        run.panel_data_map[token] = {
            "lock": threading.Lock(),
            "log": log_queue,
            "image": None,
            "time": time.time(),
            "future": None,
        }
        run.create_image_path = None

        with caplog.at_level(logging.ERROR):
            run.generate_image_impl("config.yaml", False, False, True, token)

        assert "create_image_path is not initialized" in caplog.text
        # 完了通知の None がキューに入っていること
        assert log_queue.get(timeout=1) is None

    def test_generate_image_impl_runs_subprocess(self, mocker):
        """サブプロセスが実行されること"""
        from weather_display.runner.webapi import run

        token = "test_impl_token"
        log_queue = queue.Queue()
        run.panel_data_map[token] = {
            "lock": threading.Lock(),
            "log": log_queue,
            "image": None,
            "time": time.time(),
        }
        run.create_image_path = "/path/to/create_image.py"

        mock_proc = mocker.MagicMock()
        # poll()は最初にNone(実行中)、次に0(終了)を返す
        # NOTE: image_reader スレッドも poll() を呼ぶため、多めに None を返す
        mock_proc.poll.side_effect = [None] * 10 + [0] * 10
        mock_proc.wait.return_value = 0
        mock_proc.stdout.read.side_effect = [b"image", b"", b""]
        mock_proc.stderr.readline.side_effect = [b"log\n", b""]

        mock_popen = mocker.patch("subprocess.Popen", return_value=mock_proc)
        mocker.patch("time.sleep")

        run.generate_image_impl("config.yaml", False, False, True, token)

        mock_popen.assert_called_once()
        # コマンドライン引数に -t (test) が含まれていること
        cmd = mock_popen.call_args[0][0]
        assert "-t" in cmd

        # キューにログと完了通知(None)が入っていること
        found_none = False
        while not log_queue.empty():
            item = log_queue.get_nowait()
            if item is None:
                found_none = True
                break
        assert found_none, "完了通知(None)がログキューに入っていること"

    def test_generate_image_impl_with_small_mode(self, mocker):
        """small モードでサブプロセスが実行されること"""
        from weather_display.runner.webapi import run

        token = "test_small_token"
        run.panel_data_map[token] = {
            "lock": threading.Lock(),
            "log": queue.Queue(),
            "image": None,
            "time": time.time(),
        }
        run.create_image_path = "/path/to/create_image.py"

        mock_proc = mocker.MagicMock()
        mock_proc.poll.return_value = 0
        mock_proc.wait.return_value = 0
        mock_proc.stdout.read.return_value = b""
        mock_proc.stderr.readline.return_value = b""

        mock_popen = mocker.patch("subprocess.Popen", return_value=mock_proc)
        mocker.patch("time.sleep")

        run.generate_image_impl("config.yaml", True, False, False, token)

        cmd = mock_popen.call_args[0][0]
        assert "-S" in cmd

    def test_generate_image_impl_with_dummy_mode(self, mocker):
        """dummy モードでサブプロセスが実行されること"""
        from weather_display.runner.webapi import run

        token = "test_dummy_token"
        run.panel_data_map[token] = {
            "lock": threading.Lock(),
            "log": queue.Queue(),
            "image": None,
            "time": time.time(),
        }
        run.create_image_path = "/path/to/create_image.py"

        mock_proc = mocker.MagicMock()
        mock_proc.poll.return_value = 0
        mock_proc.wait.return_value = 0
        mock_proc.stdout.read.return_value = b""
        mock_proc.stderr.readline.return_value = b""

        mock_popen = mocker.patch("subprocess.Popen", return_value=mock_proc)
        mocker.patch("time.sleep")

        run.generate_image_impl("config.yaml", False, True, False, token)

        cmd = mock_popen.call_args[0][0]
        assert "-d" in cmd

    def test_generate_image_impl_handles_timeout(self, mocker):
        """タイムアウト時にプロセスを終了させること"""
        import subprocess

        from weather_display.runner.webapi import run

        token = "test_timeout_token"
        run.panel_data_map[token] = {
            "lock": threading.Lock(),
            "log": queue.Queue(),
            "image": None,
            "time": time.time(),
        }
        run.create_image_path = "/path/to/create_image.py"

        mock_proc = mocker.MagicMock()
        mock_proc.poll.return_value = 0
        mock_proc.wait.side_effect = subprocess.TimeoutExpired(cmd="test", timeout=120)
        mock_proc.stdout.read.return_value = b""
        mock_proc.stderr.readline.return_value = b""

        mocker.patch("subprocess.Popen", return_value=mock_proc)
        mocker.patch("time.sleep")

        run.generate_image_impl("config.yaml", False, False, False, token)

        mock_proc.terminate.assert_called()

    def test_generate_image_impl_handles_kill_after_terminate(self, mocker):
        """terminate後もタイムアウトした場合にkillすること"""
        import subprocess

        from weather_display.runner.webapi import run

        token = "test_kill_token"
        run.panel_data_map[token] = {
            "lock": threading.Lock(),
            "log": queue.Queue(),
            "image": None,
            "time": time.time(),
        }
        run.create_image_path = "/path/to/create_image.py"

        mock_proc = mocker.MagicMock()
        mock_proc.poll.return_value = 0
        # 1回目: タイムアウト、2回目（terminate後）: タイムアウト
        mock_proc.wait.side_effect = [
            subprocess.TimeoutExpired(cmd="test", timeout=120),
            subprocess.TimeoutExpired(cmd="test", timeout=10),
        ]
        mock_proc.stdout.read.return_value = b""
        mock_proc.stderr.readline.return_value = b""

        mocker.patch("subprocess.Popen", return_value=mock_proc)
        mocker.patch("time.sleep")

        run.generate_image_impl("config.yaml", False, False, False, token)

        mock_proc.terminate.assert_called()
        mock_proc.kill.assert_called()

    def test_generate_image_impl_handles_exception(self, mocker):
        """サブプロセス起動時の例外を処理すること"""
        from weather_display.runner.webapi import run

        token = "test_exception_token"
        run.panel_data_map[token] = {
            "lock": threading.Lock(),
            "log": queue.Queue(),
            "image": None,
            "time": time.time(),
        }
        run.create_image_path = "/path/to/create_image.py"

        mocker.patch("subprocess.Popen", side_effect=OSError("Failed to start"))

        run.generate_image_impl("config.yaml", False, False, False, token)

        # None がログキューに入っていること（完了通知）
        assert run.panel_data_map[token]["log"].get() is None


class TestApiEndpoints:
    """API エンドポイントのテスト"""

    @pytest.fixture
    def flask_app(self):
        """Flask アプリケーションを作成"""
        import flask

        from weather_display.runner.webapi import run

        app = flask.Flask(__name__)
        # url_prefix を空に上書きして登録
        app.register_blueprint(run.blueprint, url_prefix="")
        app.config["TESTING"] = True
        app.config["CONFIG_FILE_NORMAL"] = "/path/to/config.yaml"
        app.config["CONFIG_FILE_SMALL"] = "/path/to/config-small.yaml"
        app.config["DUMMY_MODE"] = True
        return app

    @pytest.fixture
    def client(self, flask_app):
        """Flask テストクライアント"""
        return flask_app.test_client()

    def test_api_image_invalid_token(self, client):
        """無効なトークンで api/image にアクセスした場合"""
        from weather_display.runner.webapi import run

        run.panel_data_map = {}

        response = client.post("/api/image", data={"token": "invalid_token"})

        assert response.status_code == 200
        assert b"Invalid token" in response.data

    def test_api_image_valid_token(self, client):
        """有効なトークンで api/image にアクセスした場合"""
        from weather_display.runner.webapi import run

        token = "valid_token"
        run.panel_data_map = {
            token: {
                "lock": threading.Lock(),
                "log": queue.Queue(),
                "image": b"\x89PNG\r\n\x1a\n",  # PNG header
                "time": time.time(),
            }
        }

        response = client.post("/api/image", data={"token": token})

        assert response.status_code == 200
        assert response.content_type == "image/png"

    def test_api_log_invalid_token(self, client):
        """無効なトークンで api/log にアクセスした場合"""
        from weather_display.runner.webapi import run

        run.panel_data_map = {}

        response = client.post("/api/log", data={"token": "invalid_token"})

        assert response.status_code == 200
        assert b"Invalid token" in response.data

    def test_api_log_valid_token_with_data(self, client):
        """有効なトークンでログデータがある場合"""
        from weather_display.runner.webapi import run

        token = "valid_log_token"
        log_queue = queue.Queue()
        log_queue.put(b"Log line 1\n")
        log_queue.put(b"Log line 2\n")
        log_queue.put(None)  # 終了マーカー

        run.panel_data_map = {
            token: {
                "lock": threading.Lock(),
                "log": log_queue,
                "image": None,
                "time": time.time(),
            }
        }

        response = client.post("/api/log", data={"token": token})

        assert response.status_code == 200
        assert b"Log line 1" in response.data
        assert b"Log line 2" in response.data

    def test_api_run_endpoint(self, client, mocker):
        """api/run エンドポイントのテスト"""
        from weather_display.runner.webapi import run

        run.init("/path/to/create_image.py")
        mocker.patch.object(run.thread_pool, "submit")

        response = client.get("/api/run")

        assert response.status_code == 200
        assert response.content_type == "application/json"

        run.term()
