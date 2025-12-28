#!/usr/bin/env python3
"""
センサーグラフを生成します。

Usage:
  sensor_graph.py [-c CONFIG] -o PNG_FILE [-D]

Options:
  -c CONFIG         : CONFIG を設定ファイルとして読み込んで実行します。[default: config.yaml]
  -o PNG_FILE       : 生成した画像を指定されたパスに保存します。
  -D                : デバッグモードで動作します。
"""

from __future__ import annotations

import asyncio
import datetime
import functools
from dataclasses import dataclass, field
import io
import logging
import os
import time
import traceback

import matplotlib  # noqa: ICN001
import matplotlib.axes
import matplotlib.dates
import matplotlib.font_manager
import matplotlib.gridspec
import matplotlib.pyplot  # noqa: ICN001
import matplotlib.ticker
import my_lib.font_util
import my_lib.panel_config
import my_lib.panel_util
import my_lib.plot_util
import pandas.plotting
import PIL.Image
from my_lib.sensor_data import DataRequest, SensorDataResult, fetch_data_parallel

from weather_display.config import (
    AppConfig,
    SensorConfig,
)
from weather_display.panel.sensor_graph_utils import (
    EMPTY_VALUE,
    draw_aircon_icon,
    draw_light_icon,
    get_aircon_power_from_results,
    get_aircon_power_requests,
)

matplotlib.use("Agg")

pandas.plotting.register_matplotlib_converters()

IMAGE_DPI = 100.0


@dataclass
class PlotData:
    """グラフ描画用のデータ構造"""

    valid: bool = False
    time: list[datetime.datetime] = field(default_factory=list)
    time_numeric: list[float] = field(default_factory=list)
    value: list[float | None] = field(default_factory=list)


@dataclass
class AxisConfig:
    """軸設定用のデータ構造"""

    major_locator: matplotlib.ticker.Locator
    major_formatter: matplotlib.ticker.Formatter


@functools.lru_cache(maxsize=8)
def get_shared_axis_config() -> AxisConfig:
    """共通の軸設定を返す（キャッシュ付き）"""
    return AxisConfig(
        major_locator=matplotlib.dates.DayLocator(interval=1),
        major_formatter=matplotlib.dates.DateFormatter("%-d"),
    )


FONT_SPEC: dict[str, my_lib.font_util.FontSpec] = {
    "title": ("jp_bold", 34),
    "value": ("en_cond", 65),
    "value_small": ("en_cond", 55),
    "value_unit": ("jp_regular", 18),
    "yaxis": ("jp_regular", 20),
    "xaxis": ("en_medium", 20),
}


def get_face_map(font_config: my_lib.panel_config.FontConfigProtocol) -> dict[str, matplotlib.font_manager.FontProperties]:
    return my_lib.font_util.build_plot_face_map(font_config, FONT_SPEC)


def plot_item(  # noqa: PLR0913
    ax: matplotlib.axes.Axes,
    title: str | None,
    unit: str,
    data: PlotData | None,
    xbegin_numeric: float,
    ylim: tuple[float, float],
    fmt: str,
    scale: str,
    small: bool,
    face_map: dict[str, matplotlib.font_manager.FontProperties],
    axis_config: AxisConfig,
) -> None:
    logging.info("Plot %s", title)

    # データがNoneの場合のフォールバック
    if data is None:
        logging.warning("plot_item received invalid data: %s", type(data))
        data = PlotData()

    # 事前に数値化された時間データを使用
    x = data.time_numeric if data.time_numeric else data.time
    y_raw = data.value
    y = list(y_raw) if y_raw else []

    if not data.valid:
        text = "?"
    else:
        # NOTE: 下記の next の記法だとカバレッジが正しく取れない
        text = fmt.format(next((item for item in reversed(y) if item is not None), None))  # pragma: no cover

    if scale == "log":
        # NOTE: エラーが出ないように値を補正
        y = [1 if (i is None or i < 1) else i for i in y]

    if title is not None:
        ax.set_title(title, fontproperties=face_map["title"], color="#333333")

    ax.set_ylim(ylim)

    # 数値化済みの時間範囲を設定
    time_numeric = data.time_numeric
    if time_numeric and len(time_numeric) > 0:
        # 3時間分のマージンを数値で追加（3時間 = 3/24日）
        ax.set_xlim((xbegin_numeric, time_numeric[-1] + 3 / 24))
    else:
        # フォールバック：従来の方式
        logging.warning("数値化済み時間データが利用できないため、フォールバック処理を実行します")
        if isinstance(x, list) and len(x) > 0:
            if isinstance(x[-1], datetime.datetime):
                logging.warning("datetime型の時間データをその場で数値化して使用します")
                ax.set_xlim((xbegin_numeric, float(matplotlib.dates.date2num(x[-1])) + 3 / 24))
            else:
                logging.warning("時間データを数値として直接使用します")
                ax.set_xlim((xbegin_numeric, float(x[-1]) + 3 / 24))
        else:
            # さらなるフォールバック
            logging.warning("時間データが無効なため、固定の時間範囲を設定します")
            ax.set_xlim((xbegin_numeric, xbegin_numeric + 3))

    ax.plot(
        x,  # type: ignore[arg-type]  # matplotlib accepts list types
        y,  # type: ignore[arg-type]
        color="#CCCCCC",
        marker="o",
        markevery=[len(y) - 1],
        markersize=5,
        markerfacecolor="#DDDDDD",
        markeredgewidth=3,
        markeredgecolor="#BBBBBB",
        linewidth=3.0,
        linestyle="solid",
    )

    ax.fill_between(
        x,  # type: ignore[arg-type]  # matplotlib accepts list types
        y,  # type: ignore[arg-type]
        0,
        facecolor="#DDDDDD",
        alpha=0.5,
    )

    font = face_map["value_small"] if small else face_map["value"]

    # 共有された軸設定を使用
    ax.xaxis.set_major_locator(axis_config.major_locator)
    ax.xaxis.set_major_formatter(axis_config.major_formatter)
    for label in ax.get_xticklabels():
        label.set_fontproperties(face_map["xaxis"])

    ax.set_ylabel(unit, fontproperties=face_map["yaxis"])
    ax.set_yscale(scale)

    ax.grid(axis="x", color="#000000", alpha=0.1, linestyle="-", linewidth=1)

    ax.text(
        0.92,
        0.05,
        text,
        transform=ax.transAxes,
        horizontalalignment="right",
        color="#000000",
        alpha=0.8,
        fontproperties=font,
    )

    ax.label_outer()


def create_sensor_graph_impl(  # noqa: C901, PLR0912, PLR0915
    sensor_config: SensorConfig,
    context: my_lib.panel_config.DatabasePanelContext,
) -> PIL.Image.Image:
    face_map = get_face_map(context.font_config)

    room_list = sensor_config.room_list
    width = sensor_config.panel.width
    height = sensor_config.panel.height

    matplotlib.pyplot.style.use("grayscale")

    fig = matplotlib.pyplot.figure(facecolor="azure", edgecolor="coral", linewidth=2)

    try:
        fig.set_size_inches(width / IMAGE_DPI, height / IMAGE_DPI)

        # NOTE: 全データを並列で一度に取得してキャッシュ（最適化）
        data_cache: dict[str, dict[int, PlotData]] = {}
        cache: PlotData = PlotData()
        range_map: dict[str, tuple[float, float]] = {}
        time_begin = datetime.datetime.now(datetime.timezone.utc)

        # 並列取得用のリクエストリストを準備
        fetch_requests: list[DataRequest] = []
        request_map: dict[tuple[str, int, str, str], int] = {}  # (param_name, col, measure, hostname) -> request_index

        for param in sensor_config.param_list:
            data_cache[param.name] = {}
            for col, room in enumerate(room_list):
                for sensor in room.sensor:
                    request_index = len(fetch_requests)
                    request_map[(param.name, col, sensor.measure, sensor.hostname)] = request_index

                    if os.environ.get("DUMMY_MODE", "false") == "true":
                        period_start = "-228h"
                        period_stop = "-168h"
                    else:
                        period_start = "-60h"
                        period_stop = "now()"

                    fetch_requests.append(
                        DataRequest(
                            measure=sensor.measure,
                            hostname=sensor.hostname,
                            field=param.name,
                            start=period_start,
                            stop=period_stop,
                        )
                    )

        # エアコン電力取得用のリクエストも追加
        aircon_requests, aircon_map = get_aircon_power_requests(room_list)

        all_requests = fetch_requests + aircon_requests
        aircon_results_offset = len(fetch_requests)

        # 並列でデータを取得
        logging.info(
            "Fetching sensor data in parallel (%d requests, %d aircon)", len(fetch_requests), len(aircon_requests)
        )
        parallel_start = time.perf_counter()
        all_results = asyncio.run(fetch_data_parallel(context.db_config, all_requests))
        parallel_time = time.perf_counter() - parallel_start
        logging.info("Parallel fetch completed in %.2f seconds", parallel_time)

        # センサーデータとエアコンデータを分離
        results = all_results[: len(fetch_requests)]
        aircon_results = all_results[aircon_results_offset:] if aircon_requests else []

        # 結果をキャッシュに格納（sensor_data関数のロジックを適用）
        for param in sensor_config.param_list:
            for col, room in enumerate(room_list):
                # 複数のセンサーから最初の有効なデータを選択
                data: SensorDataResult | None = None
                for sensor in room.sensor:
                    request_key = (param.name, col, sensor.measure, sensor.hostname)
                    if request_key in request_map:  # pragma: no branch  # 同じデータから構築されるため常にTrue
                        request_index = request_map[request_key]
                        candidate_data = results[request_index]

                        # BaseException をスキップ
                        if isinstance(candidate_data, BaseException):
                            logging.warning("Sensor data fetch failed: %s", candidate_data)
                            continue

                        if candidate_data.valid:
                            data = candidate_data
                            break

                # 有効なデータが見つからない場合は最後のデータを使用
                if data is None and room.sensor:
                    last_sensor = room.sensor[-1]
                    request_key = (param.name, col, last_sensor.measure, last_sensor.hostname)
                    if request_key in request_map:  # pragma: no branch  # 同じデータから構築されるため常にTrue
                        request_index = request_map[request_key]
                        last_result = results[request_index]
                        if isinstance(last_result, SensorDataResult):
                            data = last_result

                # SensorDataResult を PlotData に変換して time_numeric を追加
                if data is not None:
                    plot_data = PlotData(valid=data.valid, time=list(data.time), value=list(data.value))
                else:  # pragma: no cover  # room.sensor が空の場合のみ
                    plot_data = PlotData()
                data_cache[param.name][col] = plot_data

                if plot_data.valid:
                    # 日付を数値化（最適化）
                    time_data = plot_data.time
                    if time_data:
                        plot_data.time_numeric = list(matplotlib.dates.date2num(time_data))
                        time_begin = min(time_begin, time_data[0])

                    if not cache.time:
                        cache = PlotData(
                            valid=False,
                            time=time_data,
                            time_numeric=plot_data.time_numeric,
                            value=[EMPTY_VALUE for _ in range(len(time_data))],
                        )

        # キャッシュからレンジを計算
        for param in sensor_config.param_list:
            param_min = float("inf")
            param_max = -float("inf")

            for col in range(len(room_list)):
                cached_data = data_cache[param.name][col]
                if not cached_data.valid:
                    continue

                value_list = cached_data.value
                min_val = min([item for item in value_list if item is not None])
                max_val = max([item for item in value_list if item is not None])
                param_min = min(param_min, min_val)
                param_max = max(param_max, max_val)

            # NOTE: 見やすくなるように、ちょっと広げる
            range_map[param.name] = (
                max(0, param_min - (param_max - param_min) * 0.3),
                param_max + (param_max - param_min) * 0.05,
            )

        # 共通の軸設定を取得（日付変換最適化）
        axis_config = get_shared_axis_config()

        # 開始時間を数値化
        time_begin_numeric = float(matplotlib.dates.date2num(time_begin))

        # サブプロットを一括生成（最適化）
        num_rows = len(sensor_config.param_list)
        num_cols = len(room_list)

        # 既存のfigを使って、gridspecでサブプロットを作成
        gs = matplotlib.gridspec.GridSpec(
            num_rows, num_cols, figure=fig, hspace=0.1, wspace=0, left=0.05, bottom=0.08, right=0.98, top=0.92
        )
        axes = []
        for i in range(num_rows * num_cols):
            row = i // num_cols
            col = i % num_cols
            ax = fig.add_subplot(gs[row, col])
            axes.append(ax)

        for row, param in enumerate(sensor_config.param_list):
            logging.info("draw %s graph", param.name)

            for col, room in enumerate(room_list):
                # キャッシュからデータを取得（最適化）
                plot_data = data_cache[param.name][col]
                if not plot_data.valid:
                    plot_data = cache

                # 一括生成したaxesを使用
                ax_index = row * num_cols + col
                ax = axes[ax_index]

                title = room.label if row == 0 else None
                graph_range = range_map[param.name] if param.range == "auto" else (param.range[0], param.range[1])

                plot_item(
                    ax,
                    title,
                    param.unit,
                    plot_data,
                    time_begin_numeric,
                    graph_range,
                    param.format,
                    param.scale,
                    param.size_small,
                    face_map,
                    axis_config,
                )

                if (param.name == "temp") and room.aircon is not None:
                    draw_aircon_icon(
                        ax,
                        get_aircon_power_from_results(aircon_results, aircon_map, col),
                        sensor_config.icon,
                    )

                if (param.name == "lux") and room.light_icon:
                    draw_light_icon(ax, plot_data.value, sensor_config.icon)

        with io.BytesIO() as buf:
            # グレースケール画像を直接生成（最適化）
            matplotlib.pyplot.savefig(buf, format="png", dpi=IMAGE_DPI, facecolor="white", transparent=False)

            buf.seek(0)

            img = PIL.Image.open(buf).copy()
            # 既にグレースケールカラーマップ使用中のため、Lモードに変換
            if img.mode != "L":  # pragma: no branch  # savefig は常に RGB を返すため
                img = img.convert("L")

        return img
    finally:
        # 例外発生時も含め、確実にmatplotlibリソースをクリーンアップ
        matplotlib.pyplot.clf()
        matplotlib.pyplot.close(fig)


def create(config: AppConfig) -> tuple[PIL.Image.Image, float] | tuple[PIL.Image.Image, float, str]:
    logging.info("draw sensor graph")
    start = time.perf_counter()

    # NOTE: sensor_graph は通常モードでのみ呼ばれるため、sensor は常に存在する (config.schema で必須)
    assert config.sensor is not None, "sensor configuration is required for normal mode"
    sensor_config = config.sensor

    context = my_lib.panel_config.DatabasePanelContext(
        font_config=config.font,
        db_config=config.influxdb,
    )

    try:
        img = create_sensor_graph_impl(sensor_config, context)
        elapsed_time = time.perf_counter() - start

        return (img, elapsed_time)
    except Exception:
        error_message = traceback.format_exc()
        elapsed_time = time.perf_counter() - start

        return (
            my_lib.panel_util.create_error_image(sensor_config, context.font_config, error_message),
            elapsed_time,
            error_message,
        )


if __name__ == "__main__":
    # TEST Code
    import docopt
    import my_lib.logger

    from weather_display.config import load

    assert __doc__ is not None
    args = docopt.docopt(__doc__)

    config_file = args["-c"]
    out_file = args["-o"]
    debug_mode = args["-D"]

    my_lib.logger.init("test", level=logging.DEBUG if debug_mode else logging.INFO)

    config = load(config_file)
    result = create(config)

    if len(result) > 2:
        # エラーが発生した場合
        img, elapsed_time, error_message = result
        logging.error("Error occurred: %s", error_message)
        logging.info("Elapsed time: %.2f seconds", elapsed_time)
    else:
        # 正常な場合
        img, elapsed_time = result
        logging.info("Elapsed time: %.2f seconds", elapsed_time)

    logging.info("Save %s.", out_file)
    # グレースケール変換は既に実施済み（最適化）
    img.save(out_file, "PNG")

    logging.info("Finish.")
