#!/usr/bin/env python3
"""
Performance metrics collection and anomaly detection for weather panel system.

This module provides functionality to:
- Collect elapsed time metrics from create_image and display_image operations
- Store metrics in SQLite database
- Perform statistical analysis and anomaly detection
- Analyze relationships with time patterns
"""

import concurrent.futures
import datetime
import logging
import pathlib
import sqlite3
import zoneinfo
from contextlib import contextmanager
from typing import Any

import my_lib.sqlite_util
import numpy as np

_TIMEZONE = zoneinfo.ZoneInfo("Asia/Tokyo")
_DEFAULT_DB_PATH = pathlib.Path("data/metrics.db")
_DEFAULT_DAYS_LIMIT = 30  # デフォルトは過去30日間


def _get_cutoff_date(days_limit: int) -> str:
    """期間制限の基準日時を取得する。

    Args:
        days_limit: 過去何日分のデータを取得するか

    Returns:
        SQLite の datetime 比較に使える形式の日時文字列

    """
    cutoff = datetime.datetime.now(_TIMEZONE) - datetime.timedelta(days=days_limit)
    return cutoff.strftime("%Y-%m-%d %H:%M:%S")


def _calculate_boxplot_stats(arr: np.ndarray) -> dict[str, Any] | None:
    """numpy配列から箱ヒゲ図統計量を計算する。

    Args:
        arr: 数値データのnumpy配列

    Returns:
        統計量の辞書（min, q1, median, q3, max, outliers, count）
        データが空の場合はNone

    """
    if len(arr) == 0:
        return None

    q1, median, q3 = np.percentile(arr, [25, 50, 75])
    iqr = q3 - q1
    lower_bound = q1 - 1.5 * iqr
    upper_bound = q3 + 1.5 * iqr

    # 外れ値を抽出（最大20件に制限）
    outliers = arr[(arr < lower_bound) | (arr > upper_bound)]
    outliers_list = sorted(outliers)[:20]

    return {
        "min": float(np.min(arr)),
        "q1": float(q1),
        "median": float(median),
        "q3": float(q3),
        "max": float(np.max(arr)),
        "outliers": [float(x) for x in outliers_list],
        "count": len(arr),
    }


class MetricsCollector:
    """Collects and stores performance metrics for weather panel operations."""

    def __init__(self, db_path: str | pathlib.Path = _DEFAULT_DB_PATH):
        """Initialize MetricsCollector with database path."""
        self.db_path = pathlib.Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_database()

    def _init_database(self):
        """Initialize SQLite database with required tables."""
        # First time initialization: use my_lib.sqlite_util.connect for optimized settings
        with my_lib.sqlite_util.connect(self.db_path, timeout=30) as conn:
            cursor = conn.cursor()

            # Create table for draw_panel metrics
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS draw_panel_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME NOT NULL,
                    hour INTEGER NOT NULL,
                    day_of_week INTEGER NOT NULL,
                    total_elapsed_time REAL NOT NULL,
                    is_small_mode BOOLEAN NOT NULL,
                    is_test_mode BOOLEAN NOT NULL,
                    is_dummy_mode BOOLEAN NOT NULL,
                    error_code INTEGER DEFAULT 0,
                    panel_count INTEGER NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Create table for individual panel metrics
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS panel_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    draw_panel_id INTEGER NOT NULL,
                    panel_name TEXT NOT NULL,
                    elapsed_time REAL NOT NULL,
                    has_error BOOLEAN DEFAULT FALSE,
                    error_message TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (draw_panel_id) REFERENCES draw_panel_metrics (id)
                )
            """)

            # Create table for display_image metrics
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS display_image_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME NOT NULL,
                    hour INTEGER NOT NULL,
                    day_of_week INTEGER NOT NULL,
                    elapsed_time REAL NOT NULL,
                    is_small_mode BOOLEAN NOT NULL,
                    is_test_mode BOOLEAN NOT NULL,
                    is_one_time BOOLEAN NOT NULL,
                    rasp_hostname TEXT,
                    success BOOLEAN NOT NULL,
                    error_message TEXT,
                    sleep_time REAL,
                    diff_sec INTEGER,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Create indexes for better query performance
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_draw_panel_timestamp ON draw_panel_metrics (timestamp)"
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_display_image_timestamp ON display_image_metrics (timestamp)"
            )
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_draw_panel_hour ON draw_panel_metrics (hour)")
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_display_image_hour ON display_image_metrics (hour)"
            )

            conn.commit()

    @contextmanager
    def _get_connection(self):
        """Get database connection with proper error handling."""
        try:
            with my_lib.sqlite_util.connect(self.db_path, timeout=30) as conn:
                conn.row_factory = sqlite3.Row
                yield conn
        except Exception:
            logging.exception("Database error")
            raise

    def log_draw_panel_metrics(
        self,
        total_elapsed_time: float,
        panel_metrics: list[dict],
        is_small_mode: bool = False,
        is_test_mode: bool = False,
        is_dummy_mode: bool = False,
        error_code: int = 0,
        timestamp: datetime.datetime | None = None,
    ) -> int:
        """
        Log draw_panel operation metrics.

        Args:
            total_elapsed_time: Total time taken for draw_panel operation
            panel_metrics: List of dicts with panel metrics (name, elapsed_time, has_error, error_message)
            is_small_mode: Whether small mode was used
            is_test_mode: Whether test mode was used
            is_dummy_mode: Whether dummy mode was used
            error_code: Error code if any (0 = success)
            timestamp: When the operation occurred (default: now)

        Returns:
            ID of the inserted draw_panel_metrics record

        """
        if timestamp is None:
            timestamp = datetime.datetime.now(_TIMEZONE)

        hour = timestamp.hour
        day_of_week = timestamp.weekday()
        panel_count = len(panel_metrics)

        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                # Insert main metrics record
                cursor.execute(
                    """
                    INSERT INTO draw_panel_metrics
                    (timestamp, hour, day_of_week, total_elapsed_time, is_small_mode,
                     is_test_mode, is_dummy_mode, error_code, panel_count)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        timestamp,
                        hour,
                        day_of_week,
                        total_elapsed_time,
                        is_small_mode,
                        is_test_mode,
                        is_dummy_mode,
                        error_code,
                        panel_count,
                    ),
                )

                draw_panel_id = cursor.lastrowid

                # Insert individual panel metrics
                for panel in panel_metrics:
                    cursor.execute(
                        """
                        INSERT INTO panel_metrics
                        (draw_panel_id, panel_name, elapsed_time, has_error, error_message)
                        VALUES (?, ?, ?, ?, ?)
                    """,
                        (
                            draw_panel_id,
                            panel["name"],
                            panel["elapsed_time"],
                            panel.get("has_error", False),
                            panel.get("error_message"),
                        ),
                    )

                conn.commit()
                logging.debug(
                    "Logged draw_panel metrics: total=%.3fs, panels=%d", total_elapsed_time, panel_count
                )
                assert draw_panel_id is not None  # noqa: S101
                return draw_panel_id

        except Exception:
            logging.exception("Failed to log draw_panel metrics")
            return -1

    def log_display_image_metrics(
        self,
        elapsed_time: float,
        is_small_mode: bool = False,
        is_test_mode: bool = False,
        is_one_time: bool = False,
        rasp_hostname: str | None = None,
        success: bool = True,
        error_message: str | None = None,
        timestamp: datetime.datetime | None = None,
        sleep_time: float | None = None,
        diff_sec: int | None = None,
    ) -> int:
        """
        Log display_image operation metrics.

        Args:
            elapsed_time: Time taken for display_image operation
            is_small_mode: Whether small mode was used
            is_test_mode: Whether test mode was used
            is_one_time: Whether one-time mode was used
            rasp_hostname: Raspberry Pi hostname
            success: Whether the operation succeeded
            error_message: Error message if any
            timestamp: When the operation occurred (default: now)
            sleep_time: Sleep time after operation
            diff_sec: Timing difference in seconds

        Returns:
            ID of the inserted record

        """
        if timestamp is None:
            timestamp = datetime.datetime.now(_TIMEZONE)

        hour = timestamp.hour
        day_of_week = timestamp.weekday()

        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                cursor.execute(
                    """
                    INSERT INTO display_image_metrics
                    (timestamp, hour, day_of_week, elapsed_time, is_small_mode, is_test_mode,
                     is_one_time, rasp_hostname, success, error_message, sleep_time, diff_sec)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        timestamp,
                        hour,
                        day_of_week,
                        elapsed_time,
                        is_small_mode,
                        is_test_mode,
                        is_one_time,
                        rasp_hostname,
                        success,
                        error_message,
                        sleep_time,
                        diff_sec,
                    ),
                )

                conn.commit()
                logging.debug(
                    "Logged display_image metrics: elapsed=%.3fs, success=%s", elapsed_time, success
                )
                lastrowid = cursor.lastrowid
                assert lastrowid is not None  # noqa: S101
                return lastrowid

        except Exception:
            logging.exception("Failed to log display_image metrics")
            return -1


class MetricsAnalyzer:
    """Analyzes metrics data for patterns and anomalies."""

    def __init__(self, db_path: str | pathlib.Path = _DEFAULT_DB_PATH):
        """Initialize MetricsAnalyzer with database path."""
        self.db_path = pathlib.Path(db_path)
        if not self.db_path.exists():
            msg = f"Metrics database not found: {self.db_path}"
            raise FileNotFoundError(msg)

    @contextmanager
    def _get_connection(self):
        """Get database connection with proper error handling."""
        try:
            with my_lib.sqlite_util.connect(self.db_path, timeout=30) as conn:
                conn.row_factory = sqlite3.Row
                yield conn
        except Exception:
            logging.exception("Database error")
            raise

    def get_data_range(self) -> dict:
        """Get the actual data range available in the database."""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Get earliest and latest timestamps from both tables
            cursor.execute("""
                SELECT
                    MIN(timestamp) as earliest,
                    MAX(timestamp) as latest,
                    COUNT(*) as total_count
                FROM draw_panel_metrics
            """)
            draw_panel_result = cursor.fetchone()
            draw_panel_range = (
                dict(draw_panel_result)
                if draw_panel_result
                else {"earliest": None, "latest": None, "total_count": 0}
            )

            cursor.execute("""
                SELECT
                    MIN(timestamp) as earliest,
                    MAX(timestamp) as latest,
                    COUNT(*) as total_count
                FROM display_image_metrics
            """)
            display_image_result = cursor.fetchone()
            display_image_range = (
                dict(display_image_result)
                if display_image_result
                else {"earliest": None, "latest": None, "total_count": 0}
            )

            # Calculate overall range
            all_earliest = None
            all_latest = None

            if draw_panel_range["earliest"] and display_image_range["earliest"]:
                all_earliest = min(draw_panel_range["earliest"], display_image_range["earliest"])
            elif draw_panel_range["earliest"]:
                all_earliest = draw_panel_range["earliest"]
            elif display_image_range["earliest"]:
                all_earliest = display_image_range["earliest"]

            if draw_panel_range["latest"] and display_image_range["latest"]:
                all_latest = max(draw_panel_range["latest"], display_image_range["latest"])
            elif draw_panel_range["latest"]:
                all_latest = draw_panel_range["latest"]
            elif display_image_range["latest"]:
                all_latest = display_image_range["latest"]

            draw_count = draw_panel_range.get("total_count") or 0
            display_count = display_image_range.get("total_count") or 0

            return {
                "draw_panel": draw_panel_range,
                "display_image": display_image_range,
                "overall": {
                    "earliest": all_earliest,
                    "latest": all_latest,
                    "total_count": draw_count + display_count,
                },
            }

    def get_basic_statistics(self, days_limit: int | None = None) -> dict:
        """Get basic statistics for the specified period.

        Args:
            days_limit: 取得するデータの日数制限（Noneの場合はデフォルト値を使用）

        Returns:
            基本統計情報の辞書

        """
        if days_limit is None:
            days_limit = _DEFAULT_DAYS_LIMIT

        cutoff_date = _get_cutoff_date(days_limit)

        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Draw panel statistics
            cursor.execute(
                """
                SELECT
                    COUNT(*) as total_operations,
                    AVG(total_elapsed_time) as avg_elapsed_time,
                    MIN(total_elapsed_time) as min_elapsed_time,
                    MAX(total_elapsed_time) as max_elapsed_time,
                    SUM(CASE WHEN error_code > 0 THEN 1 ELSE 0 END) as error_count
                FROM draw_panel_metrics
                WHERE timestamp >= ?
            """,
                (cutoff_date,),
            )
            draw_panel_stats = dict(cursor.fetchone())

            # Display image statistics
            cursor.execute(
                """
                SELECT
                    COUNT(*) as total_operations,
                    AVG(elapsed_time) as avg_elapsed_time,
                    MIN(elapsed_time) as min_elapsed_time,
                    MAX(elapsed_time) as max_elapsed_time,
                    SUM(CASE WHEN success = 0 THEN 1 ELSE 0 END) as error_count
                FROM display_image_metrics
                WHERE timestamp >= ?
            """,
                (cutoff_date,),
            )
            display_image_stats = dict(cursor.fetchone())

            return {
                "draw_panel": draw_panel_stats,
                "display_image": display_image_stats,
            }

    def get_hourly_patterns(self, days_limit: int | None = None) -> dict:
        """Analyze performance patterns by hour of day.

        Args:
            days_limit: 取得するデータの日数制限（Noneの場合はデフォルト値を使用）

        Returns:
            時間別のパフォーマンスパターンデータ

        """
        if days_limit is None:
            days_limit = _DEFAULT_DAYS_LIMIT

        cutoff_date = _get_cutoff_date(days_limit)

        def fetch_draw_panel() -> tuple[list, list]:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT hour, COUNT(*) as count,
                           AVG(total_elapsed_time) as avg_elapsed_time,
                           MIN(total_elapsed_time) as min_elapsed_time,
                           MAX(total_elapsed_time) as max_elapsed_time,
                           SUM(CASE WHEN error_code > 0 THEN 1 ELSE 0 END) * 100.0 / COUNT(*) as error_rate
                    FROM draw_panel_metrics WHERE timestamp >= ? GROUP BY hour ORDER BY hour
                """,
                    (cutoff_date,),
                )
                hourly = [dict(row) for row in cursor.fetchall()]
                cursor.execute(
                    """SELECT hour, total_elapsed_time FROM draw_panel_metrics
                    WHERE timestamp >= ? ORDER BY hour""",
                    (cutoff_date,),
                )
                raw = cursor.fetchall()
                return hourly, raw

        def fetch_display_image() -> tuple[list, list]:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT hour, COUNT(*) as count, AVG(elapsed_time) as avg_elapsed_time,
                           MIN(elapsed_time) as min_elapsed_time, MAX(elapsed_time) as max_elapsed_time,
                           SUM(CASE WHEN success = 0 THEN 1 ELSE 0 END) * 100.0 / COUNT(*) as error_rate
                    FROM display_image_metrics WHERE timestamp >= ? GROUP BY hour ORDER BY hour
                """,
                    (cutoff_date,),
                )
                hourly = [dict(row) for row in cursor.fetchall()]
                cursor.execute(
                    "SELECT hour, elapsed_time FROM display_image_metrics WHERE timestamp >= ? ORDER BY hour",
                    (cutoff_date,),
                )
                raw = cursor.fetchall()
                return hourly, raw

        def fetch_diff_sec() -> tuple[list, list]:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT hour, COUNT(*) as count,
                           AVG(CAST(diff_sec AS REAL)) as avg_diff_sec,
                           MIN(CAST(diff_sec AS REAL)) as min_diff_sec,
                           MAX(CAST(diff_sec AS REAL)) as max_diff_sec
                    FROM display_image_metrics
                    WHERE timestamp >= ? AND diff_sec IS NOT NULL AND is_one_time = 0
                    GROUP BY hour ORDER BY hour
                """,
                    (cutoff_date,),
                )
                hourly = [dict(row) for row in cursor.fetchall()]
                cursor.execute(
                    """SELECT hour, CAST(diff_sec AS REAL) FROM display_image_metrics
                    WHERE timestamp >= ? AND diff_sec IS NOT NULL AND is_one_time = 0 ORDER BY hour""",
                    (cutoff_date,),
                )
                raw = cursor.fetchall()
                return hourly, raw

        # 並列でデータ取得
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            future_draw = executor.submit(fetch_draw_panel)
            future_display = executor.submit(fetch_display_image)
            future_diff = executor.submit(fetch_diff_sec)

            draw_panel_hourly, draw_panel_raw = future_draw.result()
            display_image_hourly, display_image_raw = future_display.result()
            diff_sec_hourly, diff_sec_raw = future_diff.result()

        # numpy配列に変換して統計量を計算
        draw_panel_boxplot = self._compute_hourly_boxplot_stats(draw_panel_raw)
        display_image_boxplot = self._compute_hourly_boxplot_stats(display_image_raw)
        diff_sec_boxplot = self._compute_hourly_boxplot_stats(diff_sec_raw)

        return {
            "draw_panel": draw_panel_hourly,
            "display_image": display_image_hourly,
            "diff_sec": diff_sec_hourly,
            "draw_panel_boxplot": draw_panel_boxplot,
            "display_image_boxplot": display_image_boxplot,
            "diff_sec_boxplot": diff_sec_boxplot,
        }

    def _compute_hourly_boxplot_stats(self, raw_data: list) -> dict:
        """生データから時間別のboxplot統計量を計算する。"""
        if not raw_data:
            return {}

        arr = np.array(raw_data)
        hours = arr[:, 0].astype(int)
        values = arr[:, 1].astype(float)

        boxplot_stats = {}
        for hour in range(24):
            mask = hours == hour
            if mask.any():
                stats = _calculate_boxplot_stats(values[mask])
                if stats:
                    boxplot_stats[hour] = stats

        return boxplot_stats

    def detect_anomalies(self, iqr_multiplier: float = 3.0, days_limit: int | None = None) -> dict:
        """
        Detect anomalies in performance metrics using IQR (Interquartile Range) method.

        処理時間が Q3 + k * IQR を超える値を異常として検出する。
        箱ひげ図の外れ値定義と統計的に一貫性がある手法。

        Args:
            iqr_multiplier: IQR に掛ける係数（デフォルト 3.0）。
                           1.5 で標準的な外れ値、3.0 でより厳格な異常検出。
            days_limit: 取得するデータの日数制限（Noneの場合はデフォルト値を使用）

        Returns:
            Dictionary with anomaly detection results including threshold info

        """
        if days_limit is None:
            days_limit = _DEFAULT_DAYS_LIMIT

        cutoff_date = _get_cutoff_date(days_limit)

        def fetch_and_analyze_draw_panel() -> dict | None:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """SELECT id, timestamp, hour, total_elapsed_time, error_code
                    FROM draw_panel_metrics WHERE timestamp >= ? ORDER BY timestamp""",
                    (cutoff_date,),
                )
                rows = cursor.fetchall()
                if len(rows) <= 10:
                    return None

                elapsed_times = np.array([row[3] for row in rows])
                q1 = float(np.percentile(elapsed_times, 25))
                q3 = float(np.percentile(elapsed_times, 75))
                iqr = q3 - q1
                threshold = q3 + iqr_multiplier * iqr

                anomalies = [
                    {
                        "id": row[0],
                        "timestamp": row[1],
                        "hour": row[2],
                        "elapsed_time": row[3],
                        "error_code": row[4],
                    }
                    for row in rows
                    if row[3] > threshold
                ]

                return {
                    "total_samples": len(rows),
                    "anomalies_detected": len(anomalies),
                    "anomaly_rate": len(anomalies) / len(rows),
                    "anomalies": anomalies,
                    "threshold": threshold,
                    "q1": q1,
                    "q3": q3,
                    "iqr": iqr,
                }

        def fetch_and_analyze_display_image() -> dict | None:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """SELECT id, timestamp, hour, elapsed_time, success
                    FROM display_image_metrics WHERE timestamp >= ? ORDER BY timestamp""",
                    (cutoff_date,),
                )
                rows = cursor.fetchall()
                if len(rows) <= 10:
                    return None

                elapsed_times = np.array([row[3] for row in rows])
                q1 = float(np.percentile(elapsed_times, 25))
                q3 = float(np.percentile(elapsed_times, 75))
                iqr = q3 - q1
                threshold = q3 + iqr_multiplier * iqr

                anomalies = [
                    {
                        "id": row[0],
                        "timestamp": row[1],
                        "hour": row[2],
                        "elapsed_time": row[3],
                        "success": row[4],
                    }
                    for row in rows
                    if row[3] > threshold
                ]

                return {
                    "total_samples": len(rows),
                    "anomalies_detected": len(anomalies),
                    "anomaly_rate": len(anomalies) / len(rows),
                    "anomalies": anomalies,
                    "threshold": threshold,
                    "q1": q1,
                    "q3": q3,
                    "iqr": iqr,
                }

        # データ取得と分析を並列実行（各関数内で完結）
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
            future_draw = executor.submit(fetch_and_analyze_draw_panel)
            future_display = executor.submit(fetch_and_analyze_display_image)
            draw_result = future_draw.result()
            display_result = future_display.result()

        results = {}
        if draw_result:
            results["draw_panel"] = draw_result
        if display_result:
            results["display_image"] = display_result

        return results

    def get_performance_trends(self, days_limit: int | None = None) -> dict:
        """Analyze performance trends over time.

        Args:
            days_limit: 取得するデータの日数制限（Noneの場合はデフォルト値を使用）

        Returns:
            日別のパフォーマンス推移データ

        """
        if days_limit is None:
            days_limit = _DEFAULT_DAYS_LIMIT

        cutoff_date = _get_cutoff_date(days_limit)

        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Daily trends for draw panel
            cursor.execute(
                """
                SELECT
                    DATE(timestamp) as date,
                    COUNT(*) as operations,
                    AVG(total_elapsed_time) as avg_elapsed_time,
                    SUM(CASE WHEN error_code > 0 THEN 1 ELSE 0 END) * 100.0 / COUNT(*) as error_rate
                FROM draw_panel_metrics
                WHERE timestamp >= ?
                GROUP BY DATE(timestamp)
                ORDER BY date
            """,
                (cutoff_date,),
            )
            draw_panel_trends = [dict(row) for row in cursor.fetchall()]

            # Daily trends for display image
            cursor.execute(
                """
                SELECT
                    DATE(timestamp) as date,
                    COUNT(*) as operations,
                    AVG(elapsed_time) as avg_elapsed_time,
                    SUM(CASE WHEN success = 0 THEN 1 ELSE 0 END) * 100.0 / COUNT(*) as error_rate
                FROM display_image_metrics
                WHERE timestamp >= ?
                GROUP BY DATE(timestamp)
                ORDER BY date
            """,
                (cutoff_date,),
            )
            display_image_trends = [dict(row) for row in cursor.fetchall()]

            # Get raw elapsed times for boxplot by day
            cursor.execute(
                """
                SELECT DATE(timestamp) as date, total_elapsed_time
                FROM draw_panel_metrics
                WHERE timestamp >= ?
                ORDER BY date
            """,
                (cutoff_date,),
            )
            draw_panel_raw = cursor.fetchall()

            cursor.execute(
                """
                SELECT DATE(timestamp) as date, elapsed_time
                FROM display_image_metrics
                WHERE timestamp >= ?
                ORDER BY date
            """,
                (cutoff_date,),
            )
            display_image_raw = cursor.fetchall()

            # Get raw diff_sec data for boxplot by day
            cursor.execute(
                """
                SELECT DATE(timestamp) as date, CAST(diff_sec AS REAL)
                FROM display_image_metrics
                WHERE timestamp >= ? AND diff_sec IS NOT NULL AND is_one_time = 0
                ORDER BY date
            """,
                (cutoff_date,),
            )
            diff_sec_raw = cursor.fetchall()

            # numpy配列を使って日別のboxplot統計量を計算
            draw_panel_boxplot_list = self._compute_daily_boxplot_stats(draw_panel_raw, "elapsed_times")
            display_image_boxplot_list = self._compute_daily_boxplot_stats(display_image_raw, "elapsed_times")
            diff_sec_boxplot_list = self._compute_daily_boxplot_stats(diff_sec_raw, "diff_secs")

            return {
                "draw_panel": draw_panel_trends,
                "display_image": display_image_trends,
                "draw_panel_boxplot": draw_panel_boxplot_list,
                "display_image_boxplot": display_image_boxplot_list,
                "diff_sec_boxplot": diff_sec_boxplot_list,
            }

    def _compute_daily_boxplot_stats(self, raw_data: list, value_key: str) -> list:
        """生データから日別のboxplot統計量を計算する。"""
        if not raw_data:
            return []

        # 日付ごとにグループ化
        daily_data: dict[str, list] = {}
        for row in raw_data:
            date = row[0]
            if date not in daily_data:
                daily_data[date] = []
            daily_data[date].append(row[1])

        # 統計量を計算
        result = []
        for date in sorted(daily_data.keys()):
            arr = np.array(daily_data[date])
            stats = _calculate_boxplot_stats(arr)
            if stats:
                result.append({"date": date, "stats": stats})

        return result

    def check_performance_alerts(self, thresholds: dict | None = None) -> list[dict]:
        """
        Check for performance alerts based on thresholds.

        Args:
            thresholds: Custom thresholds (default: reasonable values)

        Returns:
            List of alert dictionaries

        """
        if thresholds is None:
            thresholds = {
                "draw_panel_max_time": 60.0,  # seconds
                "display_image_max_time": 120.0,  # seconds
                "error_rate_threshold": 10.0,  # percent
                "recent_hours": 24,  # hours to check
            }

        alerts = []
        since = datetime.datetime.now(_TIMEZONE) - datetime.timedelta(hours=thresholds["recent_hours"])

        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Check for slow draw_panel operations
            cursor.execute(
                """
                SELECT COUNT(*) as slow_count, MAX(total_elapsed_time) as max_time
                FROM draw_panel_metrics
                WHERE timestamp >= ? AND total_elapsed_time > ?
            """,
                (since, thresholds["draw_panel_max_time"]),
            )
            row = cursor.fetchone()
            if row["slow_count"] > 0:
                alerts.append(
                    {
                        "type": "slow_draw_panel",
                        "message": (
                            f"Found {row['slow_count']} slow draw_panel operations "
                            f"(max: {row['max_time']:.1f}s)"
                        ),
                        "severity": "warning",
                    }
                )

            # Check for slow display_image operations
            cursor.execute(
                """
                SELECT COUNT(*) as slow_count, MAX(elapsed_time) as max_time
                FROM display_image_metrics
                WHERE timestamp >= ? AND elapsed_time > ?
            """,
                (since, thresholds["display_image_max_time"]),
            )
            row = cursor.fetchone()
            if row["slow_count"] > 0:
                alerts.append(
                    {
                        "type": "slow_display_image",
                        "message": (
                            f"Found {row['slow_count']} slow display_image operations "
                            f"(max: {row['max_time']:.1f}s)"
                        ),
                        "severity": "warning",
                    }
                )

            # Check error rates
            cursor.execute(
                """
                SELECT
                    SUM(CASE WHEN error_code > 0 THEN 1 ELSE 0 END) * 100.0 / COUNT(*) as error_rate
                FROM draw_panel_metrics
                WHERE timestamp >= ?
            """,
                (since,),
            )
            row = cursor.fetchone()
            if row["error_rate"] and row["error_rate"] > thresholds["error_rate_threshold"]:
                alerts.append(
                    {
                        "type": "high_draw_panel_error_rate",
                        "message": f"High draw_panel error rate: {row['error_rate']:.1f}%",
                        "severity": "critical",
                    }
                )

            cursor.execute(
                """
                SELECT
                    SUM(CASE WHEN success = 0 THEN 1 ELSE 0 END) * 100.0 / COUNT(*) as error_rate
                FROM display_image_metrics
                WHERE timestamp >= ?
            """,
                (since,),
            )
            row = cursor.fetchone()
            if row["error_rate"] and row["error_rate"] > thresholds["error_rate_threshold"]:
                alerts.append(
                    {
                        "type": "high_display_image_error_rate",
                        "message": f"High display_image error rate: {row['error_rate']:.1f}%",
                        "severity": "critical",
                    }
                )

        return alerts

    def get_panel_performance_trends(self, days_limit: int | None = None) -> dict:
        """パネル別の処理時間統計量を取得する。

        Args:
            days_limit: 取得するデータの日数制限（Noneの場合はデフォルト値を使用）

        Returns:
            パネル名をキーとした統計量の辞書

        """
        if days_limit is None:
            days_limit = _DEFAULT_DAYS_LIMIT

        cutoff_date = _get_cutoff_date(days_limit)

        with self._get_connection() as conn:
            cursor = conn.cursor()

            # パネル別の処理時間データを取得
            cursor.execute(
                """
                SELECT
                    pm.panel_name,
                    pm.elapsed_time
                FROM panel_metrics pm
                JOIN draw_panel_metrics dpm ON pm.draw_panel_id = dpm.id
                WHERE dpm.timestamp >= ?
                ORDER BY pm.panel_name
            """,
                (cutoff_date,),
            )
            panel_data = cursor.fetchall()

            # パネル名ごとにグループ化して統計量を計算
            panel_groups: dict[str, list] = {}
            for row in panel_data:
                panel_name = row[0]
                elapsed_time = row[1]

                if panel_name not in panel_groups:
                    panel_groups[panel_name] = []
                panel_groups[panel_name].append(elapsed_time)

            # 統計量を計算
            panel_stats = {}
            for panel_name, values in panel_groups.items():
                arr = np.array(values)
                stats = _calculate_boxplot_stats(arr)
                if stats:
                    panel_stats[panel_name] = stats

            return panel_stats

    def get_panel_daily_trends(self, days_limit: int | None = None) -> dict:
        """パネル別の日別処理時間推移を取得する。

        Args:
            days_limit: 取得するデータの日数制限（Noneの場合はデフォルト値を使用）

        Returns:
            パネル名をキーとした日別boxplot統計量のリストの辞書

        """
        if days_limit is None:
            days_limit = _DEFAULT_DAYS_LIMIT

        cutoff_date = _get_cutoff_date(days_limit)

        with self._get_connection() as conn:
            cursor = conn.cursor()

            # パネル別の処理時間データを日付とともに取得
            cursor.execute(
                """
                SELECT
                    pm.panel_name,
                    DATE(dpm.timestamp) as date,
                    pm.elapsed_time
                FROM panel_metrics pm
                JOIN draw_panel_metrics dpm ON pm.draw_panel_id = dpm.id
                WHERE dpm.timestamp >= ?
                ORDER BY pm.panel_name, date
            """,
                (cutoff_date,),
            )
            panel_data = cursor.fetchall()

            # パネル名と日付ごとにグループ化
            panel_daily_groups: dict[str, dict[str, list]] = {}
            for row in panel_data:
                panel_name = row[0]
                date = row[1]
                elapsed_time = row[2]

                if panel_name not in panel_daily_groups:
                    panel_daily_groups[panel_name] = {}
                if date not in panel_daily_groups[panel_name]:
                    panel_daily_groups[panel_name][date] = []
                panel_daily_groups[panel_name][date].append(elapsed_time)

            # パネルごとに日別の統計量を計算
            panel_daily_trends = {}
            for panel_name, daily_data in panel_daily_groups.items():
                daily_stats = []
                for date in sorted(daily_data.keys()):
                    arr = np.array(daily_data[date])
                    stats = _calculate_boxplot_stats(arr)
                    if stats:
                        daily_stats.append({"date": date, "stats": stats})
                if daily_stats:
                    panel_daily_trends[panel_name] = daily_stats

            return panel_daily_trends

    def get_performance_statistics(self, days_limit: int | None = None) -> dict:
        """パフォーマンス統計情報を取得する（異常検知詳細用）。

        Args:
            days_limit: 取得するデータの日数制限（Noneの場合はデフォルト値を使用）

        Returns:
            統計情報の辞書

        """
        if days_limit is None:
            days_limit = _DEFAULT_DAYS_LIMIT

        cutoff_date = _get_cutoff_date(days_limit)

        with self._get_connection() as conn:
            cursor = conn.cursor()

            # 画像生成処理の統計
            cursor.execute(
                """
                SELECT
                    AVG(total_elapsed_time) as avg_time,
                    COUNT(*) as count,
                    MIN(total_elapsed_time) as min_time,
                    MAX(total_elapsed_time) as max_time
                FROM draw_panel_metrics
                WHERE timestamp >= ?
            """,
                (cutoff_date,),
            )
            draw_panel_stats = dict(cursor.fetchone())

            # 標準偏差を計算（SQLiteにはSTDDEV関数がないため、numpy使用）
            cursor.execute(
                """
                SELECT total_elapsed_time
                FROM draw_panel_metrics
                WHERE timestamp >= ?
            """,
                (cutoff_date,),
            )
            draw_panel_times = np.array([row[0] for row in cursor.fetchall()])

            if len(draw_panel_times) > 1:
                draw_panel_stats["std_time"] = float(np.std(draw_panel_times, ddof=1))
            else:
                draw_panel_stats["std_time"] = 0

            # 表示実行処理の統計
            cursor.execute(
                """
                SELECT
                    AVG(elapsed_time) as avg_time,
                    COUNT(*) as count,
                    MIN(elapsed_time) as min_time,
                    MAX(elapsed_time) as max_time
                FROM display_image_metrics
                WHERE timestamp >= ?
            """,
                (cutoff_date,),
            )
            display_image_stats = dict(cursor.fetchone())

            cursor.execute(
                """
                SELECT elapsed_time
                FROM display_image_metrics
                WHERE timestamp >= ?
            """,
                (cutoff_date,),
            )
            display_image_times = np.array([row[0] for row in cursor.fetchall()])

            if len(display_image_times) > 1:
                display_image_stats["std_time"] = float(np.std(display_image_times, ddof=1))
            else:
                display_image_stats["std_time"] = 0

            return {"draw_panel": draw_panel_stats, "display_image": display_image_stats}


def collect_draw_panel_metrics(*args, db_path: str | pathlib.Path | None = None, **kwargs) -> int:
    """Collect draw_panel metrics with convenience wrapper.

    Args:
        db_path: データベースパス。None の場合はメトリクス収集をスキップ。

    Returns:
        レコードID。db_path が None の場合は -1 を返す。

    """
    if db_path is None:
        return -1  # メトリクス収集をスキップ

    collector = MetricsCollector(db_path)
    return collector.log_draw_panel_metrics(*args, **kwargs)


def collect_display_image_metrics(*args, db_path: str | pathlib.Path | None = None, **kwargs) -> int:
    """Collect display_image metrics with convenience wrapper.

    Args:
        db_path: データベースパス。None の場合はメトリクス収集をスキップ。

    Returns:
        レコードID。db_path が None の場合は -1 を返す。

    """
    if db_path is None:
        return -1  # メトリクス収集をスキップ

    collector = MetricsCollector(db_path)
    return collector.log_display_image_metrics(*args, **kwargs)
