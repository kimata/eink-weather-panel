#!/usr/bin/env python3
"""
電子ペーパ表示用の画像を表示します。

Usage:
  display_image.py [-c CONFIG] [-s HOST] [-p PORT] [-S] [-t] [-O] [-D]

Options:
  -c CONFIG         : CONFIG を設定ファイルとして読み込んで実行します。[default: config.yaml]
  -S                : 小型ディスプレイモードで実行します。
  -t                : テストモードで実行します。
  -s HOST           : 表示を行う Raspberry Pi のホスト名。
  -p PORT           : メトリクス表示用のサーバーを動かすポート番号。[default: 5000]
  -O                : 1回のみ表示
  -D                : デバッグモードで動作します。
"""

from __future__ import annotations

import datetime
import faulthandler
import logging
import os
import pathlib
import signal
import sys
import threading
import time
import traceback
import zoneinfo
from typing import TYPE_CHECKING

import my_lib.footprint
import my_lib.panel_util
import my_lib.proc_util

import weather_display.config
import weather_display.display
import weather_display.metrics.collector
import weather_display.metrics.server
import weather_display.timing_filter
from weather_display.config import AppConfig

if TYPE_CHECKING:
    import paramiko

TIMEZONE = zoneinfo.ZoneInfo("Asia/Tokyo")

SCHEMA_CONFIG = "config.schema"
SCHEMA_CONFIG_SMALL = "config-small.schema"


NOTIFY_THRESHOLD = 2

should_terminate = threading.Event()


def sig_handler(num: int, frame: object) -> None:  # noqa: ARG001
    global should_terminate

    logging.warning("receive signal %d", num)

    # シグナル受信時のスレッド状態を記録
    logging.info("Active threads at signal: %d", threading.active_count())
    for thread in threading.enumerate():
        logging.info("  Thread: %s (daemon=%s, alive=%s)", thread.name, thread.daemon, thread.is_alive())

    if num in (signal.SIGTERM, signal.SIGINT):
        should_terminate.set()
    elif num == signal.SIGUSR1:
        # SIGUSR1を受け取ったらスレッドダンプを出力
        faulthandler.dump_traceback()


def execute(  # noqa: PLR0913
    config: AppConfig,
    rasp_hostname: str,
    key_file_path: pathlib.Path | str,
    config_file: str,
    small_mode: bool,
    test_mode: bool,
    is_one_time: bool,
    prev_ssh: paramiko.SSHClient | None = None,
    timing_controller: weather_display.timing_filter.TimingController | None = None,
) -> tuple[paramiko.SSHClient | None, float, weather_display.timing_filter.TimingController | None]:
    start_time = datetime.datetime.now(TIMEZONE)
    start = time.perf_counter()
    success = True
    error_message: str | None = None
    sleep_time = 60.0
    diff_sec = 0.0

    try:
        weather_display.display.ssh_kill_and_close(prev_ssh, "fbi")

        ssh = weather_display.display.ssh_connect(rasp_hostname, str(key_file_path))

        weather_display.display.execute(ssh, config, config_file, small_mode, test_mode)

        if is_one_time:
            diff_sec = 0
        else:
            # diff_secはtiming_controllerで計算されるため、ここでは初期化のみ
            diff_sec = 0

            # NOTE: 更新されていることが直感的に理解しやすくなるように、
            # 更新完了タイミングを各分の 0 秒に合わせる
            elapsed = time.perf_counter() - start

            # カルマンフィルタを使用したタイミング制御
            if timing_controller is None:
                timing_controller = weather_display.timing_filter.TimingController(
                    update_interval=config.panel.update.interval, target_second=0
                )

            sleep_time, diff_sec = timing_controller.calculate_sleep_time(
                elapsed, datetime.datetime.now(TIMEZONE)
            )

            # タイミングのずれが大きい場合は警告
            if abs(diff_sec) > 3:
                logging.warning("Update timing gap is large: %d", diff_sec)

    except Exception as e:
        success = False
        error_message = str(e)
        logging.exception("execute failed")
        ssh = prev_ssh  # Return previous ssh connection on error

    finally:
        # Log metrics to database
        elapsed_time = time.perf_counter() - start
        try:
            db_path = config.metrics.data if config.metrics is not None else None
            weather_display.metrics.collector.collect_display_image_metrics(
                elapsed_time=elapsed_time,
                is_small_mode=small_mode,
                is_test_mode=test_mode,
                is_one_time=is_one_time,
                rasp_hostname=rasp_hostname,
                success=success,
                error_message=error_message,
                timestamp=start_time,
                sleep_time=sleep_time,
                diff_sec=diff_sec,
                db_path=db_path,
            )
        except Exception as e:
            logging.warning("Failed to log execute metrics: %s", e)

    return ssh, sleep_time, timing_controller


def start(
    config: AppConfig,
    rasp_hostname: str,
    key_file_path: pathlib.Path | str,
    config_file: str,
    small_mode: bool,
    test_mode: bool,
    is_one_time: bool,
) -> None:
    fail_count = 0
    prev_ssh: object = None
    timing_controller: weather_display.timing_filter.TimingController | None = None

    logging.info("Start worker")

    while True:
        try:
            prev_ssh, sleep_time, timing_controller = execute(
                config,
                rasp_hostname,
                key_file_path,
                config_file,
                small_mode,
                test_mode,
                is_one_time,
                prev_ssh,
                timing_controller,
            )
            fail_count = 0

            if is_one_time:
                break

            logging.info("sleep %.1f sec...", sleep_time)

            should_terminate.wait(timeout=sleep_time)
            if should_terminate.is_set():
                logging.info("Terminate worker")
                break
        except Exception:
            logging.exception("Failed to display image")
            fail_count += 1
            if is_one_time or (fail_count >= NOTIFY_THRESHOLD):
                my_lib.panel_util.notify_error(
                    config.slack,
                    "weather_panel",
                    traceback.format_exc(),
                )
                logging.error("エラーが続いたので終了します。")  # noqa: TRY400
                sys.stderr.flush()
                time.sleep(1)
                raise
            time.sleep(10)

    logging.info("Stop worker")


def cleanup(handle: weather_display.metrics.server.MetricsServerHandle) -> None:
    # アクティブなスレッドを確認
    logging.info("Active threads before cleanup: %d", threading.active_count())
    for thread in threading.enumerate():
        logging.info("  Thread: %s (daemon=%s, alive=%s)", thread.name, thread.daemon, thread.is_alive())

    # メトリクスサーバーを停止
    logging.info("Stopping metrics server...")
    weather_display.metrics.server.term(handle)
    logging.info("Metrics server stopped")

    # 残存スレッドの詳細を確認
    logging.info("Active threads after server stop: %d", threading.active_count())
    for thread in threading.enumerate():
        logging.info("  Thread: %s (daemon=%s, alive=%s)", thread.name, thread.daemon, thread.is_alive())
        if thread.daemon and thread.is_alive() and thread.name != "MainThread":
            logging.info(
                "    Note: Daemon thread %s is still alive but will be terminated on exit", thread.name
            )

    # 子プロセスを終了
    logging.info("Killing child processes...")
    my_lib.proc_util.kill_child()
    logging.info("Child processes killed")

    # 最終的なスレッド状態を確認
    logging.info("Active threads after cleanup: %d", threading.active_count())
    for thread in threading.enumerate():
        logging.info("  Thread: %s (daemon=%s, alive=%s)", thread.name, thread.daemon, thread.is_alive())

    # プロセス終了
    logging.info("Graceful shutdown completed")
    sys.exit(0)


if __name__ == "__main__":
    import docopt
    import my_lib.logger

    assert __doc__ is not None
    args = docopt.docopt(__doc__)

    config_file = args["-c"]
    is_one_time = args["-O"]
    small_mode = args["-S"]
    rasp_hostname = os.environ.get("RASP_HOSTNAME", args["-s"])
    metrics_port = int(args["-p"])
    test_mode = args["-t"]
    debug_mode = args["-D"]

    my_lib.logger.init("panel.e-ink.weather", level=logging.DEBUG if debug_mode else logging.INFO)

    key_file_path = os.environ.get(
        "SSH_KEY",
        pathlib.Path("key/panel.id_rsa"),
    )

    if rasp_hostname is None:
        raise ValueError("HOSTNAME is required")

    config = weather_display.config.load(
        config_file, pathlib.Path(SCHEMA_CONFIG_SMALL if small_mode else SCHEMA_CONFIG)
    )

    logging.info("Raspberry Pi hostname: %s", rasp_hostname)

    signal.signal(signal.SIGTERM, sig_handler)
    signal.signal(signal.SIGUSR1, sig_handler)  # デバッグ用

    # faulthandlerを有効化（タイムアウト時にスレッドダンプを出力）
    faulthandler.enable()

    handle = weather_display.metrics.server.start(config, metrics_port)

    start(config, rasp_hostname, key_file_path, config_file, small_mode, test_mode, is_one_time)

    cleanup(handle)
