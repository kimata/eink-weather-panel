from __future__ import annotations

import contextlib
import logging
import os
import pathlib
import signal
import subprocess
import sys
import time
import traceback

import my_lib.footprint
import my_lib.panel_util
import my_lib.proc_util
import paramiko

import create_image
from weather_display.config import AppConfig

RETRY_COUNT = 3
RETRY_WAIT = 2
CREATE_IMAGE = pathlib.Path(__file__).parent.parent / "create_image.py"


def exec_patiently(func, args):
    for i in range(RETRY_COUNT):
        try:
            return func(*args)
        except Exception:  # noqa: PERF203
            if i == (RETRY_COUNT - 1):
                raise
            logging.warning(traceback.format_exc())
            time.sleep(RETRY_WAIT)
    return None  # pragma: no cover  # 論理的に到達不能（ループは必ず return か raise で終了）


def ssh_connect_impl(hostname, key_filename):
    logging.info("Connect to %s", hostname)

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())  # noqa: S507

    try:
        with open(key_filename) as f:  # noqa: PTH123
            ssh.connect(
                hostname,
                username="ubuntu",
                pkey=paramiko.RSAKey.from_private_key(f),
                allow_agent=False,
                look_for_keys=False,
                timeout=2,
                auth_timeout=2,
            )
    except Exception:
        # 接続失敗時にSSHクライアントをクローズしてリソースリークを防止
        with contextlib.suppress(Exception):
            ssh.close()
        raise

    return ssh


def ssh_kill_and_close_impl(ssh, cmd):
    if ssh is None:
        return

    try:
        # NOTE: fbi コマンドのプロセスが残るので強制終了させる
        stdin, stdout, stderr = ssh.exec_command(f"sudo killall -9 {cmd}")

        # SSHコマンドの完了を待機してゾンビプロセスを防止
        stdout.channel.recv_exit_status()

        # チャンネルのクリーンアップ
        try:
            stdin.close()
            stdout.close()
            stderr.close()
        except Exception as e:
            logging.warning("Error closing SSH command channels: %s", e)

        ssh.close()
        return
    except AttributeError:
        return
    except Exception:
        raise


def ssh_kill_and_close(ssh, cmd):
    exec_patiently(ssh_kill_and_close_impl, (ssh, cmd))


def ssh_connect(hostname, key_file_path):
    return exec_patiently(ssh_connect_impl, (hostname, key_file_path))


def terminate_session_processes(session_id):
    """セッションIDに属する全プロセスを段階的に終了する"""
    try:
        # セッションIDに属する全プロセスを取得
        result = subprocess.run(  # noqa: S603
            ["/bin/ps", "-s", str(session_id), "-o", "pid="], capture_output=True, text=True, check=False
        )

        if result.returncode == 0 and result.stdout:
            pids = [int(pid.strip()) for pid in result.stdout.strip().split() if pid.strip()]

            # SIGTERM送信
            for pid in pids:
                with contextlib.suppress(ProcessLookupError):
                    os.kill(pid, signal.SIGTERM)

            time.sleep(2)

            # まだ残っているプロセスにSIGKILL送信
            for pid in pids:
                with contextlib.suppress(ProcessLookupError):
                    os.kill(pid, signal.SIGKILL)
    except Exception as e:
        logging.warning("Error terminating session processes: %s", e)


def _cleanup_ssh_channels(ssh_stdin, ssh_stdout, ssh_stderr):
    """SSHチャンネルを安全にクローズする"""
    for channel in [ssh_stdin, ssh_stdout, ssh_stderr]:
        if channel is not None:
            with contextlib.suppress(Exception):
                channel.close()


def execute(
    ssh: object,
    config: AppConfig,
    config_file: str,
    small_mode: bool,
    test_mode: bool,
) -> None:
    ssh_stdin = None
    ssh_stdout = None
    ssh_stderr = None

    try:
        ssh_stdin, ssh_stdout, ssh_stderr = exec_patiently(
            ssh.exec_command,
            (
                "cat - > /dev/shm/display.png && "
                "sudo fbi -1 -T 1 -d /dev/fb0 --noverbose /dev/shm/display.png; echo $?",
            ),
        )

        logging.info("Start drawing.")

        cmd = ["python3", CREATE_IMAGE, "-c", config_file]
        if small_mode:
            cmd.append("-S")
        if test_mode:
            cmd.append("-t")

        # セッション管理でプロセスグループを作成してゾンビプロセス対策
        proc = subprocess.Popen(  # noqa: S603
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            start_new_session=True,  # 新しいセッションを作成
        )

        # セッションIDを取得（プロセスIDと同じ）
        session_id = proc.pid

        try:
            # タイムアウト付きでプロセスの完了を待機
            stdout_data, stderr_data = proc.communicate(timeout=300)  # 5分でタイムアウト
        except subprocess.TimeoutExpired:
            logging.warning("create_image.py process timed out, terminating session %d...", session_id)
            terminate_session_processes(session_id)
            my_lib.proc_util.reap_zombie()
            timeout_msg = "Image creation process timed out"
            raise RuntimeError(timeout_msg) from None

        ssh_stdin.write(stdout_data)

        ssh_stdin.flush()
        ssh_stdin.channel.shutdown_write()

        logging.info(stderr_data.decode("utf-8").rstrip())

        # SSH接続の終了ステータスを取得
        fbi_status = ssh_stdout.channel.recv_exit_status()

        # NOTE: -24 は create_image.py の異常時の終了コードに合わせる。
        if (fbi_status == 0) and (proc.returncode == 0):
            logging.info("Succeeded.")
            my_lib.footprint.update(config.liveness.file.display)
        elif proc.returncode == create_image.ERROR_CODE_MAJOR:
            logging.warning("Failed to create image at all. (code: %d)", proc.returncode)
        elif proc.returncode == create_image.ERROR_CODE_MINOR:
            logging.warning("Failed to create image partially. (code: %d)", proc.returncode)
            my_lib.footprint.update(config.liveness.file.display)
        elif fbi_status != 0:
            logging.warning("Failed to display image. (code: %d)", fbi_status)
            logging.warning("[stdout] %s", ssh_stdout.read().decode("utf-8"))
            logging.warning("[stderr] %s", ssh_stderr.read().decode("utf-8"))
        else:
            logging.error("Failed to create image. (code: %d)", proc.returncode)
            sys.exit(proc.returncode)
    finally:
        # 例外発生時も含め、SSHチャンネルを確実にクリーンアップ
        _cleanup_ssh_channels(ssh_stdin, ssh_stdout, ssh_stderr)
        # プロセス終了後に必ずゾンビプロセスを回収
        my_lib.proc_util.reap_zombie()
