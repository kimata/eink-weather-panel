#!/usr/bin/env python3
"""設定ファイルの型定義

設計方針:
- my_lib.panel_config の共通型を使用
- パスは pathlib.Path で統一
- None の使用を最小限に
"""

from __future__ import annotations

import pathlib
from dataclasses import dataclass, field
from typing import Literal

import my_lib.config
from my_lib.notify.slack import SlackConfigTypes, SlackEmptyConfig
from my_lib.notify.slack import parse_config as parse_slack_config
from my_lib.panel_config import FontConfig, IconConfig, PanelGeometry

# my_lib から re-export
__all__ = [
    "FontConfig",
    "IconConfig",
    "PanelGeometry",
    "AppConfig",
    "parse_config",
    "load",
]


# === センサー関連 ===
@dataclass(frozen=True)
class SensorSpec:
    """センサー指定"""

    hostname: str
    measure: str


# === Liveness ===
@dataclass(frozen=True)
class LivenessFileConfig:
    """Liveness ファイルパス設定"""

    display: pathlib.Path


@dataclass(frozen=True)
class LivenessConfig:
    """Liveness 設定"""

    file: LivenessFileConfig


# === Panel Device ===
@dataclass(frozen=True)
class DeviceConfig:
    """デバイス設定"""

    width: int
    height: int


@dataclass(frozen=True)
class UpdateConfig:
    """更新設定"""

    interval: int


@dataclass(frozen=True)
class PanelDeviceConfig:
    """パネルデバイス設定"""

    device: DeviceConfig
    update: UpdateConfig


# === InfluxDB ===
@dataclass(frozen=True)
class InfluxDBConfig:
    """InfluxDB 接続設定"""

    url: str
    org: str
    token: str
    bucket: str


# === Wall ===
@dataclass(frozen=True)
class WallImageConfig:
    """壁紙画像設定"""

    path: pathlib.Path
    scale: float = 1.0
    brightness: float = 1.0
    offset_x: int = 0
    offset_y: int = 0


@dataclass(frozen=True)
class WallConfig:
    """壁紙設定"""

    image: list[WallImageConfig]


# === Time ===
@dataclass(frozen=True)
class TimeConfig:
    """時刻パネル設定"""

    panel: PanelGeometry


# === Weather ===
@dataclass(frozen=True)
class YahooDataConfig:
    """Yahoo データソース設定"""

    url: str


@dataclass(frozen=True)
class WeatherDataConfig:
    """天気データソース設定"""

    yahoo: YahooDataConfig


@dataclass(frozen=True)
class WeatherConfig:
    """天気パネル設定"""

    panel: PanelGeometry
    data: WeatherDataConfig
    icon: dict[str, IconConfig]


# === Power ===
@dataclass(frozen=True)
class PowerParamConfig:
    """電力パラメータ設定"""

    field: str
    format: str
    unit: str
    range: list[int]


@dataclass(frozen=True)
class PowerDataConfig:
    """電力データソース設定"""

    sensor: SensorSpec
    param: PowerParamConfig


@dataclass(frozen=True)
class PowerConfig:
    """電力パネル設定"""

    panel: PanelGeometry
    data: PowerDataConfig


# === Sensor ===
@dataclass(frozen=True)
class AirconConfig:
    """エアコン設定"""

    measure: str
    hostname: str


@dataclass(frozen=True)
class RoomConfig:
    """部屋設定"""

    label: str
    sensor: list[SensorSpec]
    light_icon: bool = False
    aircon: AirconConfig | None = None
    type: str | None = None


@dataclass(frozen=True)
class SensorParamConfig:
    """センサーパラメータ設定"""

    name: str
    format: str
    unit: str
    range: Literal["auto"] | list[int]
    scale: Literal["linear", "log"]
    size_small: bool = False


@dataclass(frozen=True)
class LightIconConfig:
    """照明アイコン設定"""

    on: IconConfig
    off: IconConfig


@dataclass(frozen=True)
class SensorIconConfig:
    """センサーアイコン設定"""

    light: LightIconConfig
    aircon: IconConfig


@dataclass(frozen=True)
class SensorConfig:
    """センサーパネル設定"""

    panel: PanelGeometry
    room_list: list[RoomConfig]
    param_list: list[SensorParamConfig]
    icon: SensorIconConfig


# === Rain Fall ===
@dataclass(frozen=True)
class RainFallConfig:
    """降雨パネル設定"""

    panel: PanelGeometry
    sensor: SensorSpec
    icon: IconConfig


# === Rain Cloud ===
@dataclass(frozen=True)
class JmaDataConfig:
    """気象庁データソース設定"""

    url: str


@dataclass(frozen=True)
class RainCloudDataConfig:
    """雨雲データソース設定"""

    jma: JmaDataConfig


@dataclass(frozen=True)
class LegendConfig:
    """凡例設定"""

    bar_size: int
    offset_x: int
    offset_y: int
    gamma: float


@dataclass(frozen=True)
class RainCloudConfig:
    """雨雲パネル設定"""

    panel: PanelGeometry
    legend: LegendConfig
    data: RainCloudDataConfig


# === Sunset ===
@dataclass(frozen=True)
class NaoDataConfig:
    """国立天文台データソース設定"""

    pref: int


@dataclass(frozen=True)
class SunsetDataConfig:
    """日没データソース設定"""

    nao: NaoDataConfig


@dataclass(frozen=True)
class SunsetConfig:
    """日没設定"""

    data: SunsetDataConfig


# === WBGT ===
@dataclass(frozen=True)
class EnvGoDataConfig:
    """環境省データソース設定"""

    url: str


@dataclass(frozen=True)
class WbgtDataConfig:
    """WBGT データソース設定"""

    env_go: EnvGoDataConfig


@dataclass(frozen=True)
class WbgtIconConfig:
    """WBGT アイコン設定"""

    face: list[IconConfig]


@dataclass(frozen=True)
class WbgtConfig:
    """WBGT パネル設定"""

    panel: PanelGeometry
    data: WbgtDataConfig
    icon: WbgtIconConfig


# === Metrics ===
@dataclass(frozen=True)
class MetricsConfig:
    """メトリクス設定"""

    data: pathlib.Path


# === WebApp ===
@dataclass(frozen=True)
class TimezoneConfig:
    """タイムゾーン設定"""

    offset: str
    name: str
    zone: str


@dataclass(frozen=True)
class WebAppConfig:
    """Web アプリケーション設定"""

    timezone: TimezoneConfig
    static_dir_path: pathlib.Path


# === メイン設定クラス ===
@dataclass(frozen=True)
class AppConfig:
    """アプリケーション設定"""

    liveness: LivenessConfig
    panel: PanelDeviceConfig
    influxdb: InfluxDBConfig
    time: TimeConfig
    weather: WeatherConfig
    power: PowerConfig
    rain_cloud: RainCloudConfig
    sunset: SunsetConfig
    wbgt: WbgtConfig
    font: FontConfig
    sensor: SensorConfig | None = None
    rain_fall: RainFallConfig | None = None
    wall: WallConfig = field(default_factory=lambda: WallConfig(image=[]))
    slack: SlackConfigTypes = field(default_factory=SlackEmptyConfig)
    metrics: MetricsConfig | None = None
    webapp: WebAppConfig | None = None


# === パース関数 ===
def _parse_panel_geometry(data: dict[str, int]) -> PanelGeometry:
    return PanelGeometry(
        width=data["width"],
        height=data["height"],
        offset_x=data.get("offset_x", 0),
        offset_y=data.get("offset_y", 0),
    )


def _parse_icon(data: dict[str, str | float]) -> IconConfig:
    return IconConfig(
        path=pathlib.Path(str(data["path"])),
        scale=float(data.get("scale", 1.0)),
        brightness=float(data.get("brightness", 1.0)),
    )


def _parse_sensor_spec(data: dict[str, str]) -> SensorSpec:
    return SensorSpec(
        hostname=data["hostname"],
        measure=data["measure"],
    )


def _parse_liveness(data: dict[str, dict[str, str]]) -> LivenessConfig:
    return LivenessConfig(
        file=LivenessFileConfig(display=pathlib.Path(data["file"]["display"])),
    )


def _parse_panel_device(data: dict[str, dict[str, int]]) -> PanelDeviceConfig:
    return PanelDeviceConfig(
        device=DeviceConfig(
            width=data["device"]["width"],
            height=data["device"]["height"],
        ),
        update=UpdateConfig(interval=data["update"]["interval"]),
    )


def _parse_influxdb(data: dict[str, str]) -> InfluxDBConfig:
    return InfluxDBConfig(
        url=data["url"],
        org=data["org"],
        token=data["token"],
        bucket=data["bucket"],
    )


def _parse_wall(data: dict[str, list[dict[str, str | float | int]]]) -> WallConfig:
    images = []
    for img_data in data["image"]:
        images.append(
            WallImageConfig(
                path=pathlib.Path(str(img_data["path"])),
                scale=float(img_data.get("scale", 1.0)),
                brightness=float(img_data.get("brightness", 1.0)),
                offset_x=int(img_data.get("offset_x", 0)),
                offset_y=int(img_data.get("offset_y", 0)),
            )
        )
    return WallConfig(image=images)


def _parse_time(data: dict[str, dict[str, int]]) -> TimeConfig:
    return TimeConfig(panel=_parse_panel_geometry(data["panel"]))


def _parse_weather(data: dict[str, object]) -> WeatherConfig:
    icon_data = data["icon"]
    if not isinstance(icon_data, dict):
        msg = "weather icon must be a dict"
        raise TypeError(msg)

    icon_map = {}
    for name, icon_item in icon_data.items():
        if isinstance(icon_item, dict):
            icon_map[name] = _parse_icon(icon_item)

    data_section = data["data"]
    if not isinstance(data_section, dict):
        msg = "weather data must be a dict"
        raise TypeError(msg)

    yahoo_data = data_section["yahoo"]
    if not isinstance(yahoo_data, dict):
        msg = "yahoo data must be a dict"
        raise TypeError(msg)

    panel_data = data["panel"]
    if not isinstance(panel_data, dict):
        msg = "panel must be a dict"
        raise TypeError(msg)

    return WeatherConfig(
        panel=_parse_panel_geometry(panel_data),
        data=WeatherDataConfig(
            yahoo=YahooDataConfig(url=str(yahoo_data["url"])),
        ),
        icon=icon_map,
    )


def _parse_power(data: dict[str, object]) -> PowerConfig:
    panel_data = data["panel"]
    if not isinstance(panel_data, dict):
        msg = "panel must be a dict"
        raise TypeError(msg)

    data_section = data["data"]
    if not isinstance(data_section, dict):
        msg = "data must be a dict"
        raise TypeError(msg)

    sensor_data = data_section["sensor"]
    param_data = data_section["param"]
    if not isinstance(sensor_data, dict) or not isinstance(param_data, dict):
        msg = "sensor and param must be dicts"
        raise TypeError(msg)

    return PowerConfig(
        panel=_parse_panel_geometry(panel_data),
        data=PowerDataConfig(
            sensor=_parse_sensor_spec(sensor_data),
            param=PowerParamConfig(
                field=str(param_data["field"]),
                format=str(param_data["format"]),
                unit=str(param_data["unit"]),
                range=list(param_data["range"]),
            ),
        ),
    )


def _parse_aircon(data: dict[str, str] | None) -> AirconConfig | None:
    if data is None:
        return None
    return AirconConfig(
        measure=data["measure"],
        hostname=data["hostname"],
    )


def _parse_room(data: dict[str, object]) -> RoomConfig:
    sensor_list = data["sensor"]
    if not isinstance(sensor_list, list):
        msg = "sensor must be a list"
        raise TypeError(msg)

    sensors = [_parse_sensor_spec(s) for s in sensor_list]

    aircon_data = data.get("aircon")
    aircon = None
    if isinstance(aircon_data, dict):
        aircon = _parse_aircon(aircon_data)

    type_val = data.get("type")

    return RoomConfig(
        label=str(data["label"]),
        sensor=sensors,
        light_icon=bool(data.get("light_icon", False)),
        aircon=aircon,
        type=str(type_val) if type_val is not None else None,
    )


def _parse_sensor_param(data: dict[str, object]) -> SensorParamConfig:
    range_val = data["range"]
    if range_val == "auto":
        range_parsed: Literal["auto"] | list[int] = "auto"
    elif isinstance(range_val, list):
        range_parsed = [int(x) for x in range_val]
    else:
        msg = f"range must be 'auto' or a list, got {type(range_val)}"
        raise TypeError(msg)

    scale_val = str(data["scale"])
    if scale_val not in ("linear", "log"):
        msg = f"scale must be 'linear' or 'log', got {scale_val}"
        raise ValueError(msg)

    return SensorParamConfig(
        name=str(data["name"]),
        format=str(data["format"]),
        unit=str(data["unit"]),
        range=range_parsed,
        scale=scale_val,  # type: ignore[arg-type]
        size_small=bool(data.get("size_small", False)),
    )


def _parse_sensor(data: dict[str, object]) -> SensorConfig:
    panel_data = data["panel"]
    if not isinstance(panel_data, dict):
        msg = "panel must be a dict"
        raise TypeError(msg)

    room_list_data = data["room_list"]
    if not isinstance(room_list_data, list):
        msg = "room_list must be a list"
        raise TypeError(msg)

    param_list_data = data["param_list"]
    if not isinstance(param_list_data, list):
        msg = "param_list must be a list"
        raise TypeError(msg)

    icon_data = data["icon"]
    if not isinstance(icon_data, dict):
        msg = "icon must be a dict"
        raise TypeError(msg)

    light_data = icon_data["light"]
    aircon_data = icon_data["aircon"]
    if not isinstance(light_data, dict) or not isinstance(aircon_data, dict):
        msg = "light and aircon must be dicts"
        raise TypeError(msg)

    return SensorConfig(
        panel=_parse_panel_geometry(panel_data),
        room_list=[_parse_room(r) for r in room_list_data],
        param_list=[_parse_sensor_param(p) for p in param_list_data],
        icon=SensorIconConfig(
            light=LightIconConfig(
                on=_parse_icon(light_data["on"]),
                off=_parse_icon(light_data["off"]),
            ),
            aircon=_parse_icon(aircon_data),
        ),
    )


def _parse_rain_fall(data: dict[str, object]) -> RainFallConfig:
    panel_data = data["panel"]
    sensor_data = data["sensor"]
    icon_data = data["icon"]

    if not isinstance(panel_data, dict):
        msg = "panel must be a dict"
        raise TypeError(msg)
    if not isinstance(sensor_data, dict):
        msg = "sensor must be a dict"
        raise TypeError(msg)
    if not isinstance(icon_data, dict):
        msg = "icon must be a dict"
        raise TypeError(msg)

    return RainFallConfig(
        panel=_parse_panel_geometry(panel_data),
        sensor=_parse_sensor_spec(sensor_data),
        icon=_parse_icon(icon_data),
    )


def _parse_rain_cloud(data: dict[str, object]) -> RainCloudConfig:
    panel_data = data["panel"]
    legend_data = data["legend"]
    data_section = data["data"]

    if not isinstance(panel_data, dict):
        msg = "panel must be a dict"
        raise TypeError(msg)
    if not isinstance(legend_data, dict):
        msg = "legend must be a dict"
        raise TypeError(msg)
    if not isinstance(data_section, dict):
        msg = "data must be a dict"
        raise TypeError(msg)

    jma_data = data_section["jma"]
    if not isinstance(jma_data, dict):
        msg = "jma must be a dict"
        raise TypeError(msg)

    return RainCloudConfig(
        panel=_parse_panel_geometry(panel_data),
        legend=LegendConfig(
            bar_size=int(legend_data["bar_size"]),
            offset_x=int(legend_data["offset_x"]),
            offset_y=int(legend_data["offset_y"]),
            gamma=float(legend_data["gamma"]),
        ),
        data=RainCloudDataConfig(
            jma=JmaDataConfig(url=str(jma_data["url"])),
        ),
    )


def _parse_sunset(data: dict[str, object]) -> SunsetConfig:
    data_section = data["data"]
    if not isinstance(data_section, dict):
        msg = "data must be a dict"
        raise TypeError(msg)

    nao_data = data_section["nao"]
    if not isinstance(nao_data, dict):
        msg = "nao must be a dict"
        raise TypeError(msg)

    return SunsetConfig(
        data=SunsetDataConfig(
            nao=NaoDataConfig(pref=int(nao_data["pref"])),
        ),
    )


def _parse_wbgt(data: dict[str, object]) -> WbgtConfig:
    panel_data = data["panel"]
    data_section = data["data"]
    icon_data = data["icon"]

    if not isinstance(panel_data, dict):
        msg = "panel must be a dict"
        raise TypeError(msg)
    if not isinstance(data_section, dict):
        msg = "data must be a dict"
        raise TypeError(msg)
    if not isinstance(icon_data, dict):
        msg = "icon must be a dict"
        raise TypeError(msg)

    env_go_data = data_section["env_go"]
    if not isinstance(env_go_data, dict):
        msg = "env_go must be a dict"
        raise TypeError(msg)

    face_data = icon_data["face"]
    if not isinstance(face_data, list):
        msg = "face must be a list"
        raise TypeError(msg)

    face_icons = [_parse_icon(f) for f in face_data]

    return WbgtConfig(
        panel=_parse_panel_geometry(panel_data),
        data=WbgtDataConfig(
            env_go=EnvGoDataConfig(url=str(env_go_data["url"])),
        ),
        icon=WbgtIconConfig(face=face_icons),
    )


def _parse_font(data: dict[str, str | dict[str, str]]) -> FontConfig:
    path = data["path"]
    if not isinstance(path, str):
        msg = "font path must be a string"
        raise TypeError(msg)

    map_data = data["map"]
    if not isinstance(map_data, dict):
        msg = "font map must be a dict"
        raise TypeError(msg)

    return FontConfig(
        path=pathlib.Path(path),
        map=dict(map_data),
    )


def _parse_metrics(data: dict[str, str] | None) -> MetricsConfig | None:
    if data is None:
        return None
    return MetricsConfig(data=pathlib.Path(data["data"]))


def _parse_webapp(data: dict[str, object] | None) -> WebAppConfig | None:
    if data is None:
        return None

    timezone_data = data["timezone"]
    if not isinstance(timezone_data, dict):
        msg = "timezone must be a dict"
        raise TypeError(msg)

    return WebAppConfig(
        timezone=TimezoneConfig(
            offset=str(timezone_data["offset"]),
            name=str(timezone_data["name"]),
            zone=str(timezone_data["zone"]),
        ),
        static_dir_path=pathlib.Path(str(data["static_dir_path"])),
    )


def parse_config(data: dict[str, object]) -> AppConfig:
    """設定辞書をパースして AppConfig を返す"""
    # オプションフィールドの処理
    wall_data = data.get("wall")
    wall = _parse_wall(wall_data) if wall_data is not None else WallConfig(image=[])  # type: ignore[arg-type]

    sensor_data = data.get("sensor")
    sensor = _parse_sensor(sensor_data) if sensor_data is not None else None  # type: ignore[arg-type]

    rain_fall_data = data.get("rain_fall")
    rain_fall = _parse_rain_fall(rain_fall_data) if rain_fall_data is not None else None  # type: ignore[arg-type]

    return AppConfig(
        liveness=_parse_liveness(data["liveness"]),  # type: ignore[arg-type]
        panel=_parse_panel_device(data["panel"]),  # type: ignore[arg-type]
        influxdb=_parse_influxdb(data["influxdb"]),  # type: ignore[arg-type]
        time=_parse_time(data["time"]),  # type: ignore[arg-type]
        weather=_parse_weather(data["weather"]),  # type: ignore[arg-type]
        power=_parse_power(data["power"]),  # type: ignore[arg-type]
        rain_cloud=_parse_rain_cloud(data["rain_cloud"]),  # type: ignore[arg-type]
        sunset=_parse_sunset(data["sunset"]),  # type: ignore[arg-type]
        wbgt=_parse_wbgt(data["wbgt"]),  # type: ignore[arg-type]
        font=_parse_font(data["font"]),  # type: ignore[arg-type]
        sensor=sensor,
        rain_fall=rain_fall,
        wall=wall,
        slack=parse_slack_config(data.get("slack", {})),
        metrics=_parse_metrics(data.get("metrics")),  # type: ignore[arg-type]
        webapp=_parse_webapp(data.get("webapp")),  # type: ignore[arg-type]
    )


def load(config_path: str, schema_path: pathlib.Path | None = None) -> AppConfig:
    """設定ファイルを読み込んで AppConfig を返す"""
    raw_config = my_lib.config.load(config_path, schema_path)
    return parse_config(raw_config)
