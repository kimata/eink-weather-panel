#!/usr/bin/env python3
# ruff: noqa: S101
"""
metrics/webapi/page.py のユニットテスト

HTML生成関数と各種エンドポイントのテスト
"""
import datetime

import pytest


class TestGenerateMetricsHtml:
    """generate_metrics_html 関数のテスト"""

    @pytest.fixture
    def sample_data(self):
        """テスト用サンプルデータ"""
        return {
            "basic_stats": {
                "draw_panel": {
                    "total_operations": 100,
                    "error_count": 5,
                    "avg_elapsed_time": 10.5,
                    "max_elapsed_time": 30.0,
                },
                "display_image": {
                    "total_operations": 95,
                    "failure_count": 2,
                    "avg_elapsed_time": 15.0,
                    "max_elapsed_time": 45.0,
                },
            },
            "hourly_patterns": {
                "draw_panel": [{"hour": i, "avg_elapsed_time": 10.0 + i} for i in range(24)],
                "display_image": [{"hour": i, "avg_elapsed_time": 15.0 + i} for i in range(24)],
            },
            "anomalies": {
                "draw_panel": {
                    "anomalies_detected": 3,
                    "anomaly_rate": 0.03,
                    "anomalies": [
                        {
                            "timestamp": "2024-12-20T10:00:00+09:00",
                            "elapsed_time": 120.5,
                            "hour": 10,
                            "error_code": 0,
                        },
                        {
                            "timestamp": "2024-12-19T14:30:00+09:00",
                            "elapsed_time": 0.5,
                            "hour": 14,
                            "error_code": 220,
                        },
                    ],
                },
                "display_image": {
                    "anomalies_detected": 1,
                    "anomaly_rate": 0.01,
                    "anomalies": [
                        {
                            "timestamp": "2024-12-20T08:00:00+09:00",
                            "elapsed_time": 180.0,
                            "hour": 8,
                            "success": True,
                        },
                        {
                            "timestamp": "2024-12-19T16:00:00+09:00",
                            "elapsed_time": 2.0,
                            "hour": 16,
                            "success": False,
                        },
                    ],
                },
            },
            "trends": {
                "draw_panel": [{"date": "2024-12-01", "avg_time": 10.0}],
                "display_image": [{"date": "2024-12-01", "avg_time": 15.0}],
            },
            "alerts": [],
            "panel_trends": {"weather": [10.0, 12.0, 11.0]},
            "performance_stats": {
                "draw_panel": {"avg_time": 10.0, "std_time": 2.0},
                "display_image": {"avg_time": 15.0, "std_time": 3.0},
            },
            "data_range": {
                "overall": {
                    "earliest": "2024-12-01T00:00:00+09:00",
                    "latest": "2024-12-25T23:59:59+09:00",
                }
            },
        }

    def test_generate_metrics_html_returns_valid_html(self, sample_data):
        """有効なHTMLを生成すること"""
        from weather_display.metrics.webapi.page import generate_metrics_html

        html = generate_metrics_html(
            sample_data["basic_stats"],
            sample_data["hourly_patterns"],
            sample_data["anomalies"],
            sample_data["trends"],
            sample_data["alerts"],
            sample_data["panel_trends"],
            sample_data["performance_stats"],
            sample_data["data_range"],
        )

        assert "<!DOCTYPE html>" in html
        assert "<html" in html
        assert "</html>" in html
        assert "天気パネル メトリクス ダッシュボード" in html

    def test_generate_metrics_html_with_alerts(self, sample_data):
        """アラートがある場合のHTMLを生成すること"""
        from weather_display.metrics.webapi.page import generate_metrics_html

        sample_data["alerts"] = [
            {"type": "high_error_rate", "message": "エラー率が高い", "severity": "critical"},
            {"type": "slow_processing", "message": "処理が遅い", "severity": "warning"},
            {"type": "info_alert", "message": "情報アラート", "severity": "info"},
        ]

        html = generate_metrics_html(
            sample_data["basic_stats"],
            sample_data["hourly_patterns"],
            sample_data["anomalies"],
            sample_data["trends"],
            sample_data["alerts"],
            sample_data["panel_trends"],
            sample_data["performance_stats"],
            sample_data["data_range"],
        )

        assert "is-danger" in html  # critical
        assert "is-warning" in html  # warning
        assert "is-info" in html  # info
        assert "エラー率が高い" in html

    def test_generate_metrics_html_with_invalid_date_range(self, sample_data):
        """無効な日付範囲でもエラーにならないこと"""
        from weather_display.metrics.webapi.page import generate_metrics_html

        sample_data["data_range"]["overall"]["earliest"] = "invalid_date"

        html = generate_metrics_html(
            sample_data["basic_stats"],
            sample_data["hourly_patterns"],
            sample_data["anomalies"],
            sample_data["trends"],
            sample_data["alerts"],
            sample_data["panel_trends"],
            sample_data["performance_stats"],
            sample_data["data_range"],
        )

        assert "<!DOCTYPE html>" in html

    def test_generate_metrics_html_with_none_data_range(self, sample_data):
        """data_range が None の場合 (branch 584->604)"""
        from weather_display.metrics.webapi.page import generate_metrics_html

        html = generate_metrics_html(
            sample_data["basic_stats"],
            sample_data["hourly_patterns"],
            sample_data["anomalies"],
            sample_data["trends"],
            sample_data["alerts"],
            sample_data["panel_trends"],
            sample_data["performance_stats"],
            None,  # data_range = None
        )

        assert "<!DOCTYPE html>" in html
        # デフォルトのサブタイトルが使われること
        assert "パフォーマンス監視と異常検知" in html

    def test_generate_metrics_html_with_none_earliest(self, sample_data):
        """earliest が None の場合 (branch 584->604)"""
        from weather_display.metrics.webapi.page import generate_metrics_html

        sample_data["data_range"]["overall"]["earliest"] = None

        html = generate_metrics_html(
            sample_data["basic_stats"],
            sample_data["hourly_patterns"],
            sample_data["anomalies"],
            sample_data["trends"],
            sample_data["alerts"],
            sample_data["panel_trends"],
            sample_data["performance_stats"],
            sample_data["data_range"],
        )

        assert "<!DOCTYPE html>" in html
        # デフォルトのサブタイトルが使われること
        assert "パフォーマンス監視と異常検知" in html


class TestGenerateAlertsSection:
    """generate_alerts_section 関数のテスト"""

    def test_no_alerts_shows_success_message(self):
        """アラートがない場合は成功メッセージを表示すること"""
        from weather_display.metrics.webapi.page import generate_alerts_section

        html = generate_alerts_section([])

        assert "is-success" in html
        assert "パフォーマンスアラートは検出されていません" in html

    def test_alerts_with_critical_severity(self):
        """critical アラートが正しく表示されること"""
        from weather_display.metrics.webapi.page import generate_alerts_section

        alerts = [
            {"type": "error_rate", "message": "テストエラー", "severity": "critical"},
        ]

        html = generate_alerts_section(alerts)

        assert "is-danger" in html
        assert "テストエラー" in html

    def test_alerts_with_unknown_severity(self):
        """不明な severity でもエラーにならないこと"""
        from weather_display.metrics.webapi.page import generate_alerts_section

        alerts = [
            {"type": "unknown", "message": "不明なアラート", "severity": "unknown_level"},
        ]

        html = generate_alerts_section(alerts)

        assert "is-info" in html  # デフォルト


class TestGenerateBasicStatsSection:
    """generate_basic_stats_section 関数のテスト"""

    def test_basic_stats_displays_values(self):
        """統計値が正しく表示されること"""
        from weather_display.metrics.webapi.page import generate_basic_stats_section

        stats = {
            "draw_panel": {
                "total_operations": 1000,
                "error_count": 10,
                "avg_elapsed_time": 12.345,
                "max_elapsed_time": 60.0,
            },
            "display_image": {
                "total_operations": 950,
                "failure_count": 5,
                "avg_elapsed_time": 20.0,
                "max_elapsed_time": 120.0,
            },
        }

        html = generate_basic_stats_section(stats)

        assert "1,000" in html  # total_operations formatted
        assert "12.35" in html or "12.34" in html  # avg_elapsed_time formatted

    def test_basic_stats_with_empty_data(self):
        """空データでもエラーにならないこと"""
        from weather_display.metrics.webapi.page import generate_basic_stats_section

        html = generate_basic_stats_section({})

        assert "画像生成処理" in html
        assert "表示実行処理" in html


class TestGenerateHourlyPatternsSection:
    """generate_hourly_patterns_section 関数のテスト"""

    def test_hourly_patterns_section_structure(self):
        """時間別パターンセクションの構造が正しいこと"""
        from weather_display.metrics.webapi.page import generate_hourly_patterns_section

        html = generate_hourly_patterns_section({})

        assert "hourly-patterns" in html
        assert "drawPanelHourlyChart" in html
        assert "displayImageHourlyChart" in html


class TestGenerateTrendsSection:
    """generate_trends_section 関数のテスト"""

    def test_trends_section_structure(self):
        """トレンドセクションの構造が正しいこと"""
        from weather_display.metrics.webapi.page import generate_trends_section

        html = generate_trends_section({})

        assert "performance-trends" in html
        assert "drawPanelTrendsChart" in html
        assert "displayImageTrendsChart" in html


class TestGenerateDiffSecSection:
    """generate_diff_sec_section 関数のテスト"""

    def test_diff_sec_section_structure(self):
        """表示タイミングセクションの構造が正しいこと"""
        from weather_display.metrics.webapi.page import generate_diff_sec_section

        html = generate_diff_sec_section()

        assert "display-timing" in html
        assert "diffSecHourlyChart" in html
        assert "diffSecBoxplotChart" in html


class TestGeneratePanelTrendsSection:
    """generate_panel_trends_section 関数のテスト"""

    def test_panel_trends_section_structure(self):
        """パネル別トレンドセクションの構造が正しいこと"""
        from weather_display.metrics.webapi.page import generate_panel_trends_section

        html = generate_panel_trends_section({})

        assert "panel-trends" in html
        assert "panelTrendsContainer" in html
        assert "panel-timeseries" in html


class TestGenerateAnomaliesSection:
    """generate_anomalies_section 関数のテスト"""

    @pytest.fixture
    def sample_anomalies(self):
        """サンプル異常データ"""
        return {
            "draw_panel": {
                "anomalies_detected": 2,
                "anomaly_rate": 0.02,
                "anomalies": [
                    {
                        "timestamp": "2024-12-20T10:30:00+09:00",
                        "elapsed_time": 120.0,
                        "hour": 10,
                        "error_code": 0,
                    },
                    {
                        "timestamp": "2024-12-20T14:00:00+09:00",
                        "elapsed_time": 0.3,
                        "hour": 14,
                        "error_code": 220,
                    },
                ],
            },
            "display_image": {
                "anomalies_detected": 1,
                "anomaly_rate": 0.01,
                "anomalies": [
                    {
                        "timestamp": "2024-12-20T08:00:00+09:00",
                        "elapsed_time": 200.0,
                        "hour": 8,
                        "success": False,
                    },
                ],
            },
        }

    @pytest.fixture
    def sample_performance_stats(self):
        """サンプルパフォーマンス統計"""
        return {
            "draw_panel": {"avg_time": 10.0, "std_time": 2.0},
            "display_image": {"avg_time": 15.0, "std_time": 3.0},
        }

    def test_anomalies_section_shows_count(self, sample_anomalies, sample_performance_stats):
        """異常件数が表示されること"""
        from weather_display.metrics.webapi.page import generate_anomalies_section

        html = generate_anomalies_section(sample_anomalies, sample_performance_stats)

        assert "検出された異常数" in html
        assert "異常率" in html

    def test_anomalies_section_with_long_elapsed_time(self, sample_anomalies, sample_performance_stats):
        """長時間処理の異常が表示されること"""
        from weather_display.metrics.webapi.page import generate_anomalies_section

        html = generate_anomalies_section(sample_anomalies, sample_performance_stats)

        assert "長時間処理" in html

    def test_anomalies_section_with_short_elapsed_time(self, sample_anomalies, sample_performance_stats):
        """短時間処理の異常が表示されること"""
        from weather_display.metrics.webapi.page import generate_anomalies_section

        html = generate_anomalies_section(sample_anomalies, sample_performance_stats)

        assert "短時間処理" in html

    def test_anomalies_section_with_error_code(self, sample_anomalies, sample_performance_stats):
        """エラーコードが表示されること"""
        from weather_display.metrics.webapi.page import generate_anomalies_section

        html = generate_anomalies_section(sample_anomalies, sample_performance_stats)

        assert "エラー発生" in html

    def test_anomalies_section_with_failure(self, sample_anomalies, sample_performance_stats):
        """実行失敗が表示されること"""
        from weather_display.metrics.webapi.page import generate_anomalies_section

        html = generate_anomalies_section(sample_anomalies, sample_performance_stats)

        assert "実行失敗" in html

    def test_anomalies_section_without_anomalies(self, sample_performance_stats):
        """異常がない場合も正常に動作すること"""
        from weather_display.metrics.webapi.page import generate_anomalies_section

        anomalies = {
            "draw_panel": {"anomalies_detected": 0, "anomaly_rate": 0},
            "display_image": {"anomalies_detected": 0, "anomaly_rate": 0},
        }

        html = generate_anomalies_section(anomalies, sample_performance_stats)

        assert "anomaly-detection" in html

    def test_anomalies_section_with_unknown_timestamp(self, sample_performance_stats):
        """不明なタイムスタンプでも正常に動作すること"""
        from weather_display.metrics.webapi.page import generate_anomalies_section

        anomalies = {
            "draw_panel": {
                "anomalies_detected": 1,
                "anomaly_rate": 0.01,
                "anomalies": [
                    {
                        "timestamp": "不明",
                        "elapsed_time": 10.0,
                        "hour": 10,
                        "error_code": 0,
                    },
                ],
            },
            "display_image": {"anomalies_detected": 0, "anomaly_rate": 0},
        }

        html = generate_anomalies_section(anomalies, sample_performance_stats)

        assert "不明" in html

    def test_anomalies_section_with_pattern_anomaly(self, sample_performance_stats):
        """パターン異常（条件に該当しない異常）が表示されること"""
        from weather_display.metrics.webapi.page import generate_anomalies_section

        anomalies = {
            "draw_panel": {
                "anomalies_detected": 1,
                "anomaly_rate": 0.01,
                "anomalies": [
                    {
                        "timestamp": "2024-12-20T10:00:00+09:00",
                        "elapsed_time": 30.0,  # 長時間でも短時間でもない
                        "hour": 10,
                        "error_code": 0,
                    },
                ],
            },
            "display_image": {
                "anomalies_detected": 1,
                "anomaly_rate": 0.01,
                "anomalies": [
                    {
                        "timestamp": "2024-12-20T10:00:00+09:00",
                        "elapsed_time": 30.0,  # 長時間でも短時間でもない
                        "hour": 10,
                        "success": True,
                    },
                ],
            },
        }

        html = generate_anomalies_section(anomalies, sample_performance_stats)

        assert "パターン異常" in html

    def test_anomalies_section_with_various_elapsed_times(self, sample_performance_stats):
        """様々な経過時間での表示テスト"""
        import time

        from weather_display.metrics.webapi.page import generate_anomalies_section

        # 各種経過時間を持つ異常を作成（日、時、分、たった今）
        import datetime
        import zoneinfo

        tz = zoneinfo.ZoneInfo("Asia/Tokyo")
        now = datetime.datetime.now(tz)

        anomalies = {
            "draw_panel": {
                "anomalies_detected": 4,
                "anomaly_rate": 0.04,
                "anomalies": [
                    {
                        "timestamp": (now - datetime.timedelta(days=2)).isoformat(),
                        "elapsed_time": 120.0,
                        "hour": 10,
                        "error_code": 0,
                    },
                    {
                        "timestamp": (now - datetime.timedelta(hours=3)).isoformat(),
                        "elapsed_time": 120.0,
                        "hour": 10,
                        "error_code": 0,
                    },
                    {
                        "timestamp": (now - datetime.timedelta(minutes=30)).isoformat(),
                        "elapsed_time": 120.0,
                        "hour": 10,
                        "error_code": 0,
                    },
                    {
                        "timestamp": (now - datetime.timedelta(seconds=10)).isoformat(),
                        "elapsed_time": 120.0,
                        "hour": 10,
                        "error_code": 0,
                    },
                ],
            },
            "display_image": {
                "anomalies_detected": 4,
                "anomaly_rate": 0.04,
                "anomalies": [
                    {
                        "timestamp": (now - datetime.timedelta(days=2)).isoformat(),
                        "elapsed_time": 200.0,
                        "hour": 10,
                        "success": False,
                    },
                    {
                        "timestamp": (now - datetime.timedelta(hours=3)).isoformat(),
                        "elapsed_time": 200.0,
                        "hour": 10,
                        "success": False,
                    },
                    {
                        "timestamp": (now - datetime.timedelta(minutes=30)).isoformat(),
                        "elapsed_time": 200.0,
                        "hour": 10,
                        "success": False,
                    },
                    {
                        "timestamp": (now - datetime.timedelta(seconds=10)).isoformat(),
                        "elapsed_time": 200.0,
                        "hour": 10,
                        "success": False,
                    },
                ],
            },
        }

        html = generate_anomalies_section(anomalies, sample_performance_stats)

        # 各種経過時間表示があること
        assert "日前" in html
        assert "時間前" in html
        assert "分前" in html
        assert "たった今" in html

    def test_anomalies_section_display_image_time_ranges(self, sample_performance_stats):
        """display_image の時間範囲テスト（短時間・長時間）"""
        from weather_display.metrics.webapi.page import generate_anomalies_section

        anomalies = {
            "draw_panel": {"anomalies_detected": 0, "anomaly_rate": 0},
            "display_image": {
                "anomalies_detected": 2,
                "anomaly_rate": 0.02,
                "anomalies": [
                    {
                        "timestamp": "2024-12-20T10:00:00+09:00",
                        "elapsed_time": 2.0,  # 5秒未満 = 短時間処理
                        "hour": 10,
                        "success": True,
                    },
                    {
                        "timestamp": "2024-12-20T11:00:00+09:00",
                        "elapsed_time": 150.0,  # 120秒以上 = 長時間処理
                        "hour": 11,
                        "success": True,
                    },
                ],
            },
        }

        html = generate_anomalies_section(anomalies, sample_performance_stats)

        assert "短時間処理" in html
        assert "長時間処理" in html

    def test_anomalies_section_with_zero_std_time(self):
        """std_time が 0 の場合 (lines 1165->1169, 1172->1176, 1184->1188, 1282->1286, 1289->1293, 1301->1305)"""
        from weather_display.metrics.webapi.page import generate_anomalies_section

        # std_time = 0 のパフォーマンス統計
        performance_stats = {
            "draw_panel": {"avg_time": 10.0, "std_time": 0},  # std_time = 0
            "display_image": {"avg_time": 15.0, "std_time": 0},  # std_time = 0
        }

        anomalies = {
            "draw_panel": {
                "anomalies_detected": 3,
                "anomaly_rate": 0.03,
                "anomalies": [
                    {
                        "timestamp": "2024-12-20T10:00:00+09:00",
                        "elapsed_time": 70.0,  # 長時間処理
                        "hour": 10,
                        "error_code": 0,
                    },
                    {
                        "timestamp": "2024-12-20T11:00:00+09:00",
                        "elapsed_time": 0.5,  # 短時間処理
                        "hour": 11,
                        "error_code": 0,
                    },
                    {
                        "timestamp": "2024-12-20T12:00:00+09:00",
                        "elapsed_time": 30.0,  # パターン異常
                        "hour": 12,
                        "error_code": 0,
                    },
                ],
            },
            "display_image": {
                "anomalies_detected": 3,
                "anomaly_rate": 0.03,
                "anomalies": [
                    {
                        "timestamp": "2024-12-20T10:00:00+09:00",
                        "elapsed_time": 130.0,  # 長時間処理 (>120)
                        "hour": 10,
                        "success": True,
                    },
                    {
                        "timestamp": "2024-12-20T11:00:00+09:00",
                        "elapsed_time": 3.0,  # 短時間処理 (<5)
                        "hour": 11,
                        "success": True,
                    },
                    {
                        "timestamp": "2024-12-20T12:00:00+09:00",
                        "elapsed_time": 30.0,  # パターン異常
                        "hour": 12,
                        "success": True,
                    },
                ],
            },
        }

        html = generate_anomalies_section(anomalies, performance_stats)

        # std_time = 0 でも正常に動作すること
        assert "anomaly-detection" in html
        assert "長時間処理" in html
        assert "短時間処理" in html

    def test_anomalies_section_with_invalid_timestamp_format(self):
        """不正なタイムスタンプ形式の場合 (lines 1218-1219, 1334-1336)"""
        from weather_display.metrics.webapi.page import generate_anomalies_section

        performance_stats = {
            "draw_panel": {"avg_time": 10.0, "std_time": 2.0},
            "display_image": {"avg_time": 15.0, "std_time": 3.0},
        }

        anomalies = {
            "draw_panel": {
                "anomalies_detected": 1,
                "anomaly_rate": 0.01,
                "anomalies": [
                    {
                        "timestamp": "invalid-timestamp-format",  # 不正な形式
                        "elapsed_time": 70.0,
                        "hour": 10,
                        "error_code": 0,
                    },
                ],
            },
            "display_image": {
                "anomalies_detected": 1,
                "anomaly_rate": 0.01,
                "anomalies": [
                    {
                        "timestamp": "also-invalid-format",  # 不正な形式
                        "elapsed_time": 130.0,
                        "hour": 10,
                        "success": True,
                    },
                ],
            },
        }

        html = generate_anomalies_section(anomalies, performance_stats)

        # 例外が発生しても正常に動作すること
        assert "anomaly-detection" in html
        # タイムスタンプがそのまま表示されること
        assert "invalid-timestamp-format" in html
        assert "also-invalid-format" in html

    def test_anomalies_section_display_image_with_unknown_timestamp(self):
        """display_image で不明なタイムスタンプの場合 (line 1334)"""
        from weather_display.metrics.webapi.page import generate_anomalies_section

        performance_stats = {
            "draw_panel": {"avg_time": 10.0, "std_time": 2.0},
            "display_image": {"avg_time": 15.0, "std_time": 3.0},
        }

        anomalies = {
            "draw_panel": {"anomalies_detected": 0, "anomaly_rate": 0},
            "display_image": {
                "anomalies_detected": 1,
                "anomaly_rate": 0.01,
                "anomalies": [
                    {
                        "timestamp": "不明",  # 不明なタイムスタンプ
                        "elapsed_time": 130.0,
                        "hour": 10,
                        "success": True,
                    },
                ],
            },
        }

        html = generate_anomalies_section(anomalies, performance_stats)

        # 不明なタイムスタンプが表示されること
        assert "不明" in html


class TestMetricsSkeletonGeneration:
    """generate_metrics_html_skeleton 関数のテスト"""

    def test_skeleton_contains_required_elements(self):
        """スケルトンに必要な要素が含まれること"""
        from weather_display.metrics.webapi.page import generate_metrics_html_skeleton

        html = generate_metrics_html_skeleton()

        assert "metricsApiUrl" in html
        assert "metricsApiBaseUrl" in html
        assert "progress-display" in html
        assert "metrics-content" in html


class TestStaticFilesEndpoint:
    """static_files エンドポイントのテスト"""

    def test_static_js_file_not_found(self, client):
        """存在しないJSファイルが404を返すこと"""
        response = client.get("/panel/static/nonexistent.js")

        assert response.status_code == 404

    def test_static_css_file_not_found(self, client):
        """存在しないCSSファイルが404を返すこと"""
        response = client.get("/panel/static/nonexistent.css")

        assert response.status_code == 404


class TestFaviconEndpoint:
    """favicon エンドポイントのテスト"""

    def test_favicon_returns_response(self, client):
        """favicon エンドポイントがレスポンスを返すこと"""
        response = client.get("/panel/favicon.png")

        # ファイルが存在する場合は200、存在しない場合は404
        assert response.status_code in [200, 404]
