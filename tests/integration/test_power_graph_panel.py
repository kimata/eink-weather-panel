#!/usr/bin/env python3
# ruff: noqa: S101
"""
消費電力グラフパネルの統合テスト
"""
import datetime

import my_lib.sensor_data
import pytest


class TestPowerGraphPanel:
    """消費電力グラフパネルのテスト"""

    def test_power_graph_panel_create(self, config, image_checker):
        """消費電力グラフパネルを生成できること"""
        import weather_display.panel.power_graph

        result = weather_display.panel.power_graph.create(config)

        assert len(result) >= 2
        img = result[0]
        assert img is not None
        image_checker.check(img, config.power.panel)


class TestPowerGraphPanelWithMockedData:
    """モックデータを使用した消費電力グラフパネルテスト"""

    @pytest.fixture
    def mock_power_data(self, mocker):
        """電力データのモック"""
        from dataclasses import dataclass

        now = datetime.datetime.now(datetime.timezone.utc)
        time_list = [now - datetime.timedelta(hours=i) for i in range(60, 0, -1)]

        @dataclass
        class MockPowerResult:
            valid: bool = True
            time: list | None = None
            value: list | None = None

            def __post_init__(self):
                if self.time is None:
                    self.time = time_list
                if self.value is None:
                    self.value = [500 + i * 10 for i in range(60)]

        return MockPowerResult

    def test_power_graph_panel_with_mock_data(self, config, image_checker, mocker, mock_power_data):
        """モックデータで消費電力グラフを生成できること"""
        import my_lib.sensor_data
        import weather_display.panel.power_graph

        mocker.patch.object(my_lib.sensor_data, "fetch_data", return_value=mock_power_data())

        result = weather_display.panel.power_graph.create(config)

        assert len(result) >= 2
        img = result[0]
        assert img is not None

    def test_power_graph_panel_with_high_values(self, config, image_checker, mocker, mock_power_data):
        """高い電力値でもグラフを生成できること"""
        import weather_display.panel.power_graph

        mock_result = mock_power_data()
        mock_result.value = [2000 + i * 50 for i in range(60)]

        mocker.patch.object(my_lib.sensor_data, "fetch_data", return_value=mock_result)

        result = weather_display.panel.power_graph.create(config)

        assert len(result) >= 2

    def test_power_graph_panel_with_low_values(self, config, image_checker, mocker, mock_power_data):
        """低い電力値でもグラフを生成できること"""
        import weather_display.panel.power_graph

        mock_result = mock_power_data()
        mock_result.value = [100 + i for i in range(60)]

        mocker.patch.object(my_lib.sensor_data, "fetch_data", return_value=mock_result)

        result = weather_display.panel.power_graph.create(config)

        assert len(result) >= 2


class TestPowerGraphPanelError:
    """消費電力グラフパネルのエラーハンドリングテスト"""

    def test_power_graph_panel_fetch_error(self, config, image_checker, mocker):
        """データ取得エラー時にエラー画像を返すこと"""
        import weather_display.panel.power_graph

        # power_graph.py で from import しているため、モジュール内でパッチする
        mocker.patch.object(
            my_lib.sensor_data, "fetch_data", side_effect=RuntimeError("Fetch error")
        )

        result = weather_display.panel.power_graph.create(config)

        # エラー時は3要素のタプルを返す
        assert len(result) == 3
        assert "Traceback" in result[2]

    def test_power_graph_panel_empty_data_error(self, config, image_checker, mocker):
        """空データ時にエラー画像を返すこと（診断情報を含む）"""
        from my_lib.sensor_data import SensorDataResult

        import weather_display.panel.power_graph

        # 接続エラーを模擬
        empty_result = SensorDataResult(
            value=[],
            time=[],
            valid=False,
            raw_record_count=0,
            null_count=0,
            error_message="Connection timeout",
        )

        mocker.patch.object(my_lib.sensor_data, "fetch_data", return_value=empty_result)

        result = weather_display.panel.power_graph.create(config)

        # エラー時は3要素のタプルを返す
        assert len(result) == 3
        # 診断情報が含まれていること
        assert "診断:" in result[2]
        assert "接続エラー" in result[2]

    def test_power_graph_panel_empty_data_no_records(self, config, image_checker, mocker):
        """クエリ結果が空の場合のエラー（診断情報を含む）"""
        from my_lib.sensor_data import SensorDataResult

        import weather_display.panel.power_graph

        # クエリ結果が空を模擬
        empty_result = SensorDataResult(
            value=[],
            time=[],
            valid=False,
            raw_record_count=0,
            null_count=0,
            error_message=None,
        )

        mocker.patch.object(my_lib.sensor_data, "fetch_data", return_value=empty_result)

        result = weather_display.panel.power_graph.create(config)

        assert len(result) == 3
        assert "診断:" in result[2]
        assert "データなし" in result[2]

    def test_power_graph_panel_all_null_data(self, config, image_checker, mocker):
        """全レコードがNoneの場合のエラー（診断情報を含む）"""
        from my_lib.sensor_data import SensorDataResult

        import weather_display.panel.power_graph

        # 全レコードがNoneを模擬
        null_result = SensorDataResult(
            value=[],
            time=[],
            valid=False,
            raw_record_count=100,
            null_count=100,
            error_message=None,
        )

        mocker.patch.object(my_lib.sensor_data, "fetch_data", return_value=null_result)

        result = weather_display.panel.power_graph.create(config)

        assert len(result) == 3
        assert "診断:" in result[2]
        assert "全データがNone" in result[2]

    def test_power_graph_panel_invalid_data(self, config, image_checker, mocker):
        """無効なデータ時にエラー画像を返すこと"""
        from my_lib.sensor_data import SensorDataResult

        import weather_display.panel.power_graph

        invalid_result = SensorDataResult(
            value=[],
            time=[],
            valid=False,
            raw_record_count=0,
            null_count=0,
            error_message=None,
        )

        mocker.patch.object(my_lib.sensor_data, "fetch_data", return_value=invalid_result)

        result = weather_display.panel.power_graph.create(config)

        assert len(result) == 3

    def test_power_graph_panel_mismatched_data_lengths(self, config, image_checker, mocker):
        """データ長が一致しない時も処理を継続すること"""
        import datetime

        from my_lib.sensor_data import SensorDataResult

        import weather_display.panel.power_graph

        now = datetime.datetime.now(datetime.timezone.utc)
        time_list = [now - datetime.timedelta(hours=i) for i in range(10)]
        # 意図的に時間と異なる長さのデータを作成
        value_list = [500.0 + i * 10.0 for i in range(5)]  # 短い

        mismatched_result = SensorDataResult(
            value=value_list,
            time=time_list,
            valid=True,
            raw_record_count=10,
            null_count=0,
        )

        mocker.patch.object(my_lib.sensor_data, "fetch_data", return_value=mismatched_result)

        result = weather_display.panel.power_graph.create(config)

        # エラーにならずに結果が返ること
        assert len(result) >= 2


class TestPowerGraphPanelNonDummyMode:
    """非DUMMYモードでのテスト"""

    def test_power_graph_panel_real_period(self, config, image_checker, mocker):
        """DUMMY_MODE=false での期間設定テスト"""
        import os

        import weather_display.panel.power_graph

        mocker.patch.dict(os.environ, {"DUMMY_MODE": "false"})

        result = weather_display.panel.power_graph.create(config)

        # 結果が返ること
        assert len(result) >= 2


class TestPowerGraphPanelSlackError:
    """Slack通知エラー時のテスト"""

    def test_power_graph_panel_slack_notification_error(self, config, image_checker, mocker):
        """Slack通知エラー時も正常に動作すること"""
        from my_lib.sensor_data import SensorDataResult

        import weather_display.panel.power_graph

        empty_result = SensorDataResult(
            value=[],
            time=[],
            valid=False,
            raw_record_count=0,
            null_count=0,
            error_message="Test error",
        )

        mocker.patch.object(my_lib.sensor_data, "fetch_data", return_value=empty_result)
        mocker.patch("my_lib.notify.slack.error", side_effect=Exception("Slack error"))

        result = weather_display.panel.power_graph.create(config)

        # エラー時は3要素のタプルを返す
        assert len(result) == 3


class TestPowerGraphPanelInvalidDataLogging:
    """無効データ時のログ出力テスト"""

    def test_power_graph_panel_valid_but_empty_time(self, config, caplog, mocker):
        """valid=True だが time が空の場合に警告ログが出力されること (lines 219-220)"""
        import logging

        from my_lib.sensor_data import SensorDataResult

        import weather_display.panel.power_graph

        empty_time_result = SensorDataResult(
            value=[100, 200, 300],
            time=[],  # 空
            valid=True,
            raw_record_count=3,
            null_count=0,
        )

        mocker.patch.object(my_lib.sensor_data, "fetch_data", return_value=empty_time_result)

        with caplog.at_level(logging.WARNING):
            weather_display.panel.power_graph.create(config)

        # 警告ログが出力されること
        assert "time data is empty" in caplog.text

    def test_power_graph_panel_valid_but_empty_value(self, config, caplog, mocker):
        """valid=True だが value が空の場合に警告ログが出力されること (lines 221-222)"""
        import datetime
        import logging

        from my_lib.sensor_data import SensorDataResult

        import weather_display.panel.power_graph

        now = datetime.datetime.now(datetime.timezone.utc)
        time_list = [now - datetime.timedelta(hours=i) for i in range(10)]

        empty_value_result = SensorDataResult(
            value=[],  # 空
            time=time_list,
            valid=True,
            raw_record_count=10,
            null_count=0,
        )

        mocker.patch.object(my_lib.sensor_data, "fetch_data", return_value=empty_value_result)

        with caplog.at_level(logging.WARNING):
            weather_display.panel.power_graph.create(config)

        # 警告ログが出力されること
        assert "value data is empty" in caplog.text
