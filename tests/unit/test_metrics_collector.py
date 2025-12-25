#!/usr/bin/env python3
# ruff: noqa: S101
"""
メトリクス収集・分析のユニットテスト
"""
import datetime
import pathlib
import tempfile
import zoneinfo

import pytest


class TestMetricsCollector:
    """MetricsCollector クラスのテスト"""

    @pytest.fixture
    def temp_db(self):
        """一時的なデータベースを作成"""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = pathlib.Path(tmpdir) / "test_metrics.db"
            yield db_path

    @pytest.fixture
    def collector(self, temp_db):
        """MetricsCollector インスタンスを作成"""
        from weather_display.metrics.collector import MetricsCollector

        return MetricsCollector(db_path=temp_db)

    def test_init_creates_database(self, temp_db):
        """初期化でデータベースが作成されること"""
        from weather_display.metrics.collector import MetricsCollector

        collector = MetricsCollector(db_path=temp_db)

        assert temp_db.exists()
        assert collector.db_path == temp_db

    def test_log_draw_panel_metrics_returns_positive_id(self, collector):
        """log_draw_panel_metrics が正のIDを返すこと"""
        panel_metrics = [
            {"name": "weather", "elapsed_time": 1.5, "has_error": False},
            {"name": "sensor", "elapsed_time": 2.0, "has_error": False},
        ]

        result = collector.log_draw_panel_metrics(
            total_elapsed_time=5.0,
            panel_metrics=panel_metrics,
        )

        assert result > 0

    def test_log_draw_panel_metrics_with_all_parameters(self, collector):
        """全パラメータ指定で log_draw_panel_metrics が動作すること"""
        tz = zoneinfo.ZoneInfo("Asia/Tokyo")
        panel_metrics = [
            {"name": "weather", "elapsed_time": 1.5, "has_error": False},
        ]

        result = collector.log_draw_panel_metrics(
            total_elapsed_time=5.0,
            panel_metrics=panel_metrics,
            is_small_mode=True,
            is_test_mode=True,
            is_dummy_mode=True,
            error_code=1,
            timestamp=datetime.datetime.now(tz),
        )

        assert result > 0

    def test_log_draw_panel_metrics_with_error(self, collector):
        """エラーありのパネルメトリクスが保存できること"""
        panel_metrics = [
            {
                "name": "weather",
                "elapsed_time": 1.5,
                "has_error": True,
                "error_message": "Test error",
            },
        ]

        result = collector.log_draw_panel_metrics(
            total_elapsed_time=5.0,
            panel_metrics=panel_metrics,
        )

        assert result > 0

    def test_log_display_image_metrics_returns_positive_id(self, collector):
        """log_display_image_metrics が正のIDを返すこと"""
        result = collector.log_display_image_metrics(
            elapsed_time=10.0,
        )

        assert result > 0

    def test_log_display_image_metrics_with_all_parameters(self, collector):
        """全パラメータ指定で log_display_image_metrics が動作すること"""
        tz = zoneinfo.ZoneInfo("Asia/Tokyo")

        result = collector.log_display_image_metrics(
            elapsed_time=10.0,
            is_small_mode=True,
            is_test_mode=True,
            is_one_time=True,
            rasp_hostname="test-host",
            success=True,
            error_message=None,
            timestamp=datetime.datetime.now(tz),
            sleep_time=50.0,
            diff_sec=5,
        )

        assert result > 0

    def test_log_display_image_metrics_with_failure(self, collector):
        """失敗時のメトリクスが保存できること"""
        result = collector.log_display_image_metrics(
            elapsed_time=10.0,
            success=False,
            error_message="Test failure",
        )

        assert result > 0

    def test_multiple_logs_have_unique_ids(self, collector):
        """複数のログが異なるIDを持つこと"""
        ids = []
        for i in range(5):
            result = collector.log_display_image_metrics(
                elapsed_time=float(i),
            )
            ids.append(result)

        assert len(ids) == len(set(ids))  # 全て異なるID


class TestMetricsAnalyzer:
    """MetricsAnalyzer クラスのテスト"""

    @pytest.fixture
    def temp_db_with_data(self):
        """テストデータ入りの一時データベースを作成"""
        from weather_display.metrics.collector import MetricsCollector

        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = pathlib.Path(tmpdir) / "test_metrics.db"
            collector = MetricsCollector(db_path=db_path)

            # テストデータを追加
            tz = zoneinfo.ZoneInfo("Asia/Tokyo")
            base_time = datetime.datetime.now(tz)

            for i in range(20):
                timestamp = base_time - datetime.timedelta(hours=i)
                collector.log_draw_panel_metrics(
                    total_elapsed_time=30.0 + (i % 5),
                    panel_metrics=[
                        {"name": "weather", "elapsed_time": 10.0 + (i % 3)},
                        {"name": "sensor", "elapsed_time": 15.0 + (i % 4)},
                    ],
                    timestamp=timestamp,
                )
                collector.log_display_image_metrics(
                    elapsed_time=60.0 + (i % 10),
                    success=i % 10 != 0,  # 10回に1回失敗
                    timestamp=timestamp,
                    sleep_time=50.0,
                    diff_sec=i % 30 - 15,
                )

            yield db_path

    @pytest.fixture
    def analyzer(self, temp_db_with_data):
        """MetricsAnalyzer インスタンスを作成"""
        from weather_display.metrics.collector import MetricsAnalyzer

        return MetricsAnalyzer(db_path=temp_db_with_data)

    def test_init_raises_on_missing_db(self):
        """存在しないDBファイルで FileNotFoundError が発生すること"""
        from weather_display.metrics.collector import MetricsAnalyzer

        with pytest.raises(FileNotFoundError):
            MetricsAnalyzer(db_path="/nonexistent/path/metrics.db")

    def test_get_data_range_returns_dict(self, analyzer):
        """get_data_range が辞書を返すこと"""
        result = analyzer.get_data_range()

        assert isinstance(result, dict)
        assert "draw_panel" in result
        assert "display_image" in result
        assert "overall" in result

    def test_get_basic_statistics_returns_dict(self, analyzer):
        """get_basic_statistics が辞書を返すこと"""
        result = analyzer.get_basic_statistics()

        assert isinstance(result, dict)
        assert "draw_panel" in result
        assert "display_image" in result
        assert result["draw_panel"]["total_operations"] > 0

    def test_get_hourly_patterns_returns_dict(self, analyzer):
        """get_hourly_patterns が辞書を返すこと"""
        result = analyzer.get_hourly_patterns()

        assert isinstance(result, dict)
        assert "draw_panel" in result
        assert "display_image" in result

    def test_detect_anomalies_returns_dict(self, analyzer):
        """detect_anomalies が辞書を返すこと"""
        result = analyzer.detect_anomalies()

        assert isinstance(result, dict)

    def test_detect_anomalies_with_custom_contamination(self, analyzer):
        """カスタム contamination パラメータで動作すること"""
        result = analyzer.detect_anomalies(contamination=0.05)

        assert isinstance(result, dict)

    def test_get_performance_trends_returns_dict(self, analyzer):
        """get_performance_trends が辞書を返すこと"""
        result = analyzer.get_performance_trends()

        assert isinstance(result, dict)
        assert "draw_panel" in result
        assert "display_image" in result

    def test_check_performance_alerts_returns_list(self, analyzer):
        """check_performance_alerts がリストを返すこと"""
        result = analyzer.check_performance_alerts()

        assert isinstance(result, list)

    def test_check_performance_alerts_with_custom_thresholds(self, analyzer):
        """カスタム閾値で check_performance_alerts が動作すること"""
        custom_thresholds = {
            "draw_panel_max_time": 10.0,  # 厳しい閾値
            "display_image_max_time": 30.0,
            "error_rate_threshold": 5.0,
            "recent_hours": 48,
        }

        result = analyzer.check_performance_alerts(thresholds=custom_thresholds)

        assert isinstance(result, list)

    def test_get_panel_performance_trends_returns_dict(self, analyzer):
        """get_panel_performance_trends が辞書を返すこと"""
        result = analyzer.get_panel_performance_trends()

        assert isinstance(result, dict)

    def test_get_performance_statistics_returns_dict(self, analyzer):
        """get_performance_statistics が辞書を返すこと"""
        result = analyzer.get_performance_statistics()

        assert isinstance(result, dict)
        assert "draw_panel" in result
        assert "display_image" in result


class TestGlobalFunctions:
    """グローバル関数のテスト"""

    @pytest.fixture
    def temp_db(self):
        """一時的なデータベースを作成"""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = pathlib.Path(tmpdir) / "test_metrics.db"
            yield db_path

    def test_get_metrics_collector_returns_collector(self, temp_db):
        """get_metrics_collector が MetricsCollector を返すこと"""
        from weather_display.metrics.collector import MetricsCollector, get_metrics_collector

        # グローバル変数をリセット
        import weather_display.metrics.collector

        weather_display.metrics.collector._metrics_collector = None

        result = get_metrics_collector(db_path=temp_db)

        assert isinstance(result, MetricsCollector)

    def test_collect_draw_panel_metrics_works(self, temp_db):
        """collect_draw_panel_metrics が動作すること"""
        from weather_display.metrics.collector import collect_draw_panel_metrics

        # グローバル変数をリセット
        import weather_display.metrics.collector

        weather_display.metrics.collector._metrics_collector = None

        result = collect_draw_panel_metrics(
            total_elapsed_time=5.0,
            panel_metrics=[{"name": "test", "elapsed_time": 1.0}],
            db_path=temp_db,
        )

        assert result > 0

    def test_collect_display_image_metrics_works(self, temp_db):
        """collect_display_image_metrics が動作すること"""
        from weather_display.metrics.collector import collect_display_image_metrics

        # グローバル変数をリセット
        import weather_display.metrics.collector

        weather_display.metrics.collector._metrics_collector = None

        result = collect_display_image_metrics(
            elapsed_time=10.0,
            db_path=temp_db,
        )

        assert result > 0

    def test_collect_draw_panel_metrics_without_db_path(self, temp_db):
        """db_path なしで collect_draw_panel_metrics が動作すること"""
        from weather_display.metrics.collector import collect_draw_panel_metrics, get_metrics_collector

        # グローバル変数をリセット
        import weather_display.metrics.collector

        weather_display.metrics.collector._metrics_collector = None

        # 先にグローバルコレクターを作成
        get_metrics_collector(db_path=temp_db)

        result = collect_draw_panel_metrics(
            total_elapsed_time=5.0,
            panel_metrics=[{"name": "test", "elapsed_time": 1.0}],
        )

        assert result > 0

    def test_collect_display_image_metrics_without_db_path(self, temp_db):
        """db_path なしで collect_display_image_metrics が動作すること"""
        from weather_display.metrics.collector import collect_display_image_metrics, get_metrics_collector

        # グローバル変数をリセット
        import weather_display.metrics.collector

        weather_display.metrics.collector._metrics_collector = None

        # 先にグローバルコレクターを作成
        get_metrics_collector(db_path=temp_db)

        result = collect_display_image_metrics(
            elapsed_time=10.0,
        )

        assert result > 0


class TestMetricsCollectorExceptionHandling:
    """MetricsCollector 例外処理のテスト"""

    @pytest.fixture
    def temp_db(self):
        """一時的なデータベースを作成"""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = pathlib.Path(tmpdir) / "test_metrics.db"
            yield db_path

    def test_log_draw_panel_metrics_handles_db_error(self, temp_db, mocker):
        """log_draw_panel_metrics がデータベースエラーを処理すること"""
        from weather_display.metrics.collector import MetricsCollector

        collector = MetricsCollector(db_path=temp_db)

        # データベース接続をモックしてエラーを発生させる
        mocker.patch.object(
            collector, "_get_connection", side_effect=Exception("Database error")
        )

        result = collector.log_draw_panel_metrics(
            total_elapsed_time=5.0,
            panel_metrics=[{"name": "test", "elapsed_time": 1.0}],
        )

        assert result == -1

    def test_log_display_image_metrics_handles_db_error(self, temp_db, mocker):
        """log_display_image_metrics がデータベースエラーを処理すること"""
        from weather_display.metrics.collector import MetricsCollector

        collector = MetricsCollector(db_path=temp_db)

        # データベース接続をモックしてエラーを発生させる
        mocker.patch.object(
            collector, "_get_connection", side_effect=Exception("Database error")
        )

        result = collector.log_display_image_metrics(
            elapsed_time=10.0,
        )

        assert result == -1


class TestMetricsAnalyzerEdgeCases:
    """MetricsAnalyzer エッジケースのテスト"""

    @pytest.fixture
    def temp_db_draw_panel_only(self):
        """draw_panelのみのデータを持つ一時データベースを作成"""
        from weather_display.metrics.collector import MetricsCollector

        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = pathlib.Path(tmpdir) / "test_metrics.db"
            collector = MetricsCollector(db_path=db_path)

            # draw_panel のみテストデータを追加
            tz = zoneinfo.ZoneInfo("Asia/Tokyo")
            base_time = datetime.datetime.now(tz)

            for i in range(5):
                timestamp = base_time - datetime.timedelta(hours=i)
                collector.log_draw_panel_metrics(
                    total_elapsed_time=30.0 + i,
                    panel_metrics=[{"name": "weather", "elapsed_time": 10.0}],
                    timestamp=timestamp,
                )

            yield db_path

    @pytest.fixture
    def temp_db_display_image_only(self):
        """display_imageのみのデータを持つ一時データベースを作成"""
        from weather_display.metrics.collector import MetricsCollector

        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = pathlib.Path(tmpdir) / "test_metrics.db"
            collector = MetricsCollector(db_path=db_path)

            # display_image のみテストデータを追加
            tz = zoneinfo.ZoneInfo("Asia/Tokyo")
            base_time = datetime.datetime.now(tz)

            for i in range(5):
                timestamp = base_time - datetime.timedelta(hours=i)
                collector.log_display_image_metrics(
                    elapsed_time=60.0 + i,
                    timestamp=timestamp,
                )

            yield db_path

    @pytest.fixture
    def temp_db_minimal_data(self):
        """最小限のデータを持つ一時データベースを作成（1件のみ）"""
        from weather_display.metrics.collector import MetricsCollector

        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = pathlib.Path(tmpdir) / "test_metrics.db"
            collector = MetricsCollector(db_path=db_path)

            # 1件のみテストデータを追加
            collector.log_draw_panel_metrics(
                total_elapsed_time=30.0,
                panel_metrics=[{"name": "weather", "elapsed_time": 10.0}],
            )
            collector.log_display_image_metrics(
                elapsed_time=60.0,
            )

            yield db_path

    def test_get_data_range_with_draw_panel_only(self, temp_db_draw_panel_only):
        """draw_panelのみの場合のget_data_range"""
        from weather_display.metrics.collector import MetricsAnalyzer

        analyzer = MetricsAnalyzer(db_path=temp_db_draw_panel_only)
        result = analyzer.get_data_range()

        assert result["overall"]["earliest"] is not None
        assert result["overall"]["latest"] is not None
        assert result["display_image"]["total_count"] == 0

    def test_get_data_range_with_display_image_only(self, temp_db_display_image_only):
        """display_imageのみの場合のget_data_range"""
        from weather_display.metrics.collector import MetricsAnalyzer

        analyzer = MetricsAnalyzer(db_path=temp_db_display_image_only)
        result = analyzer.get_data_range()

        assert result["overall"]["earliest"] is not None
        assert result["overall"]["latest"] is not None
        assert result["draw_panel"]["total_count"] == 0

    @pytest.fixture
    def temp_db_empty(self):
        """空のデータベースを作成"""
        from weather_display.metrics.collector import MetricsCollector

        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = pathlib.Path(tmpdir) / "test_metrics.db"
            # Collector を初期化してテーブルを作成するが、データは追加しない
            MetricsCollector(db_path=db_path)

            yield db_path

    def test_get_data_range_with_empty_database(self, temp_db_empty):
        """空のデータベースでのget_data_range (lines 345->348, 352->355)"""
        from weather_display.metrics.collector import MetricsAnalyzer

        analyzer = MetricsAnalyzer(db_path=temp_db_empty)
        result = analyzer.get_data_range()

        # 両方のテーブルが空なので、overall の earliest/latest は None
        assert result["overall"]["earliest"] is None
        assert result["overall"]["latest"] is None
        assert result["draw_panel"]["total_count"] == 0
        assert result["display_image"]["total_count"] == 0

    def test_detect_anomalies_with_insufficient_data(self, temp_db_minimal_data):
        """データが少ない場合のdetect_anomalies"""
        from weather_display.metrics.collector import MetricsAnalyzer

        analyzer = MetricsAnalyzer(db_path=temp_db_minimal_data)
        result = analyzer.detect_anomalies()

        # データが10件以下なのでdraw_panel/display_imageキーがない
        assert "draw_panel" not in result or result.get("draw_panel") is None
        assert "display_image" not in result or result.get("display_image") is None

    def test_get_performance_statistics_with_single_record(self, temp_db_minimal_data):
        """1件のみのデータでのget_performance_statistics"""
        from weather_display.metrics.collector import MetricsAnalyzer

        analyzer = MetricsAnalyzer(db_path=temp_db_minimal_data)
        result = analyzer.get_performance_statistics()

        # 1件のみなので std_time は 0
        assert result["draw_panel"]["std_time"] == 0
        assert result["display_image"]["std_time"] == 0

    def test_get_connection_raises_exception(self, temp_db_minimal_data, mocker):
        """_get_connection で例外が発生した場合に再度発生させること"""
        from weather_display.metrics.collector import MetricsAnalyzer

        analyzer = MetricsAnalyzer(db_path=temp_db_minimal_data)

        # sqlite_util.connect をモックしてエラーを発生させる
        mocker.patch(
            "my_lib.sqlite_util.connect",
            side_effect=Exception("Database connection error"),
        )

        with pytest.raises(Exception, match="Database connection error"):
            analyzer.get_basic_statistics()


class TestMetricsCollectorDatabaseError:
    """MetricsCollector のデータベースエラーテスト"""

    @pytest.fixture
    def temp_db(self):
        """一時的なデータベースを作成"""
        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = pathlib.Path(tmpdir) / "test_metrics.db"
            yield db_path

    def test_get_connection_database_error(self, temp_db, mocker):
        """_get_connection でデータベースエラー時に例外が再スローされること (line 115-117)"""
        from weather_display.metrics.collector import MetricsCollector

        collector = MetricsCollector(db_path=temp_db)

        # sqlite_util.connect をモックしてエラーを発生させる
        mocker.patch(
            "my_lib.sqlite_util.connect",
            side_effect=Exception("Database error"),
        )

        with pytest.raises(Exception, match="Database error"):
            with collector._get_connection():
                pass
