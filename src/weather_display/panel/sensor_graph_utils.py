#!/usr/bin/env python3
"""センサーグラフ用ユーティリティ関数

アイコン描画およびエアコン電力データ取得に関する関数を提供します。
"""

from __future__ import annotations

import collections.abc
import datetime
import os

import matplotlib.axes
import matplotlib.offsetbox
import matplotlib.pyplot
import my_lib.sensor_data

import weather_display.config

# エアコン動作判定の閾値（W）
AIRCON_WORK_THRESHOLD = 30

# 無効値を示す定数
EMPTY_VALUE = -100.0


def get_aircon_power_requests(
    room_list: list[weather_display.config.RoomConfig],
) -> tuple[list[my_lib.sensor_data.DataRequest], dict[int, int]]:
    """エアコン電力取得用のリクエストリストを生成"""
    aircon_requests: list[my_lib.sensor_data.DataRequest] = []
    aircon_map: dict[int, int] = {}

    if os.environ.get("DUMMY_MODE", "false") == "true":
        start = "-169h"
        stop = "-168h"
    else:
        start = "-1h"
        stop = "now()"

    for col, room in enumerate(room_list):
        if room.aircon is not None:
            request_index = len(aircon_requests)
            aircon_map[col] = request_index
            aircon_requests.append(
                my_lib.sensor_data.DataRequest(
                    measure=room.aircon.measure,
                    hostname=room.aircon.hostname,
                    field="power",
                    start=start,
                    stop=stop,
                    last=True,
                )
            )

    return aircon_requests, aircon_map


def get_aircon_power_from_results(
    results: collections.abc.Sequence[my_lib.sensor_data.SensorDataResult | BaseException],
    aircon_map: dict[int, int],
    col: int,
) -> float | None:
    """並列取得結果からエアコン電力を取得"""
    if col not in aircon_map:
        return None

    data = results[aircon_map[col]]
    if isinstance(data, BaseException):
        return None
    if data.valid:
        return data.value[0]
    else:
        return None


def draw_aircon_icon(
    ax: matplotlib.axes.Axes,
    power: float | None,
    icon_config: weather_display.config.SensorIconConfig,
) -> None:
    """エアコン動作中アイコンを描画"""
    if (power is None) or (power < AIRCON_WORK_THRESHOLD):
        return

    icon_file = icon_config.aircon.path

    img = matplotlib.pyplot.imread(str(icon_file))

    imagebox = matplotlib.offsetbox.OffsetImage(img, zoom=0.3)
    imagebox.image.axes = ax

    ab = matplotlib.offsetbox.AnnotationBbox(
        offsetbox=imagebox,
        box_alignment=(0, 1),
        xycoords="axes fraction",
        xy=(0.05, 0.95),
        frameon=False,
    )
    ax.add_artist(ab)


def draw_light_icon(
    ax: matplotlib.axes.Axes,
    lux_list: list[float | None],
    icon_config: weather_display.config.SensorIconConfig,
) -> None:
    """照明状態アイコンを描画"""
    # NOTE: 下記の next の記法だとカバレッジが正しく取れない
    lux = next((item for item in reversed(lux_list) if item is not None), None)  # pragma: no cover

    now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=+9), "JST"))
    # NOTE: 昼間はアイコンを描画しない
    if (now.hour > 7) and (now.hour < 17):
        return

    if lux == EMPTY_VALUE:
        return
    elif lux is not None and lux < 10:
        icon_file = icon_config.light.off.path
    else:
        icon_file = icon_config.light.on.path

    img = matplotlib.pyplot.imread(str(icon_file))

    imagebox = matplotlib.offsetbox.OffsetImage(img, zoom=0.25)
    imagebox.image.axes = ax

    ab = matplotlib.offsetbox.AnnotationBbox(
        offsetbox=imagebox,
        box_alignment=(0, 1),
        xycoords="axes fraction",
        xy=(0, 1),
        frameon=False,
    )
    ax.add_artist(ab)
