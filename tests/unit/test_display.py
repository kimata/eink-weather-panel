#!/usr/bin/env python3
# ruff: noqa: S101
"""
display.py のユニットテスト
"""

import subprocess

import pytest


class TestExecPatiently:
    """exec_patiently 関数のテスト"""

    def test_exec_patiently_success_first_try(self, mocker):
        """最初の試行で成功すること"""
        from weather_display import display

        mock_func = mocker.MagicMock(return_value="success")

        result = display._exec_patiently(mock_func, ("arg1", "arg2"))

        assert result == "success"
        assert mock_func.call_count == 1

    def test_exec_patiently_retry_on_failure(self, mocker):
        """失敗時にリトライすること"""
        from weather_display import display

        mock_func = mocker.MagicMock(side_effect=[RuntimeError(), RuntimeError(), "success"])
        mocker.patch("time.sleep")

        result = display._exec_patiently(mock_func, ("arg1",))

        assert result == "success"
        assert mock_func.call_count == 3

    def test_exec_patiently_raises_after_max_retries(self, mocker):
        """最大リトライ回数後に例外を発生させること"""
        from weather_display import display

        mock_func = mocker.MagicMock(side_effect=RuntimeError("Always fails"))
        mocker.patch("time.sleep")

        with pytest.raises(RuntimeError, match="Always fails"):
            display._exec_patiently(mock_func, ())


class TestSshConnect:
    """ssh_connect 関数のテスト"""

    def test_ssh_connect_success(self, mocker):
        """SSH接続が成功すること"""
        from weather_display import display

        mock_ssh = mocker.MagicMock()
        mocker.patch("paramiko.SSHClient", return_value=mock_ssh)
        mocker.patch("paramiko.RSAKey.from_private_key")
        mocker.patch("builtins.open", mocker.mock_open(read_data="key_content"))

        result = display.ssh_connect("hostname", "/path/to/key")

        assert result == mock_ssh

    def test_ssh_connect_retry_on_failure(self, mocker):
        """接続失敗時にリトライすること"""
        from weather_display import display

        mock_ssh = mocker.MagicMock()
        mock_ssh.connect.side_effect = [Exception("Connection failed"), None]
        mocker.patch("paramiko.SSHClient", return_value=mock_ssh)
        mocker.patch("paramiko.RSAKey.from_private_key")
        mocker.patch("builtins.open", mocker.mock_open(read_data="key_content"))
        mocker.patch("time.sleep")

        result = display.ssh_connect("hostname", "/path/to/key")

        assert result == mock_ssh


class TestSshKillAndClose:
    """ssh_kill_and_close 関数のテスト"""

    def test_ssh_kill_and_close_success(self, mocker):
        """SSH接続を正常に終了できること"""
        from weather_display import display

        mock_ssh = mocker.MagicMock()
        mock_stdout = mocker.MagicMock()
        mock_stdout.channel.recv_exit_status.return_value = 0
        mock_ssh.exec_command.return_value = (mocker.MagicMock(), mock_stdout, mocker.MagicMock())

        display.ssh_kill_and_close(mock_ssh, "fbi")

        mock_ssh.exec_command.assert_called()
        mock_ssh.close.assert_called()

    def test_ssh_kill_and_close_with_none(self, mocker):
        """ssh が None でも問題なく動作すること"""
        from weather_display import display

        # 例外が発生しないこと
        display.ssh_kill_and_close(None, "fbi")

    def test_ssh_kill_and_close_handles_attribute_error(self, mocker):
        """AttributeError を適切に処理すること"""
        from weather_display import display

        mock_ssh = mocker.MagicMock()
        mock_ssh.exec_command.side_effect = AttributeError()

        # 例外が発生しないこと
        display.ssh_kill_and_close(mock_ssh, "fbi")


class TestTerminateSessionProcesses:
    """terminate_session_processes 関数のテスト"""

    def test_terminate_session_processes_success(self, mocker):
        """セッションプロセスを正常に終了できること"""
        from weather_display import display

        mock_result = mocker.MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "1234\n5678\n"

        mocker.patch("subprocess.run", return_value=mock_result)
        mock_kill = mocker.patch("os.kill")
        mocker.patch("time.sleep")

        display._terminate_session_processes(1000)

        # SIGTERM と SIGKILL が呼ばれること
        assert mock_kill.call_count >= 2

    def test_terminate_session_processes_no_processes(self, mocker):
        """プロセスが存在しない場合も正常に動作すること"""
        from weather_display import display

        mock_result = mocker.MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = ""

        mocker.patch("subprocess.run", return_value=mock_result)

        # 例外が発生しないこと
        display._terminate_session_processes(1000)

    def test_terminate_session_processes_handles_exception(self, mocker):
        """例外を適切に処理すること"""
        from weather_display import display

        mocker.patch("subprocess.run", side_effect=Exception("Error"))

        # 例外が発生しないこと
        display._terminate_session_processes(1000)


class TestExecute:
    """execute 関数のテスト"""

    @pytest.fixture
    def mock_ssh_session(self, mocker):
        """SSH セッションのモック"""
        mock_ssh = mocker.MagicMock()

        mock_stdin = mocker.MagicMock()
        mock_stdout = mocker.MagicMock()
        mock_stderr = mocker.MagicMock()

        mock_stdout.channel.recv_exit_status.return_value = 0
        mock_ssh.exec_command.return_value = (mock_stdin, mock_stdout, mock_stderr)

        return {"ssh": mock_ssh, "stdin": mock_stdin, "stdout": mock_stdout, "stderr": mock_stderr}

    def test_execute_success(self, config, mocker, mock_ssh_session):
        """画像表示が成功すること"""
        from weather_display import display

        mock_proc = mocker.MagicMock()
        mock_proc.returncode = 0
        mock_proc.pid = 12345
        mock_proc.communicate.return_value = (b"image_data", b"log output")

        mocker.patch("subprocess.Popen", return_value=mock_proc)
        mocker.patch("my_lib.footprint.update")
        mocker.patch("my_lib.proc_util.reap_zombie")

        display.execute(
            mock_ssh_session["ssh"],
            config,
            "config.yaml",
            small_mode=False,
            test_mode=True,
        )

        mock_ssh_session["stdin"].write.assert_called_with(b"image_data")

    def test_execute_with_small_mode(self, config, mocker, mock_ssh_session):
        """small_mode で実行できること"""
        from weather_display import display

        mock_proc = mocker.MagicMock()
        mock_proc.returncode = 0
        mock_proc.pid = 12345
        mock_proc.communicate.return_value = (b"image_data", b"log output")

        mock_popen = mocker.patch("subprocess.Popen", return_value=mock_proc)
        mocker.patch("my_lib.footprint.update")
        mocker.patch("my_lib.proc_util.reap_zombie")

        display.execute(
            mock_ssh_session["ssh"],
            config,
            "config.yaml",
            small_mode=True,
            test_mode=False,
        )

        # -S オプションが含まれていること
        call_args = mock_popen.call_args
        cmd = call_args[0][0]
        assert "-S" in cmd

    def test_execute_timeout(self, config, mocker, mock_ssh_session):
        """タイムアウト時に適切に処理すること"""
        from weather_display import display

        mock_proc = mocker.MagicMock()
        mock_proc.pid = 12345
        mock_proc.communicate.side_effect = subprocess.TimeoutExpired(cmd="test", timeout=300)

        mocker.patch("subprocess.Popen", return_value=mock_proc)
        mocker.patch.object(display, "_terminate_session_processes")
        mocker.patch("my_lib.proc_util.reap_zombie")

        with pytest.raises(RuntimeError, match="timed out"):
            display.execute(
                mock_ssh_session["ssh"],
                config,
                "config.yaml",
                small_mode=False,
                test_mode=True,
            )

    def test_execute_with_error_code_major(self, config, mocker, mock_ssh_session):
        """ERROR_CODE_MAJOR でエラーログが出力されること"""
        import create_image
        from weather_display import display

        mock_proc = mocker.MagicMock()
        mock_proc.returncode = create_image.ERROR_CODE_MAJOR
        mock_proc.pid = 12345
        mock_proc.communicate.return_value = (b"image_data", b"error log")

        mocker.patch("subprocess.Popen", return_value=mock_proc)
        mocker.patch("my_lib.footprint.update")
        mocker.patch("my_lib.proc_util.reap_zombie")

        # 例外が発生しないこと
        display.execute(
            mock_ssh_session["ssh"],
            config,
            "config.yaml",
            small_mode=False,
            test_mode=True,
        )

    def test_execute_with_error_code_minor(self, config, mocker, mock_ssh_session):
        """ERROR_CODE_MINOR でフットプリントが更新されること"""
        import create_image
        from weather_display import display

        mock_proc = mocker.MagicMock()
        mock_proc.returncode = create_image.ERROR_CODE_MINOR
        mock_proc.pid = 12345
        mock_proc.communicate.return_value = (b"image_data", b"partial error")

        mocker.patch("subprocess.Popen", return_value=mock_proc)
        mock_update = mocker.patch("my_lib.footprint.update")
        mocker.patch("my_lib.proc_util.reap_zombie")

        display.execute(
            mock_ssh_session["ssh"],
            config,
            "config.yaml",
            small_mode=False,
            test_mode=True,
        )

        mock_update.assert_called_once()

    def test_execute_with_fbi_failure(self, config, mocker, mock_ssh_session):
        """fbi コマンド失敗時にログが出力されること"""
        from weather_display import display

        mock_proc = mocker.MagicMock()
        mock_proc.returncode = 0
        mock_proc.pid = 12345
        mock_proc.communicate.return_value = (b"image_data", b"log")

        # fbi の終了ステータスを 1 に設定
        mock_ssh_session["stdout"].channel.recv_exit_status.return_value = 1
        mock_ssh_session["stdout"].read.return_value = b"fbi error stdout"
        mock_ssh_session["stderr"].read.return_value = b"fbi error stderr"

        mocker.patch("subprocess.Popen", return_value=mock_proc)
        mocker.patch("my_lib.footprint.update")
        mocker.patch("my_lib.proc_util.reap_zombie")

        # 例外が発生しないこと
        display.execute(
            mock_ssh_session["ssh"],
            config,
            "config.yaml",
            small_mode=False,
            test_mode=True,
        )

    def test_execute_with_unknown_error(self, config, mocker, mock_ssh_session):
        """不明なエラーコードで終了すること"""
        from weather_display import display

        mock_proc = mocker.MagicMock()
        mock_proc.returncode = 99  # 未知のエラーコード
        mock_proc.pid = 12345
        mock_proc.communicate.return_value = (b"image_data", b"unknown error")

        mocker.patch("subprocess.Popen", return_value=mock_proc)
        mocker.patch("my_lib.footprint.update")
        mocker.patch("my_lib.proc_util.reap_zombie")

        with pytest.raises(SystemExit) as exc_info:
            display.execute(
                mock_ssh_session["ssh"],
                config,
                "config.yaml",
                small_mode=False,
                test_mode=True,
            )

        assert exc_info.value.code == 99


class TestSshKillAndCloseEdgeCases:
    """ssh_kill_and_close_impl 関数のエッジケーステスト"""

    def test_ssh_kill_and_close_impl_channel_close_error(self, mocker):
        """チャンネルクローズ時のエラーを処理すること"""
        from weather_display import display

        mock_ssh = mocker.MagicMock()
        mock_stdin = mocker.MagicMock()
        mock_stdout = mocker.MagicMock()
        mock_stderr = mocker.MagicMock()

        mock_stdout.channel.recv_exit_status.return_value = 0
        mock_stdin.close.side_effect = Exception("Close error")
        mock_ssh.exec_command.return_value = (mock_stdin, mock_stdout, mock_stderr)

        # 例外が発生しないこと
        display._ssh_kill_and_close_impl(mock_ssh, "fbi")

        mock_ssh.close.assert_called()

    def test_ssh_kill_and_close_impl_raises_general_exception(self, mocker):
        """一般的な例外を再度発生させること"""
        from weather_display import display

        mock_ssh = mocker.MagicMock()
        mock_ssh.exec_command.side_effect = RuntimeError("General error")

        with pytest.raises(RuntimeError, match="General error"):
            display._ssh_kill_and_close_impl(mock_ssh, "fbi")


class TestCleanupSshChannels:
    """_cleanup_ssh_channels 関数のテスト"""

    def test_cleanup_ssh_channels_success(self, mocker):
        """チャンネルを正常にクローズできること"""
        from weather_display import display

        mock_stdin = mocker.MagicMock()
        mock_stdout = mocker.MagicMock()
        mock_stderr = mocker.MagicMock()

        display._cleanup_ssh_channels(mock_stdin, mock_stdout, mock_stderr)

        mock_stdin.close.assert_called_once()
        mock_stdout.close.assert_called_once()
        mock_stderr.close.assert_called_once()

    def test_cleanup_ssh_channels_with_none(self, mocker):
        """None のチャンネルを処理できること"""
        from weather_display import display

        mock_stdout = mocker.MagicMock()

        # 例外が発生しないこと
        display._cleanup_ssh_channels(None, mock_stdout, None)

        mock_stdout.close.assert_called_once()

    def test_cleanup_ssh_channels_handles_exception(self, mocker):
        """チャンネルクローズ時の例外を処理すること"""
        from weather_display import display

        mock_stdin = mocker.MagicMock()
        mock_stdin.close.side_effect = Exception("Close failed")

        # 例外が発生しないこと
        display._cleanup_ssh_channels(mock_stdin, None, None)
