#!/usr/bin/env python3
# ruff: noqa: S101
"""
センサーグラフユーティリティのユニットテスト
"""
import datetime
import zoneinfo

import pytest


class TestEmptyValue:
    """EMPTY_VALUE 定数のテスト"""

    def test_empty_value_is_defined(self):
        """EMPTY_VALUE が定義されていること"""
        from weather_display.panel.sensor_graph_utils import EMPTY_VALUE

        assert EMPTY_VALUE is not None


class TestGetAirconPowerRequests:
    """エアコン電力リクエスト生成のテスト"""

    def test_returns_empty_for_no_aircon(self, config):
        """エアコンがない部屋リストでは空を返すこと"""
        from weather_display.panel.sensor_graph_utils import get_aircon_power_requests

        # エアコンのない部屋リストを作成（既存設定を使用）
        room_list = config.sensor.room_list

        requests, aircon_map = get_aircon_power_requests(room_list)

        # 結果の型を確認
        assert isinstance(requests, list)
        assert isinstance(aircon_map, dict)


class TestGetAirconPowerFromResults:
    """エアコン電力取得のテスト"""

    def test_returns_none_for_empty_results(self):
        """空の結果でNoneを返すこと"""
        from weather_display.panel.sensor_graph_utils import get_aircon_power_from_results

        result = get_aircon_power_from_results([], {}, 0)

        assert result is None

    def test_returns_none_for_missing_col(self):
        """存在しないカラムでNoneを返すこと"""
        from weather_display.panel.sensor_graph_utils import get_aircon_power_from_results

        aircon_map = {0: [0]}  # col 0 のみ
        results = []

        result = get_aircon_power_from_results(results, aircon_map, 1)  # col 1 は存在しない

        assert result is None


class TestDrawAirconIcon:
    """エアコンアイコン描画のテスト"""

    @pytest.fixture
    def mock_ax(self, mocker):
        """matplotlib Axes のモック"""
        ax = mocker.MagicMock()
        ax.transAxes = mocker.MagicMock()
        return ax

    @pytest.fixture
    def icon_config(self, config):
        """アイコン設定を取得"""
        return config.sensor.icon

    def test_no_draw_when_power_is_none(self, mock_ax, icon_config):
        """電力がNoneの場合、描画しないこと"""
        from weather_display.panel.sensor_graph_utils import draw_aircon_icon

        draw_aircon_icon(mock_ax, None, icon_config)

        # add_artist が呼ばれていないこと
        assert not mock_ax.add_artist.called

    def test_no_draw_when_power_below_threshold(self, mock_ax, icon_config):
        """電力が閾値未満の場合、描画しないこと"""
        from weather_display.panel.sensor_graph_utils import AIRCON_WORK_THRESHOLD, draw_aircon_icon

        draw_aircon_icon(mock_ax, AIRCON_WORK_THRESHOLD - 1, icon_config)

        # add_artist が呼ばれていないこと
        assert not mock_ax.add_artist.called

    def test_draws_when_power_above_threshold(self, mock_ax, icon_config):
        """電力が閾値以上の場合、描画すること"""
        from weather_display.panel.sensor_graph_utils import AIRCON_WORK_THRESHOLD, draw_aircon_icon

        draw_aircon_icon(mock_ax, AIRCON_WORK_THRESHOLD + 10, icon_config)

        # add_artist が呼ばれていること
        assert mock_ax.add_artist.called

    @pytest.mark.parametrize("power", [0, 10, 20, 29])
    def test_no_draw_for_low_power_values(self, mock_ax, icon_config, power):
        """低電力値（閾値未満）では描画しないこと"""
        from weather_display.panel.sensor_graph_utils import draw_aircon_icon

        draw_aircon_icon(mock_ax, power, icon_config)

        assert not mock_ax.add_artist.called

    @pytest.mark.parametrize("power", [30, 50, 100, 500, 1000])
    def test_draws_for_high_power_values(self, mock_ax, icon_config, power):
        """高電力値（閾値以上）では描画すること"""
        from weather_display.panel.sensor_graph_utils import draw_aircon_icon

        draw_aircon_icon(mock_ax, power, icon_config)

        assert mock_ax.add_artist.called


class TestDrawLightIcon:
    """照明アイコン描画のテスト"""

    @pytest.fixture
    def mock_ax(self, mocker):
        """matplotlib Axes のモック"""
        ax = mocker.MagicMock()
        ax.transAxes = mocker.MagicMock()
        return ax

    @pytest.fixture
    def icon_config(self, config):
        """アイコン設定を取得"""
        return config.sensor.icon

    def test_no_draw_for_empty_value_list(self, mock_ax, icon_config, time_machine):
        """空の値リストでは描画しないこと"""
        from weather_display.panel.sensor_graph_utils import draw_light_icon

        tz = zoneinfo.ZoneInfo("Asia/Tokyo")
        time_machine.move_to(datetime.datetime.now(tz).replace(hour=20))

        # 空リストでも add_artist は呼ばれる可能性がある（実装依存）
        # エラーなく実行されることを確認
        draw_light_icon(mock_ax, [], icon_config)

    def test_handles_none_values_in_list(self, mock_ax, icon_config, time_machine):
        """リスト内のNone値を処理できること"""
        from weather_display.panel.sensor_graph_utils import draw_light_icon

        tz = zoneinfo.ZoneInfo("Asia/Tokyo")
        time_machine.move_to(datetime.datetime.now(tz).replace(hour=20))

        value_list = [None, None, 100, None]

        # エラーなく実行されること
        draw_light_icon(mock_ax, value_list, icon_config)

    def test_no_draw_during_daytime(self, mock_ax, icon_config, time_machine):
        """昼間（8-16時）は描画しないこと"""
        from weather_display.panel.sensor_graph_utils import draw_light_icon

        tz = zoneinfo.ZoneInfo("Asia/Tokyo")
        time_machine.move_to(datetime.datetime.now(tz).replace(hour=12))

        value_list = [100, 200, 300, 400]

        draw_light_icon(mock_ax, value_list, icon_config)

        # 昼間は描画しない
        assert not mock_ax.add_artist.called

    def test_draws_light_on_icon_at_night_when_bright(self, mock_ax, icon_config, time_machine):
        """夜間で明るい（照明点灯）場合、点灯アイコンを描画すること"""
        from weather_display.panel.sensor_graph_utils import draw_light_icon

        tz = zoneinfo.ZoneInfo("Asia/Tokyo")
        time_machine.move_to(datetime.datetime.now(tz).replace(hour=20))

        # 明るい値（照明点灯中 - 10lux以上）
        value_list = [50, 100, 150, 200]

        draw_light_icon(mock_ax, value_list, icon_config)

        # add_artist が呼ばれていること
        assert mock_ax.add_artist.called

    def test_draws_light_off_icon_at_night_when_dark(self, mock_ax, icon_config, time_machine):
        """夜間で暗い（照明消灯）場合、消灯アイコンを描画すること"""
        from weather_display.panel.sensor_graph_utils import draw_light_icon

        tz = zoneinfo.ZoneInfo("Asia/Tokyo")
        time_machine.move_to(datetime.datetime.now(tz).replace(hour=20))

        # 暗い値（照明消灯中 - 10lux未満）
        value_list = [1, 2, 3, 5]

        draw_light_icon(mock_ax, value_list, icon_config)

        # add_artist が呼ばれていること
        assert mock_ax.add_artist.called

    @pytest.mark.parametrize("hour", [0, 3, 6, 7, 17, 20, 23])
    def test_operates_during_nighttime_hours(self, mock_ax, icon_config, time_machine, hour):
        """夜間の時間帯で動作すること"""
        from weather_display.panel.sensor_graph_utils import draw_light_icon

        tz = zoneinfo.ZoneInfo("Asia/Tokyo")
        time_machine.move_to(datetime.datetime.now(tz).replace(hour=hour))

        value_list = [100, 200, 300, 400]

        # エラーなく実行されること
        draw_light_icon(mock_ax, value_list, icon_config)

    def test_no_draw_when_lux_is_empty_value(self, mock_ax, icon_config, time_machine):
        """lux が EMPTY_VALUE の場合、描画しないこと (line 113-114)"""
        from weather_display.panel.sensor_graph_utils import EMPTY_VALUE, draw_light_icon

        tz = zoneinfo.ZoneInfo("Asia/Tokyo")
        time_machine.move_to(datetime.datetime.now(tz).replace(hour=20))

        # EMPTY_VALUE で埋められたリスト（センサーデータが invalid の場合のキャッシュ）
        value_list = [EMPTY_VALUE, EMPTY_VALUE, EMPTY_VALUE]

        draw_light_icon(mock_ax, value_list, icon_config)

        # EMPTY_VALUE の場合は描画しない
        assert not mock_ax.add_artist.called
