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
from typing import Any, Literal

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
        path=pathlib.Path(data["path"]),  # type: ignore[arg-type]
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
                path=pathlib.Path(img_data["path"]),  # type: ignore[arg-type]
                scale=float(img_data.get("scale", 1.0)),
                brightness=float(img_data.get("brightness", 1.0)),
                offset_x=int(img_data.get("offset_x", 0)),
                offset_y=int(img_data.get("offset_y", 0)),
            )
        )
    return WallConfig(image=images)


def _parse_time(data: dict[str, dict[str, int]]) -> TimeConfig:
    return TimeConfig(panel=_parse_panel_geometry(data["panel"]))


def _parse_weather(data: dict[str, Any]) -> WeatherConfig:
    icon_map = {name: _parse_icon(item) for name, item in data["icon"].items()}

    return WeatherConfig(
        panel=_parse_panel_geometry(data["panel"]),
        data=WeatherDataConfig(
            yahoo=YahooDataConfig(url=data["data"]["yahoo"]["url"]),
        ),
        icon=icon_map,
    )


def _parse_power(data: dict[str, Any]) -> PowerConfig:
    param_data = data["data"]["param"]

    return PowerConfig(
        panel=_parse_panel_geometry(data["panel"]),
        data=PowerDataConfig(
            sensor=_parse_sensor_spec(data["data"]["sensor"]),
            param=PowerParamConfig(
                field=param_data["field"],
                format=param_data["format"],
                unit=param_data["unit"],
                range=param_data["range"],
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


def _parse_room(data: dict[str, Any]) -> RoomConfig:
    sensors = [_parse_sensor_spec(s) for s in data["sensor"]]
    aircon_data = data.get("aircon")

    return RoomConfig(
        label=data["label"],
        sensor=sensors,
        light_icon=bool(data.get("light_icon", False)),
        aircon=_parse_aircon(aircon_data) if aircon_data else None,
        type=data.get("type"),
    )


def _parse_sensor_param(data: dict[str, Any]) -> SensorParamConfig:
    range_val = data["range"]
    if range_val == "auto":
        range_parsed: Literal["auto"] | list[int] = "auto"
    elif isinstance(range_val, list):
        range_parsed = [int(x) for x in range_val]
    else:
        msg = f"range must be 'auto' or a list, got {type(range_val)}"
        raise TypeError(msg)

    scale_val = data["scale"]
    if scale_val not in ("linear", "log"):
        msg = f"scale must be 'linear' or 'log', got {scale_val}"
        raise ValueError(msg)

    # Literal 型へのキャストは型チェッカーの制限により必要
    scale: Literal["linear", "log"] = "linear" if scale_val == "linear" else "log"

    return SensorParamConfig(
        name=data["name"],
        format=data["format"],
        unit=data["unit"],
        range=range_parsed,
        scale=scale,
        size_small=bool(data.get("size_small", False)),
    )


def _parse_sensor(data: dict[str, Any]) -> SensorConfig:
    icon_data = data["icon"]

    return SensorConfig(
        panel=_parse_panel_geometry(data["panel"]),
        room_list=[_parse_room(r) for r in data["room_list"]],
        param_list=[_parse_sensor_param(p) for p in data["param_list"]],
        icon=SensorIconConfig(
            light=LightIconConfig(
                on=_parse_icon(icon_data["light"]["on"]),
                off=_parse_icon(icon_data["light"]["off"]),
            ),
            aircon=_parse_icon(icon_data["aircon"]),
        ),
    )


def _parse_rain_fall(data: dict[str, Any]) -> RainFallConfig:
    return RainFallConfig(
        panel=_parse_panel_geometry(data["panel"]),
        sensor=_parse_sensor_spec(data["sensor"]),
        icon=_parse_icon(data["icon"]),
    )


def _parse_rain_cloud(data: dict[str, Any]) -> RainCloudConfig:
    legend_data = data["legend"]
    jma_data = data["data"]["jma"]

    return RainCloudConfig(
        panel=_parse_panel_geometry(data["panel"]),
        legend=LegendConfig(
            bar_size=legend_data["bar_size"],
            offset_x=legend_data["offset_x"],
            offset_y=legend_data["offset_y"],
            gamma=legend_data["gamma"],
        ),
        data=RainCloudDataConfig(
            jma=JmaDataConfig(url=jma_data["url"]),
        ),
    )


def _parse_sunset(data: dict[str, Any]) -> SunsetConfig:
    nao_data = data["data"]["nao"]

    return SunsetConfig(
        data=SunsetDataConfig(
            nao=NaoDataConfig(pref=nao_data["pref"]),
        ),
    )


def _parse_wbgt(data: dict[str, Any]) -> WbgtConfig:
    env_go_data = data["data"]["env_go"]
    face_data = data["icon"]["face"]

    face_icons = [_parse_icon(f) for f in face_data]

    return WbgtConfig(
        panel=_parse_panel_geometry(data["panel"]),
        data=WbgtDataConfig(
            env_go=EnvGoDataConfig(url=env_go_data["url"]),
        ),
        icon=WbgtIconConfig(face=face_icons),
    )


def _parse_font(data: dict[str, str | dict[str, str]]) -> FontConfig:
    return FontConfig(
        path=pathlib.Path(data["path"]),  # type: ignore[arg-type]
        map=dict(data["map"]),  # type: ignore[arg-type]
    )


def _parse_metrics(data: dict[str, str] | None) -> MetricsConfig | None:
    if data is None:
        return None
    return MetricsConfig(data=pathlib.Path(data["data"]))


def _parse_webapp(data: dict[str, Any] | None) -> WebAppConfig | None:
    if data is None:
        return None

    timezone_data = data["timezone"]

    return WebAppConfig(
        timezone=TimezoneConfig(
            offset=timezone_data["offset"],
            name=timezone_data["name"],
            zone=timezone_data["zone"],
        ),
        static_dir_path=pathlib.Path(data["static_dir_path"]),
    )


def parse_config(data: dict[str, Any]) -> AppConfig:
    """設定辞書をパースして AppConfig を返す"""
    # オプションフィールド
    wall_data = data.get("wall")
    wall = _parse_wall(wall_data) if wall_data is not None else WallConfig(image=[])

    sensor_data = data.get("sensor")
    sensor = _parse_sensor(sensor_data) if sensor_data is not None else None

    rain_fall_data = data.get("rain_fall")
    rain_fall = _parse_rain_fall(rain_fall_data) if rain_fall_data is not None else None

    return AppConfig(
        liveness=_parse_liveness(data["liveness"]),
        panel=_parse_panel_device(data["panel"]),
        influxdb=_parse_influxdb(data["influxdb"]),
        time=_parse_time(data["time"]),
        weather=_parse_weather(data["weather"]),
        power=_parse_power(data["power"]),
        rain_cloud=_parse_rain_cloud(data["rain_cloud"]),
        sunset=_parse_sunset(data["sunset"]),
        wbgt=_parse_wbgt(data["wbgt"]),
        font=_parse_font(data["font"]),
        sensor=sensor,
        rain_fall=rain_fall,
        wall=wall,
        slack=parse_slack_config(data.get("slack", {})),
        metrics=_parse_metrics(data.get("metrics")),
        webapp=_parse_webapp(data.get("webapp")),
    )


def load(config_path: str, schema_path: pathlib.Path | None = None) -> AppConfig:
    """設定ファイルを読み込んで AppConfig を返す"""
    raw_config = my_lib.config.load(config_path, schema_path)
    return parse_config(raw_config)
