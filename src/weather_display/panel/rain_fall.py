#!/usr/bin/env python3
"""
雨雲レーダー画像を生成します。

Usage:
  rain_cloud_panel.py [-c CONFIG] -o PNG_FILE [-D]

Options:
  -c CONFIG         : CONFIG を設定ファイルとして読み込んで実行します。[default: config.yaml]
  -o PNG_FILE       : 生成した画像を指定されたパスに保存します。
  -D                : デバッグモードで動作します。
"""

from __future__ import annotations

import datetime
import logging
import pathlib
import time
import traceback

import my_lib.font_util
import my_lib.notify.slack
import my_lib.panel_config
import my_lib.panel_util
import my_lib.pil_util
import my_lib.sensor_data
import PIL.Image
import PIL.ImageDraw
import PIL.ImageFont
import pytz

import weather_display.config

DATA_PATH = pathlib.Path("data")
WINDOW_SIZE_CACHE = DATA_PATH / "window_size.cache"
CACHE_EXPIRE_HOUR = 1

CLOUD_IMAGE_XPATH = '//div[contains(@id, "jmatile_map_")]'


FONT_SPEC: dict[str, my_lib.font_util.FontSpec] = {
    "value": ("en_bold", 80),
    "unit": ("en_bold", 30),
    "start": ("jp_medium", 40),
}


def get_face_map(
    font_config: my_lib.panel_config.FontConfigProtocol,
) -> dict[str, PIL.ImageFont.FreeTypeFont]:
    return my_lib.font_util.build_pil_face_map(font_config, FONT_SPEC)


def get_rainfall_status(
    rain_fall_config: weather_display.config.RainFallConfig,
    db_config: my_lib.sensor_data.InfluxDBConfig,
) -> dict[str, object] | None:
    START = "-3m"

    data = my_lib.sensor_data.fetch_data(
        db_config,
        rain_fall_config.sensor.measure,
        rain_fall_config.sensor.hostname,
        "rain",
        start=START,
        window_min=1,
    )

    if not data.valid:
        return None

    # NOTE:過去二分間の平均にする
    amount = (data.value[-1] + data.value[-2]) / 2.0 if len(data.value) > 1 else data.value[-1]

    # NOTE: 1分あたりの降水量なので、時間あたりに直す
    amount *= 60

    data = my_lib.sensor_data.fetch_data(
        db_config,
        rain_fall_config.sensor.measure,
        rain_fall_config.sensor.hostname,
        "raining",
        start=START,
        window_min=0,
        last=True,
    )

    raining_status = data.value[0]

    if raining_status:
        raining_start = my_lib.sensor_data.get_last_event(
            db_config,
            rain_fall_config.sensor.measure,
            rain_fall_config.sensor.hostname,
            "raining",
        )
    else:
        raining_start = None

    return {
        "amount": amount,
        "raining": {
            "status": raining_status,
            "start": raining_start,
        },
    }


def gen_amount_text(amount: float) -> str:
    if amount >= 10:
        return str(int(amount))
    elif (amount < 1) and (int(amount * 100) % 10 != 0):
        return f"{amount:.2f}"
    else:
        return f"{amount:.1f}"


def gen_start_text(start_time: datetime.datetime) -> str:
    delta = datetime.datetime.now(pytz.utc) - start_time.astimezone(pytz.utc)
    total_minutes = delta.total_seconds() // 60

    if total_minutes < 60:
        return f"({int(total_minutes)}分前〜)"
    elif total_minutes < 120:
        return f"(1時間{int(total_minutes - 60)}分前〜)"
    else:
        total_hours = total_minutes // 60
        return f"({int(total_hours)}時間前〜)"


def draw_rainfall(
    img: PIL.Image.Image,
    rainfall_status: dict[str, object],
    icon_config: weather_display.config.IconConfig,
    face_map: dict[str, PIL.ImageFont.FreeTypeFont],
) -> PIL.Image.Image:
    raining = rainfall_status["raining"]
    if not isinstance(raining, dict):
        return img

    if not raining["status"]:
        return img

    pos_x = 10
    pos_y = 70

    icon = my_lib.pil_util.load_image(icon_config)

    my_lib.pil_util.alpha_paste(
        img,
        icon,
        (pos_x, pos_y),
    )

    amount = rainfall_status["amount"]
    if not isinstance(amount, int | float) or amount < 0.01:
        return img

    amount_text = gen_amount_text(amount)

    start = raining["start"]
    if not isinstance(start, datetime.datetime):
        return img

    start_text = gen_start_text(start)

    line_height = my_lib.pil_util.text_size(img, face_map["value"], "0")[1]

    pos_y = pos_y + icon.size[1] + 10

    next_pos_x = my_lib.pil_util.draw_text(
        img,
        amount_text,
        (pos_x, pos_y + line_height - my_lib.pil_util.text_size(img, face_map["value"], "0")[1]),
        face_map["value"],
        "left",
        "#333",
        stroke_width=10,
        stroke_fill=(255, 255, 255, 200),
    )[0]
    next_pos_x += my_lib.pil_util.text_size(img, face_map["unit"], " ")[0]
    next_pos_x = my_lib.pil_util.draw_text(
        img,
        "mm/h",
        (next_pos_x, pos_y + line_height - my_lib.pil_util.text_size(img, face_map["unit"], "h")[1]),
        face_map["unit"],
        "left",
        "#333",
        stroke_width=10,
        stroke_fill=(255, 255, 255, 200),
    )[0]
    next_pos_x += my_lib.pil_util.text_size(img, face_map["start"], " ")[0]

    pos_y = int(pos_y + line_height * 1.2)
    my_lib.pil_util.draw_text(
        img,
        start_text,
        (pos_x, pos_y),
        face_map["start"],
        "left",
        "#333",
        stroke_width=10,
        stroke_fill=(255, 255, 255, 200),
    )

    return img


def create_rain_fall_panel_impl(
    rain_fall_config: weather_display.config.RainFallConfig,
    context: my_lib.panel_config.DatabasePanelContext,
) -> PIL.Image.Image:
    face_map = get_face_map(context.font_config)

    img = PIL.Image.new(
        "RGBA",
        (rain_fall_config.panel.width, rain_fall_config.panel.height),
        (255, 255, 255, 0),
    )

    status = get_rainfall_status(rain_fall_config, context.db_config)

    if status is None:
        logging.warning("Unable to fetch rainfall status")
        return img

    draw_rainfall(img, status, rain_fall_config.icon, face_map)

    return img


def create(
    config: weather_display.config.AppConfig,
) -> tuple[PIL.Image.Image, float] | tuple[PIL.Image.Image, float, str]:
    logging.info("draw rain fall panel")

    assert config.rain_fall is not None  # noqa: S101

    start = time.perf_counter()

    context = my_lib.panel_config.DatabasePanelContext(
        font_config=config.font,
        db_config=config.influxdb,
    )

    try:
        return (
            create_rain_fall_panel_impl(config.rain_fall, context),
            time.perf_counter() - start,
        )
    except Exception:
        logging.exception("Failed to draw panel")

        error_message = traceback.format_exc()
        return (
            my_lib.panel_util.create_error_image(config.rain_fall, context.font_config, error_message),
            time.perf_counter() - start,
            error_message,
        )


if __name__ == "__main__":
    # TEST Code
    import docopt
    import my_lib.logger

    assert __doc__ is not None  # noqa: S101
    args = docopt.docopt(__doc__)

    config_file = args["-c"]
    out_file = args["-o"]
    debug_mode = args["-D"]

    my_lib.logger.init("test", level=logging.DEBUG if debug_mode else logging.INFO)

    config = weather_display.config.load(config_file)

    img = create(config)[0]

    logging.info("Save %s.", out_file)
    my_lib.pil_util.convert_to_gray(img).save(out_file, "PNG")

    logging.info("Finish.")
