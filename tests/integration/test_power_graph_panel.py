#!/usr/bin/env python3
# ruff: noqa: S101
"""
消費電力グラフパネルの統合テスト
"""
import datetime

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
        import weather_display.panel.power_graph

        mocker.patch.object(weather_display.panel.power_graph, "fetch_data", return_value=mock_power_data())

        result = weather_display.panel.power_graph.create(config)

        assert len(result) >= 2
        img = result[0]
        assert img is not None

    def test_power_graph_panel_with_high_values(self, config, image_checker, mocker, mock_power_data):
        """高い電力値でもグラフを生成できること"""
        import weather_display.panel.power_graph

        mock_result = mock_power_data()
        mock_result.value = [2000 + i * 50 for i in range(60)]

        mocker.patch.object(weather_display.panel.power_graph, "fetch_data", return_value=mock_result)

        result = weather_display.panel.power_graph.create(config)

        assert len(result) >= 2

    def test_power_graph_panel_with_low_values(self, config, image_checker, mocker, mock_power_data):
        """低い電力値でもグラフを生成できること"""
        import weather_display.panel.power_graph

        mock_result = mock_power_data()
        mock_result.value = [100 + i for i in range(60)]

        mocker.patch.object(weather_display.panel.power_graph, "fetch_data", return_value=mock_result)

        result = weather_display.panel.power_graph.create(config)

        assert len(result) >= 2


class TestPowerGraphPanelError:
    """消費電力グラフパネルのエラーハンドリングテスト"""

    def test_power_graph_panel_fetch_error(self, config, image_checker, mocker):
        """データ取得エラー時にエラー画像を返すこと"""
        import weather_display.panel.power_graph

        # power_graph.py で from import しているため、モジュール内でパッチする
        mocker.patch.object(
            weather_display.panel.power_graph, "fetch_data", side_effect=RuntimeError("Fetch error")
        )

        result = weather_display.panel.power_graph.create(config)

        # エラー時は3要素のタプルを返す
        assert len(result) == 3
        assert "Traceback" in result[2]

    def test_power_graph_panel_empty_data_error(self, config, image_checker, mocker):
        """空データ時にエラー画像を返すこと"""
        from dataclasses import dataclass

        import weather_display.panel.power_graph

        @dataclass
        class EmptyResult:
            valid: bool = False
            time: list | None = None
            value: list | None = None

            def __post_init__(self):
                if self.time is None:
                    self.time = []
                if self.value is None:
                    self.value = []

        mocker.patch.object(weather_display.panel.power_graph, "fetch_data", return_value=EmptyResult())

        result = weather_display.panel.power_graph.create(config)

        # エラー時は3要素のタプルを返す
        assert len(result) == 3

    def test_power_graph_panel_invalid_data(self, config, image_checker, mocker):
        """無効なデータ時にエラー画像を返すこと"""
        from dataclasses import dataclass

        import weather_display.panel.power_graph

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

        mocker.patch.object(weather_display.panel.power_graph, "fetch_data", return_value=InvalidResult())

        result = weather_display.panel.power_graph.create(config)

        assert len(result) == 3

    def test_power_graph_panel_mismatched_data_lengths(self, config, image_checker, mocker):
        """データ長が一致しない時も処理を継続すること"""
        from dataclasses import dataclass

        import datetime

        import weather_display.panel.power_graph

        now = datetime.datetime.now(datetime.timezone.utc)

        @dataclass
        class MismatchedResult:
            valid: bool = True
            time: list | None = None
            value: list | None = None

            def __post_init__(self):
                if self.time is None:
                    self.time = [now - datetime.timedelta(hours=i) for i in range(10)]
                if self.value is None:
                    # 意図的に時間と異なる長さのデータを作成
                    self.value = [500 + i * 10 for i in range(5)]  # 短い

        mocker.patch.object(weather_display.panel.power_graph, "fetch_data", return_value=MismatchedResult())

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
        from dataclasses import dataclass

        import weather_display.panel.power_graph

        @dataclass
        class EmptyResult:
            valid: bool = False
            time: list | None = None
            value: list | None = None

            def __post_init__(self):
                if self.time is None:
                    self.time = []
                if self.value is None:
                    self.value = []

        mocker.patch.object(weather_display.panel.power_graph, "fetch_data", return_value=EmptyResult())
        mocker.patch("my_lib.notify.slack.error", side_effect=Exception("Slack error"))

        result = weather_display.panel.power_graph.create(config)

        # エラー時は3要素のタプルを返す
        assert len(result) == 3


class TestPowerGraphPanelInvalidDataLogging:
    """無効データ時のログ出力テスト"""

    def test_power_graph_panel_valid_but_empty_time(self, config, caplog, mocker):
        """valid=True だが time が空の場合に警告ログが出力されること (lines 219-220)"""
        import logging
        from dataclasses import dataclass

        import weather_display.panel.power_graph

        @dataclass
        class ValidButEmptyTime:
            valid: bool = True
            time: list | None = None
            value: list | None = None

            def __post_init__(self):
                if self.time is None:
                    self.time = []  # 空
                if self.value is None:
                    self.value = [100, 200, 300]

        mocker.patch.object(weather_display.panel.power_graph, "fetch_data", return_value=ValidButEmptyTime())

        with caplog.at_level(logging.WARNING):
            result = weather_display.panel.power_graph.create(config)

        # 警告ログが出力されること
        assert "time data is empty" in caplog.text

    def test_power_graph_panel_valid_but_empty_value(self, config, caplog, mocker):
        """valid=True だが value が空の場合に警告ログが出力されること (lines 221-222)"""
        import datetime
        import logging
        from dataclasses import dataclass

        import weather_display.panel.power_graph

        now = datetime.datetime.now(datetime.timezone.utc)

        @dataclass
        class ValidButEmptyValue:
            valid: bool = True
            time: list | None = None
            value: list | None = None

            def __post_init__(self):
                if self.time is None:
                    self.time = [now - datetime.timedelta(hours=i) for i in range(10)]
                if self.value is None:
                    self.value = []  # 空

        mocker.patch.object(weather_display.panel.power_graph, "fetch_data", return_value=ValidButEmptyValue())

        with caplog.at_level(logging.WARNING):
            result = weather_display.panel.power_graph.create(config)

        # 警告ログが出力されること
        assert "value data is empty" in caplog.text
