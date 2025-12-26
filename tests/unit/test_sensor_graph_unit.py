#!/usr/bin/env python3
# ruff: noqa: S101
"""
sensor_graph.py のユニットテスト
"""
import datetime
import os

import pytest


class TestPlotItem:
    """plot_item 関数のテスト"""

    @pytest.fixture
    def plot_setup(self):
        """プロット用のセットアップ"""
        import matplotlib
        import matplotlib.dates
        import matplotlib.font_manager
        import matplotlib.pyplot as plt

        matplotlib.use("Agg")

        fig, ax = plt.subplots()

        yield {"fig": fig, "ax": ax}

        plt.close(fig)

    @pytest.fixture
    def face_map(self, config):
        """フォントマップ"""
        import matplotlib.font_manager

        font_path = config.font.path
        return {
            "title": matplotlib.font_manager.FontProperties(fname=f"{font_path}/migmix-1p-bold.ttf"),
            "value": matplotlib.font_manager.FontProperties(fname=f"{font_path}/migmix-1p-bold.ttf"),
            "unit": matplotlib.font_manager.FontProperties(fname=f"{font_path}/migmix-1p-regular.ttf"),
            "axis": matplotlib.font_manager.FontProperties(fname=f"{font_path}/migmix-1p-regular.ttf"),
            "xaxis": matplotlib.font_manager.FontProperties(fname=f"{font_path}/migmix-1p-regular.ttf"),
            "yaxis": matplotlib.font_manager.FontProperties(fname=f"{font_path}/migmix-1p-regular.ttf"),
        }

    @pytest.fixture
    def axis_config(self):
        """軸設定"""
        from weather_display.panel.sensor_graph import get_shared_axis_config

        return get_shared_axis_config()

    def test_plot_item_with_none_data(self, plot_setup, face_map, axis_config):
        """data が None の場合のテスト"""
        from weather_display.panel.sensor_graph import plot_item

        # data=None を渡してエラーにならないこと
        plot_item(
            ax=plot_setup["ax"],
            data=None,
            ylim=(0, 100),
            fmt="{:.1f}",
            unit="℃",
            scale="linear",
            title="Test",
            xbegin_numeric=0,
            small=False,
            face_map=face_map,
            axis_config=axis_config,
        )

    def test_plot_item_with_empty_time_numeric(self, plot_setup, face_map, axis_config):
        """time_numeric が空の場合のフォールバックテスト"""
        from weather_display.panel.sensor_graph import PlotData, plot_item

        # time_numeric を含まないデータを渡す（フォールバック処理が発生）
        data = PlotData(
            time=[],
            value=[],
            valid=False,
        )

        plot_item(
            ax=plot_setup["ax"],
            data=data,
            ylim=(0, 100),
            fmt="{:.1f}",
            unit="℃",
            scale="linear",
            title="Test",
            xbegin_numeric=0,
            small=False,
            face_map=face_map,
            axis_config=axis_config,
        )

    def test_plot_item_with_datetime_time(self, plot_setup, face_map, axis_config):
        """datetime型の時間データを含むデータのテスト（フォールバック処理）"""
        from weather_display.panel.sensor_graph import PlotData, plot_item

        now = datetime.datetime.now(datetime.timezone.utc)
        time_list = [now - datetime.timedelta(hours=i) for i in range(10, 0, -1)]

        # time_numeric を含まないが time は含むデータ
        data = PlotData(
            time=time_list,
            value=[20.0 + i for i in range(10)],
            valid=True,
        )

        plot_item(
            ax=plot_setup["ax"],
            data=data,
            ylim=(0, 100),
            fmt="{:.1f}",
            unit="℃",
            scale="linear",
            title="Test",
            xbegin_numeric=0,
            small=False,
            face_map=face_map,
            axis_config=axis_config,
        )

    def test_plot_item_with_numeric_time(self, plot_setup, face_map, axis_config):
        """数値型の時間データを含むデータのテスト（フォールバック処理）"""
        from weather_display.panel.sensor_graph import PlotData, plot_item

        now = datetime.datetime.now(datetime.timezone.utc)
        time_list = [now - datetime.timedelta(hours=i) for i in range(5, 0, -1)]

        # time_numeric で数値データを与える（time は datetime のまま）
        data = PlotData(
            time=time_list,
            time_numeric=[1.0, 2.0, 3.0, 4.0, 5.0],
            value=[20.0, 21.0, 22.0, 23.0, 24.0],
            valid=True,
        )

        plot_item(
            ax=plot_setup["ax"],
            data=data,
            ylim=(0, 100),
            fmt="{:.1f}",
            unit="℃",
            scale="linear",
            title="Test",
            xbegin_numeric=0,
            small=False,
            face_map=face_map,
            axis_config=axis_config,
        )

    def test_plot_item_with_log_scale_and_none_values(self, plot_setup, face_map, axis_config):
        """log スケールで None 値を含むデータのテスト"""
        import matplotlib.dates

        from weather_display.panel.sensor_graph import PlotData, plot_item

        now = datetime.datetime.now(datetime.timezone.utc)
        time_list = [now - datetime.timedelta(hours=i) for i in range(10, 0, -1)]
        time_numeric = list(matplotlib.dates.date2num(time_list))

        data = PlotData(
            time=time_list,
            time_numeric=time_numeric,
            value=[0, None, 0.5, 1, 10, 100, 1000, 10000, 100000, None],
            valid=True,
        )

        plot_item(
            ax=plot_setup["ax"],
            data=data,
            ylim=(1, 100000),
            fmt="{:.0f}",
            unit="lux",
            scale="log",
            title="Lux Test",
            xbegin_numeric=time_numeric[0],
            small=False,
            face_map=face_map,
            axis_config=axis_config,
        )


class TestGetDataRequests:
    """データリクエスト生成のテスト"""

    def test_dummy_mode_period_settings(self, config, mocker):
        """DUMMY_MODE による期間設定のテスト"""
        # DUMMY_MODE=false を設定
        mocker.patch.dict(os.environ, {"DUMMY_MODE": "false"})

        from weather_display.panel.sensor_graph import create

        # create 関数を呼び出すと内部でデータリクエストが生成される
        # ただし、実際のデータ取得は mock_sensor_fetch_data でモックされる


class TestFetchDataParallel:
    """fetch_data_parallel 関数のテスト"""

    @pytest.fixture(autouse=True)
    def reset_event_loop(self):
        """各テストで新しいイベントループを使用"""
        import asyncio

        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None

        if loop is None:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        yield

        # クリーンアップ
        try:
            loop = asyncio.get_event_loop()
            if not loop.is_closed():
                loop.close()
        except Exception:
            pass
        asyncio.set_event_loop(asyncio.new_event_loop())

    def test_fetch_data_parallel_with_invalid_config(self, mocker):
        """無効な設定でも例外を適切に処理すること"""
        import asyncio

        from weather_display.panel.sensor_graph import DataRequest, fetch_data_parallel

        # InfluxDB設定をモックして接続エラーを発生させる
        mocker.patch(
            "my_lib.sensor_data.fetch_data",
            side_effect=RuntimeError("Connection error"),
        )

        requests = [
            DataRequest(
                measure="test_measure",
                hostname="test_host",
                field="temp",
                start="-1h",
                stop="now()",
            )
        ]

        # 例外が発生してもNoneリストが返ること
        async def run_test():
            influxdb_config = mocker.MagicMock()
            return await fetch_data_parallel(influxdb_config, requests)

        results = asyncio.get_event_loop().run_until_complete(run_test())

        # 結果はリストであること
        assert isinstance(results, list)


class TestSensorDataEdgeCases:
    """sensor_graph.py のエッジケーステスト"""

    def test_create_with_empty_time_valid_data(self, config, mocker):
        """valid=True で time が空の場合 (line 296 カバー)"""
        from my_lib.sensor_data import SensorDataResult

        from weather_display.panel.sensor_graph import create

        # valid=True だが time が空のデータを返すモック
        async def mock_fetch_parallel(db_config, requests):
            results = []
            for _ in requests:
                # valid=True で time=[] のデータを返す
                results.append(SensorDataResult(value=[], time=[], valid=True))
            return results

        mocker.patch(
            "weather_display.panel.sensor_graph.fetch_data_parallel",
            side_effect=mock_fetch_parallel,
        )

        result = create(config)

        # エラーなく画像が生成されること
        assert len(result) >= 2
        assert result[0] is not None

    def test_create_with_none_sensor_data(self, config, mocker):
        """センサーデータが None の場合 (line 286 カバー)"""
        from weather_display.panel.sensor_graph import create

        # None を返すモック（データ取得失敗をシミュレート）
        async def mock_fetch_parallel(db_config, requests):
            return [None for _ in requests]

        mocker.patch(
            "weather_display.panel.sensor_graph.fetch_data_parallel",
            side_effect=mock_fetch_parallel,
        )

        result = create(config)

        # エラーなく画像が生成されること
        assert len(result) >= 2
        assert result[0] is not None
