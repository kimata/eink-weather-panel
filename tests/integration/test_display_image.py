#!/usr/bin/env python3
# ruff: noqa: S101
"""
display_image.py 統合テスト

画像表示制御の統合テストを行います。
"""

import pytest


@pytest.fixture
def mock_ssh(mocker):
    """SSH接続のモック"""
    ssh = mocker.MagicMock()
    stdin = mocker.MagicMock()
    stdout = mocker.MagicMock()
    stderr = mocker.MagicMock()
    stdout.channel.recv_exit_status.return_value = 0
    ssh.exec_command.return_value = (stdin, stdout, stderr)

    mocker.patch("paramiko.RSAKey.from_private_key")
    mocker.patch("paramiko.SSHClient", return_value=ssh)

    return {"ssh": ssh, "stdin": stdin, "stdout": stdout, "stderr": stderr}


@pytest.fixture
def mock_display(mocker, mock_ssh, mock_sensor_fetch_data):
    """display関連のモック"""
    mock_sensor_fetch_data()

    mocker.patch("weather_display.display.ssh_connect", return_value=mock_ssh["ssh"])
    mocker.patch("weather_display.display.ssh_kill_and_close")
    mocker.patch("weather_display.display.execute")

    return mock_ssh


class TestExecute:
    """execute 関数のテスト"""

    def test_execute_one_time_mode(self, config, mock_display):
        """1回のみ実行モードで動作すること"""
        import display_image

        ssh, sleep_time, timing_controller = display_image.execute(
            config,
            rasp_hostname="test-host",
            key_file_path="key/test.id_rsa",
            config_file="config.example.yaml",
            small_mode=False,
            test_mode=True,
            is_one_time=True,
            prev_ssh=None,
            timing_controller=None,
        )

        # 正常に実行されること
        assert ssh is not None

    def test_execute_continuous_mode(self, config, mock_display, mocker):
        """連続モードで動作すること"""
        import display_image

        ssh, sleep_time, timing_controller = display_image.execute(
            config,
            rasp_hostname="test-host",
            key_file_path="key/test.id_rsa",
            config_file="config.example.yaml",
            small_mode=False,
            test_mode=True,
            is_one_time=False,
            prev_ssh=None,
            timing_controller=None,
        )

        # スリープ時間が設定されること
        assert sleep_time >= 0
        # タイミングコントローラーが作成されること
        assert timing_controller is not None

    def test_execute_with_exception(self, config, mocker, mock_sensor_fetch_data):
        """例外発生時にエラーハンドリングされること"""
        import display_image

        mock_sensor_fetch_data()

        mocker.patch("weather_display.display.ssh_kill_and_close")
        mocker.patch("weather_display.display.ssh_connect", side_effect=Exception("Test exception"))

        ssh, sleep_time, timing_controller = display_image.execute(
            config,
            rasp_hostname="test-host",
            key_file_path="key/test.id_rsa",
            config_file="config.example.yaml",
            small_mode=False,
            test_mode=True,
            is_one_time=True,
            prev_ssh=None,
            timing_controller=None,
        )

        # 例外発生時も処理が継続すること


class TestSigHandler:
    """シグナルハンドラのテスト"""

    def test_sig_handler_sigterm(self, mocker):
        """SIGTERM シグナルを処理できること"""
        import signal

        import display_image

        display_image.should_terminate.clear()

        display_image.sig_handler(signal.SIGTERM, None)

        assert display_image.should_terminate.is_set()

    def test_sig_handler_sigint(self, mocker):
        """SIGINT シグナルを処理できること"""
        import signal

        import display_image

        display_image.should_terminate.clear()

        display_image.sig_handler(signal.SIGINT, None)

        assert display_image.should_terminate.is_set()


class TestCleanup:
    """cleanup 関数のテスト"""

    def test_cleanup_calls_term(self, mocker):
        """cleanup がメトリクスサーバーを停止すること"""
        import display_image

        mock_term = mocker.patch("weather_display.metrics.server.term")
        mocker.patch("my_lib.proc_util.kill_child")
        mocker.patch("sys.exit")

        handle = mocker.MagicMock()

        display_image.cleanup(handle)

        # term が呼ばれること
        mock_term.assert_called_once()


class TestStart:
    """start 関数のテスト"""

    @pytest.fixture
    def mock_execute(self, mocker, mock_ssh):
        """execute 関数のモック"""
        import display_image

        mock = mocker.patch.object(
            display_image,
            "execute",
            return_value=(mock_ssh["ssh"], 0.0, None),
        )
        return mock

    def test_start_one_time_mode(self, config, mocker, mock_execute):
        """1回のみモードで start が動作すること"""
        import display_image

        display_image.start(
            config,
            rasp_hostname="test-host",
            key_file_path="key/test.id_rsa",
            config_file="config.example.yaml",
            small_mode=False,
            test_mode=True,
            is_one_time=True,
        )

        mock_execute.assert_called_once()

    def test_start_continuous_mode_with_terminate(self, config, mocker, mock_execute):
        """連続モードで terminate シグナルにより終了すること"""
        import display_image

        # 2回目の実行後に終了するようにする
        call_count = 0

        def mock_execute_side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count >= 2:
                display_image.should_terminate.set()
            return (mocker.MagicMock(), 0.1, None)

        mock_execute.side_effect = mock_execute_side_effect
        display_image.should_terminate.clear()

        display_image.start(
            config,
            rasp_hostname="test-host",
            key_file_path="key/test.id_rsa",
            config_file="config.example.yaml",
            small_mode=False,
            test_mode=True,
            is_one_time=False,
        )

        assert call_count >= 2

    def test_start_handles_exception(self, config, mocker):
        """例外発生時に適切にハンドリングすること"""
        import display_image

        mocker.patch.object(display_image, "execute", side_effect=RuntimeError("Test exception"))
        mocker.patch("my_lib.panel_util.notify_error")
        mocker.patch("time.sleep")

        with pytest.raises(RuntimeError, match="Test exception"):
            display_image.start(
                config,
                rasp_hostname="test-host",
                key_file_path="key/test.id_rsa",
                config_file="config.example.yaml",
                small_mode=False,
                test_mode=True,
                is_one_time=True,
            )


class TestExecuteTimingController:
    """execute 関数のタイミングコントローラテスト"""

    @pytest.fixture
    def mock_display(self, mocker, mock_ssh, mock_sensor_fetch_data):
        """display関連のモック"""
        mock_sensor_fetch_data()

        mocker.patch("weather_display.display.ssh_connect", return_value=mock_ssh["ssh"])
        mocker.patch("weather_display.display.ssh_kill_and_close")
        mocker.patch("weather_display.display.execute")

        return mock_ssh

    def test_execute_creates_timing_controller(self, config, mock_display, mocker):
        """execute がタイミングコントローラを作成すること"""
        import display_image

        ssh, sleep_time, timing_controller = display_image.execute(
            config,
            rasp_hostname="test-host",
            key_file_path="key/test.id_rsa",
            config_file="config.example.yaml",
            small_mode=False,
            test_mode=True,
            is_one_time=False,
            prev_ssh=None,
            timing_controller=None,
        )

        assert timing_controller is not None

    def test_execute_reuses_timing_controller(self, config, mock_display, mocker):
        """execute が既存のタイミングコントローラを再利用すること"""
        import display_image
        from weather_display.timing_filter import TimingController

        existing_controller = TimingController(update_interval=5, target_second=0)

        ssh, sleep_time, timing_controller = display_image.execute(
            config,
            rasp_hostname="test-host",
            key_file_path="key/test.id_rsa",
            config_file="config.example.yaml",
            small_mode=False,
            test_mode=True,
            is_one_time=False,
            prev_ssh=None,
            timing_controller=existing_controller,
        )

        assert timing_controller is existing_controller

    def test_execute_warns_on_large_timing_gap(self, config, mock_display, mocker, caplog):
        """大きなタイミングずれ時に警告すること"""
        import logging

        import display_image
        from weather_display.timing_filter import TimingController

        # タイミングコントローラをモックして大きなdiff_secを返す
        mock_controller = mocker.MagicMock(spec=TimingController)
        mock_controller.calculate_sleep_time.return_value = (50.0, 10)  # diff_sec = 10 > 3

        with caplog.at_level(logging.WARNING):
            ssh, sleep_time, timing_controller = display_image.execute(
                config,
                rasp_hostname="test-host",
                key_file_path="key/test.id_rsa",
                config_file="config.example.yaml",
                small_mode=False,
                test_mode=True,
                is_one_time=False,
                prev_ssh=None,
                timing_controller=mock_controller,
            )

        assert any("timing gap is large" in record.message for record in caplog.records)

    def test_execute_no_warning_on_small_timing_gap(self, config, mock_display, mocker, caplog):
        """小さなタイミングずれ時は警告しないこと (line 117->128)"""
        import logging

        import display_image
        from weather_display.timing_filter import TimingController

        # タイミングコントローラをモックして小さなdiff_secを返す (|diff_sec| <= 3)
        mock_controller = mocker.MagicMock(spec=TimingController)
        mock_controller.calculate_sleep_time.return_value = (50.0, 2)  # diff_sec = 2 <= 3

        with caplog.at_level(logging.WARNING):
            ssh, sleep_time, timing_controller = display_image.execute(
                config,
                rasp_hostname="test-host",
                key_file_path="key/test.id_rsa",
                config_file="config.example.yaml",
                small_mode=False,
                test_mode=True,
                is_one_time=False,
                prev_ssh=None,
                timing_controller=mock_controller,
            )

        # タイミングずれの警告がないこと
        assert not any("timing gap is large" in record.message for record in caplog.records)


class TestSigHandlerAdvanced:
    """シグナルハンドラの追加テスト"""

    def test_sig_handler_sigusr1(self, mocker):
        """SIGUSR1 シグナルでトレースバックを出力すること"""
        import signal

        import display_image

        mock_dump = mocker.patch("faulthandler.dump_traceback")

        display_image.sig_handler(signal.SIGUSR1, None)

        mock_dump.assert_called_once()

    def test_sig_handler_other_signal(self, mocker):
        """未知のシグナルでは何も行わないこと (line 66->exit)"""
        import signal

        import display_image

        display_image.should_terminate.clear()
        mock_dump = mocker.patch("faulthandler.dump_traceback")

        # SIGHUP など、処理対象外のシグナル
        display_image.sig_handler(signal.SIGHUP, None)

        # should_terminate は設定されない
        assert not display_image.should_terminate.is_set()
        # dump_traceback も呼ばれない
        assert not mock_dump.called


class TestExecuteMetricsLogging:
    """execute 関数のメトリクスログ処理テスト"""

    @pytest.fixture
    def mock_display(self, mocker, mock_ssh, mock_sensor_fetch_data):
        """display関連のモック"""
        mock_sensor_fetch_data()

        mocker.patch("weather_display.display.ssh_connect", return_value=mock_ssh["ssh"])
        mocker.patch("weather_display.display.ssh_kill_and_close")
        mocker.patch("weather_display.display.execute")

        return mock_ssh

    def test_execute_handles_metrics_log_error(self, config, mock_display, mocker, caplog):
        """メトリクスログ失敗時も処理を継続すること"""
        import logging

        import display_image

        # メトリクス収集をモックしてエラーを発生させる
        mocker.patch(
            "weather_display.metrics.collector.collect_display_image_metrics",
            side_effect=Exception("Metrics logging failed"),
        )

        with caplog.at_level(logging.WARNING):
            ssh, sleep_time, timing_controller = display_image.execute(
                config,
                rasp_hostname="test-host",
                key_file_path="key/test.id_rsa",
                config_file="config.example.yaml",
                small_mode=False,
                test_mode=True,
                is_one_time=True,
                prev_ssh=None,
                timing_controller=None,
            )

        # 例外が発生してもエラーにならず処理が完了すること
        assert ssh is not None
        assert any("Failed to log execute metrics" in record.message for record in caplog.records)


class TestCleanupAdvanced:
    """cleanup 関数の追加テスト"""

    def test_cleanup_handles_daemon_threads(self, mocker):
        """cleanup がデーモンスレッドを適切に処理すること"""
        import threading

        import display_image

        mocker.patch("weather_display.metrics.server.term")
        mocker.patch("my_lib.proc_util.kill_child")
        mocker.patch("sys.exit")

        # デーモンスレッドをシミュレート
        mock_thread = mocker.MagicMock(spec=threading.Thread)
        mock_thread.name = "TestDaemon"
        mock_thread.daemon = True
        mock_thread.is_alive.return_value = True

        # threading.enumerate をモック
        mocker.patch("threading.enumerate", return_value=[mock_thread])

        handle = mocker.MagicMock()

        # 例外なく完了すること
        display_image.cleanup(handle)


class TestStartWithMultipleFailures:
    """start 関数の連続失敗テスト"""

    def test_start_continues_on_first_failure(self, config, mocker):
        """最初の失敗で継続し、2回目で終了すること"""
        import display_image

        call_count = 0

        def failing_execute(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise RuntimeError("First failure")
            elif call_count == 2:
                raise RuntimeError("Second failure")
            return (mocker.MagicMock(), 0.1, None)

        mocker.patch.object(display_image, "execute", side_effect=failing_execute)
        mocker.patch("my_lib.panel_util.notify_error")
        mocker.patch("time.sleep")

        with pytest.raises(RuntimeError, match="Second failure"):
            display_image.start(
                config,
                rasp_hostname="test-host",
                key_file_path="key/test.id_rsa",
                config_file="config.example.yaml",
                small_mode=False,
                test_mode=True,
                is_one_time=False,
            )

        # 2回実行されること（NOTIFY_THRESHOLD = 2）
        assert call_count == 2
