#!/usr/bin/env python3
# ruff: noqa: S101
"""
センサーグラフパネルの統合テスト
"""
import datetime
import zoneinfo

import pytest


class TestSensorGraphPanel:
    """センサーグラフパネルのテスト"""

    def test_sensor_graph_panel_create(self, config, image_checker):
        """センサーグラフパネルを生成できること"""
        import weather_display.panel.sensor_graph

        result = weather_display.panel.sensor_graph.create(config)

        assert len(result) >= 2
        img = result[0]
        assert img is not None
        image_checker.check(img, config.sensor.panel)


class TestSensorGraphPanelWithMockedData:
    """モックデータを使用したセンサーグラフパネルテスト"""

    @pytest.fixture
    def mock_sensor_data(self, mocker):
        """センサーデータのモック"""
        from dataclasses import dataclass

        import matplotlib.dates

        now = datetime.datetime.now(datetime.timezone.utc)
        time_list = [now - datetime.timedelta(hours=i) for i in range(60, 0, -1)]
        time_numeric = matplotlib.dates.date2num(time_list)

        @dataclass
        class MockSensorResult:
            valid: bool = True
            time: list | None = None
            value: list | None = None

            def __post_init__(self):
                if self.time is None:
                    self.time = time_list
                if self.value is None:
                    self.value = [20 + i * 0.1 for i in range(60)]

        def create_mock(valid=True, temp_range=(15, 30), humi_range=(30, 80), lux_range=(0, 1000)):
            results = []
            for _ in range(20):  # 十分な数の結果を返す
                result = MockSensorResult(valid=valid)
                results.append(result)
            return results

        return create_mock

    def test_sensor_graph_panel_with_invalid_data(self, config, image_checker, mocker, mock_sensor_data):
        """無効なデータでも正常に動作すること"""
        from dataclasses import dataclass

        import weather_display.panel.sensor_graph

        @dataclass
        class InvalidResult:
            valid: bool = False
            time: list | None = None
            value: list | None = None

            def __post_init__(self):
                if self.time is None:
                    self.time = []
                if self.value is None:
                    self.value = []

        async def mock_fetch(*args):
            return [InvalidResult() for _ in range(20)]

        mocker.patch.object(weather_display.panel.sensor_graph, "fetch_data_parallel", side_effect=mock_fetch)

        result = weather_display.panel.sensor_graph.create(config)

        # エラーが発生しても結果が返ること
        assert len(result) >= 2


class TestSensorGraphPanelError:
    """センサーグラフパネルのエラーハンドリングテスト"""

    def test_sensor_graph_panel_fetch_error(self, config, image_checker, mocker):
        """データ取得エラー時にエラー画像を返すこと"""
        import weather_display.panel.sensor_graph

        # sensor_graph.py で from import しているため、モジュール内でパッチする
        mocker.patch.object(
            weather_display.panel.sensor_graph,
            "fetch_data_parallel",
            side_effect=RuntimeError("Fetch error"),
        )

        result = weather_display.panel.sensor_graph.create(config)

        # エラー時は3要素のタプルを返す
        assert len(result) == 3
        assert "Traceback" in result[2]


class TestGetSharedAxisConfig:
    """get_shared_axis_config 関数のテスト"""

    def test_get_shared_axis_config_returns_axis_config(self):
        """AxisConfig を返すこと"""
        from weather_display.panel.sensor_graph import AxisConfig, get_shared_axis_config

        result = get_shared_axis_config()

        assert isinstance(result, AxisConfig)
        assert result.major_locator is not None
        assert result.major_formatter is not None

    def test_get_shared_axis_config_is_cached(self):
        """キャッシュされていること"""
        from weather_display.panel.sensor_graph import get_shared_axis_config

        result1 = get_shared_axis_config()
        result2 = get_shared_axis_config()

        # 同じオブジェクトを返すこと
        assert result1 is result2


