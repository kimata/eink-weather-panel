#!/usr/bin/env python3
"""
電子ペーパ表示用の画像を生成します。

Usage:
  create_image.py [-c CONFIG] [-S] [-o PNG_FILE] [-t] [-D] [-d]

Options:
  -c CONFIG         : CONFIG を設定ファイルとして読み込んで実行します。[default: config.yaml]
  -S                : 小型ディスプレイモードで実行します。
  -o PNG_FILE       : 生成した画像を指定されたパスに保存します。
  -t                : テストモードで実行します。
  -d                : ダミーモードで実行します。
  -D                : デバッグモードで動作します。
"""

from __future__ import annotations

import faulthandler
import logging
import multiprocessing
import multiprocessing.pool
import os
import pathlib
import sys
import textwrap
import threading
import time
import traceback
from collections.abc import Callable
from typing import Any

import my_lib.panel_config
import my_lib.panel_util
import my_lib.pil_util
import my_lib.proc_util
import PIL.Image
import PIL.ImageDraw

import weather_display.config
import weather_display.metrics.collector
import weather_display.panel.power_graph
import weather_display.panel.rain_cloud
import weather_display.panel.rain_fall
import weather_display.panel.sensor_graph
import weather_display.panel.time
import weather_display.panel.wbgt
import weather_display.panel.weather

# パネル関数の型エイリアス
PanelFunc = Callable[..., tuple[PIL.Image.Image, float] | tuple[PIL.Image.Image, float, str]]

SCHEMA_CONFIG = "schema/config.schema"
SCHEMA_CONFIG_SMALL = "schema/config-small.schema"

# 一部の描画でエラー
ERROR_CODE_MINOR = 220
# 描画全体がエラー
ERROR_CODE_MAJOR = 222


def draw_wall(config: weather_display.config.AppConfig, img: PIL.Image.Image) -> None:
    for wall_image in config.wall.image:
        my_lib.pil_util.alpha_paste(
            img,
            my_lib.pil_util.load_image(wall_image),
            (wall_image.offset_x, wall_image.offset_y),
        )


def draw_panel(
    config: weather_display.config.AppConfig,
    img: PIL.Image.Image,
    is_small_mode: bool = False,
    is_test_mode: bool = False,
    is_dummy_mode: bool = False,
) -> int:
    # パネル定義: (name, func, extra_args)
    panel_defs: list[tuple[str, PanelFunc, tuple[Any, ...]]] = []
    if is_small_mode:
        panel_defs = [
            ("rain_cloud", weather_display.panel.rain_cloud.create, (True,)),
            ("weather", weather_display.panel.weather.create, (False,)),
            ("wbgt", weather_display.panel.wbgt.create, ()),
            ("time", weather_display.panel.time.create, ()),
        ]
    else:
        panel_defs = [
            ("rain_cloud", weather_display.panel.rain_cloud.create, ()),
            ("sensor", weather_display.panel.sensor_graph.create, ()),
            ("power", weather_display.panel.power_graph.create, ()),
            ("weather", weather_display.panel.weather.create, ()),
            ("wbgt", weather_display.panel.wbgt.create, ()),
            ("rain_fall", weather_display.panel.rain_fall.create, ()),
            ("time", weather_display.panel.time.create, ()),
        ]

    panel_map: dict[str, PIL.Image.Image] = {}
    panel_metrics: list[dict[str, object]] = []
    tasks: dict[str, multiprocessing.pool.AsyncResult[Any]] = {}

    # NOTE: 並列処理 (matplotlib はマルチスレッド対応していないので、マルチプロセス処理する)
    # with ステートメントで確実にPoolをクリーンアップする
    start = time.perf_counter()
    with multiprocessing.Pool(processes=len(panel_defs)) as pool:
        for name, func, extra_args in panel_defs:
            arg: tuple[Any, ...] = (config, *extra_args)
            tasks[name] = pool.apply_async(func, arg)

        pool.close()
        pool.join()

    ret = 0
    for name, _func, _extra_args in panel_defs:
        result = tasks[name].get()
        panel_img = result[0]
        elapsed = result[1]
        has_error = len(result) > 2
        error_message: str | None = result[2] if has_error else None

        if has_error:
            assert error_message is not None  # noqa: S101
            my_lib.panel_util.notify_error(
                config.slack,
                "weather_panel",
                error_message,
            )
            ret = ERROR_CODE_MINOR

        panel_map[name] = panel_img
        panel_metrics.append(
            {
                "name": name,
                "elapsed_time": elapsed,
                "has_error": has_error,
                "error_message": error_message,
            }
        )

        logging.info("elapsed time: %s panel = %.3f sec", name, elapsed)

    total_elapsed_time = time.perf_counter() - start
    logging.info("total elapsed time: %.3f sec", total_elapsed_time)

    # Log metrics to database
    try:
        db_path = config.metrics.data if config.metrics is not None else None
        weather_display.metrics.collector.collect_draw_panel_metrics(
            total_elapsed_time=total_elapsed_time,
            panel_metrics=panel_metrics,
            is_small_mode=is_small_mode,
            is_test_mode=is_test_mode,
            is_dummy_mode=is_dummy_mode,
            error_code=ret,
            db_path=db_path,
        )
    except Exception as e:
        logging.warning("Failed to log draw_panel metrics: %s", e)

    draw_wall(config, img)

    # パネル配置順序とオフセット取得用マッピング
    panel_configs: dict[str, my_lib.panel_config.PanelGeometry] = {
        "power": config.power.panel,
        "weather": config.weather.panel,
        "rain_cloud": config.rain_cloud.panel,
        "wbgt": config.wbgt.panel,
        "time": config.time.panel,
    }
    # オプショナルなパネル設定を追加
    if config.sensor is not None:
        panel_configs["sensor"] = config.sensor.panel
    if config.rain_fall is not None:
        panel_configs["rain_fall"] = config.rain_fall.panel

    for name in ["power", "weather", "sensor", "rain_cloud", "wbgt", "rain_fall", "time"]:
        if name not in panel_map or name not in panel_configs:
            continue

        panel_cfg = panel_configs[name]
        my_lib.pil_util.alpha_paste(
            img,
            panel_map[name],
            (panel_cfg.offset_x, panel_cfg.offset_y),
        )

    return ret


def create_image(
    config: weather_display.config.AppConfig,
    small_mode: bool = False,
    dummy_mode: bool = False,
    test_mode: bool = False,
) -> tuple[PIL.Image.Image, int]:
    # NOTE: オプションでダミーモードが指定された場合、環境変数もそれに揃えておく
    if dummy_mode:
        logging.warning("Set dummy mode")
        os.environ["DUMMY_MODE"] = "true"
    else:  # pragma: no cover
        pass

    logging.info("Start to create image")
    logging.info("Mode : %s", "small" if small_mode else "normal")

    img = PIL.Image.new(
        "RGBA",
        (config.panel.device.width, config.panel.device.height),
        (255, 255, 255, 255),
    )
    if test_mode:
        return (img, 0)

    try:
        ret = draw_panel(config, img, small_mode, test_mode, dummy_mode)

        return (img, ret)
    except Exception:
        draw = PIL.ImageDraw.Draw(img)
        draw.rectangle(
            (
                0,
                0,
                config.panel.device.width,
                config.panel.device.height,
            ),
            fill=(255, 255, 255, 255),
        )

        my_lib.pil_util.draw_text(
            img,
            "ERROR",
            (10, 10),
            my_lib.pil_util.get_font(config.font, "en_bold", 160),
            "left",
            "#666",
        )

        my_lib.pil_util.draw_text(
            img,
            "\n".join(textwrap.wrap(traceback.format_exc(), 100)),
            (20, 200),
            my_lib.pil_util.get_font(config.font, "en_medium", 40),
            "left",
            "#333",
        )
        my_lib.panel_util.notify_error(
            config.slack,
            "weather_panel",
            traceback.format_exc(),
        )

        return (img, ERROR_CODE_MAJOR)


if __name__ == "__main__":
    import docopt
    import my_lib.logger

    assert __doc__ is not None  # noqa: S101
    args = docopt.docopt(__doc__)

    config_file = args["-c"]
    small_mode = args["-S"]
    dummy_mode = args["-d"]
    test_mode = args["-t"]
    debug_mode = args["-D"]
    out_file = args["-o"] if args["-o"] is not None else sys.stdout.buffer

    my_lib.logger.init("panel.e-ink.weather", level=logging.DEBUG if debug_mode else logging.INFO)

    # faulthandlerを有効化（タイムアウト時にスレッドダンプを出力）
    faulthandler.enable()

    config = weather_display.config.load(
        config_file, pathlib.Path(SCHEMA_CONFIG_SMALL if small_mode else SCHEMA_CONFIG)
    )

    img, status = create_image(config, small_mode, dummy_mode, test_mode)

    logging.info("Save %s.", out_file)
    my_lib.pil_util.convert_to_gray(img).save(out_file, "PNG")

    if status == 0:
        logging.info("create_image: Succeeded.")
    else:
        logging.warning("create_image: Something wrong..")

    logging.info("Finish.")

    # アクティブなスレッドを確認
    logging.info("Active threads before cleanup: %d", threading.active_count())
    for thread in threading.enumerate():
        logging.info("  Thread: %s (daemon=%s, alive=%s)", thread.name, thread.daemon, thread.is_alive())
        if thread.daemon and thread.is_alive() and thread.name != "MainThread":
            logging.info("    Note: Daemon thread %s will be terminated on exit", thread.name)

    # 終了前にゾンビプロセスを回収
    logging.info("Reaping zombie processes...")
    try:
        my_lib.proc_util.reap_zombie()
        logging.info("Zombie processes reaped")
    except Exception as e:
        logging.warning("Failed to reap zombie processes: %s", e)

    # 最終的なスレッド状態を確認
    logging.info("Active threads after cleanup: %d", threading.active_count())
    for thread in threading.enumerate():
        logging.info("  Thread: %s (daemon=%s, alive=%s)", thread.name, thread.daemon, thread.is_alive())

    sys.exit(status)
