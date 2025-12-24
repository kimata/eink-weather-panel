#!/usr/bin/env python3
"""
暑さ指数(WBGP)の画像を生成します。

Usage:
  wbgt_panel.py [-c CONFIG] -o PNG_FILE [-D]

Options:
  -c CONFIG         : CONFIG を設定ファイルとして読み込んで実行します。[default: config.yaml]
  -o PNG_FILE       : 生成した画像を指定されたパスに保存します。
  -D                : デバッグモードで動作します。
"""

from __future__ import annotations

import logging

import my_lib.panel_util
import my_lib.pil_util
import my_lib.weather
import PIL.Image
import PIL.ImageDraw
import PIL.ImageEnhance
import PIL.ImageFont
import my_lib.notify.slack
import my_lib.panel_config
from my_lib.weather import get_wbgt

from weather_display.config import AppConfig, WbgtConfig, WbgtIconConfig


def get_face_map(font_config: my_lib.panel_config.FontConfigProtocol) -> dict[str, PIL.ImageFont.FreeTypeFont]:
    return {
        "wbgt": my_lib.pil_util.get_font(font_config, "en_bold", 80),
        "wbgt_symbol": my_lib.pil_util.get_font(font_config, "jp_bold", 120),
        "wbgt_title": my_lib.pil_util.get_font(font_config, "jp_medium", 30),
    }


def draw_wbgt(
    img: PIL.Image.Image,
    wbgt: float,
    wbgt_config: WbgtConfig,
    icon_config: WbgtIconConfig,
    face_map: dict[str, PIL.ImageFont.FreeTypeFont],
) -> PIL.Image.Image:
    title = "暑さ指数:"
    wbgt_str = f"{wbgt:.1f}"

    if wbgt >= 31:
        index = 4
    elif wbgt >= 28:
        index = 3
    elif wbgt >= 25:
        index = 2
    elif wbgt >= 21:
        index = 1
    else:
        index = 0

    icon = my_lib.pil_util.load_image(icon_config.face[index])

    pos_x = wbgt_config.panel.width - 10
    pos_y = 10

    my_lib.pil_util.alpha_paste(
        img,
        icon,
        (int(pos_x - icon.size[0]), pos_y),
    )

    pos_y += icon.size[1] + 10

    next_pos_y = my_lib.pil_util.draw_text(
        img,
        title,
        (pos_x, pos_y),
        face_map["wbgt_title"],
        "right",
        "#333",
        stroke_width=10,
        stroke_fill=(255, 255, 255, 200),
    )[1]
    next_pos_y += 12
    my_lib.pil_util.draw_text(
        img,
        wbgt_str,
        (pos_x, next_pos_y),
        face_map["wbgt"],
        "right",
        "#333",
        stroke_width=10,
        stroke_fill=(255, 255, 255, 200),
    )

    return img


def create_wbgt_panel_impl(
    panel_config: my_lib.panel_config.PanelConfigProtocol,
    font_config: my_lib.panel_config.FontConfigProtocol,
    slack_config: my_lib.notify.slack.SlackEmptyConfig,  # noqa: ARG001
    is_side_by_side: bool,  # noqa: ARG001
    trial: int,  # noqa: ARG001
    opt_config: object = None,  # noqa: ARG001
) -> PIL.Image.Image:
    # panel_config is WbgtConfig
    wbgt_config: WbgtConfig = panel_config  # type: ignore[assignment]

    face_map = get_face_map(font_config)

    img = PIL.Image.new(
        "RGBA",
        (wbgt_config.panel.width, wbgt_config.panel.height),
        (255, 255, 255, 0),
    )

    wbgt = get_wbgt(wbgt_config.data.env_go.url).current

    if wbgt is None:
        return img

    draw_wbgt(img, wbgt, wbgt_config, wbgt_config.icon, face_map)

    return img


def create(config: AppConfig, is_side_by_side: bool = True) -> tuple[PIL.Image.Image, float] | tuple[PIL.Image.Image, float, str]:
    logging.info("draw WBGT panel")

    return my_lib.panel_util.draw_panel_patiently(
        create_wbgt_panel_impl, config.wbgt, config.font, my_lib.notify.slack.SlackEmptyConfig(), is_side_by_side, error_image=False
    )


if __name__ == "__main__":
    # TEST Code
    import docopt
    import my_lib.logger

    from weather_display.config import load

    args = docopt.docopt(__doc__)

    config_file = args["-c"]
    out_file = args["-o"]
    debug_mode = args["-D"]

    my_lib.logger.init("test", level=logging.DEBUG if debug_mode else logging.INFO)

    config = load(config_file)

    img = create(config)[0]

    logging.info("Save %s.", out_file)
    my_lib.pil_util.convert_to_gray(img).save(out_file, "PNG")

    logging.info("Finish.")
