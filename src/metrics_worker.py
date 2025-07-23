#!/usr/bin/env python3
"""
メトリクス記録用のワーカースレッド

Usage:
    このモジュールはインポートして使用します。
"""

import logging
import os
import queue
import threading
import time
from dataclasses import dataclass
from typing import Any, Dict, Optional

import influxdb_client
from influxdb_client.client.write_api import SYNCHRONOUS


@dataclass
class MetricsData:
    """メトリクスデータのコンテナ"""

    measurement: str
    tags: Dict[str, str]
    fields: Dict[str, Any]
    timestamp: Optional[int] = None


class MetricsWorker:
    """
    メトリクスをバックグラウンドで記録するワーカークラス

    メイン処理への影響を最小限にするため、別スレッドでInfluxDBへの書き込みを行います。
    """

    def __init__(self, db_config: Dict[str, Any], queue_size: int = 1000):
        """
        Args:
            db_config: InfluxDBの設定 (url, token, org, bucket)
            queue_size: キューの最大サイズ
        """
        self.db_config = db_config
        self.queue: queue.Queue[Optional[MetricsData]] = queue.Queue(maxsize=queue_size)
        self.worker_thread: Optional[threading.Thread] = None
        self.running = False
        self.client: Optional[influxdb_client.InfluxDBClient] = None
        self.write_api = None

    def start(self) -> None:
        """ワーカースレッドを開始"""
        if self.running:
            logging.warning("MetricsWorker is already running")
            return

        self.running = True
        self.worker_thread = threading.Thread(target=self._worker_loop, daemon=True)
        self.worker_thread.start()
        logging.info("MetricsWorker started")

    def stop(self, timeout: float = 5.0) -> None:
        """ワーカースレッドを停止"""
        if not self.running:
            return

        logging.info("Stopping MetricsWorker...")
        self.running = False

        # 終了シグナルをキューに送信
        try:
            self.queue.put(None, block=False)
        except queue.Full:
            logging.warning("Queue is full, force stopping")

        if self.worker_thread and self.worker_thread.is_alive():
            self.worker_thread.join(timeout=timeout)
            if self.worker_thread.is_alive():
                logging.error("MetricsWorker thread did not stop gracefully")

        logging.info("MetricsWorker stopped")

    def record(
        self, measurement: str, tags: Dict[str, str], fields: Dict[str, Any], timestamp: Optional[int] = None
    ) -> bool:
        """
        メトリクスを記録（キューに追加）

        Args:
            measurement: メジャー名
            tags: タグの辞書
            fields: フィールドの辞書
            timestamp: タイムスタンプ（Noneの場合は現在時刻）

        Returns:
            キューへの追加が成功したかどうか
        """
        if not self.running:
            logging.warning("MetricsWorker is not running")
            return False

        try:
            data = MetricsData(measurement, tags, fields, timestamp)
            self.queue.put(data, block=False)
            return True
        except queue.Full:
            logging.warning("Metrics queue is full, dropping data")
            return False

    def _worker_loop(self) -> None:
        """ワーカースレッドのメインループ"""
        try:
            self._init_client()

            while self.running:
                try:
                    # タイムアウト付きでキューから取得
                    data = self.queue.get(timeout=1.0)

                    if data is None:  # 終了シグナル
                        break

                    self._write_metrics(data)

                except queue.Empty:
                    continue
                except Exception:
                    logging.exception("Error in metrics worker loop")
                    time.sleep(1)  # エラー時は少し待機

        finally:
            self._cleanup()

    def _init_client(self) -> None:
        """InfluxDBクライアントを初期化"""
        try:
            self.client = influxdb_client.InfluxDBClient(
                url=self.db_config["url"], token=self.db_config["token"], org=self.db_config["org"]
            )
            self.write_api = self.client.write_api(write_options=SYNCHRONOUS)
            logging.info("InfluxDB client initialized")
        except Exception:
            logging.exception("Failed to initialize InfluxDB client")
            raise

    def _cleanup(self) -> None:
        """リソースをクリーンアップ"""
        # 残りのデータを書き込む
        remaining_count = 0
        while not self.queue.empty():
            try:
                data = self.queue.get_nowait()
                if data is not None:
                    self._write_metrics(data)
                    remaining_count += 1
            except queue.Empty:
                break
            except Exception:
                logging.exception("Error writing remaining metrics")

        if remaining_count > 0:
            logging.info("Wrote %d remaining metrics before shutdown", remaining_count)

        # クライアントをクローズ
        if self.write_api:
            try:
                self.write_api.close()
            except Exception:
                logging.exception("Error closing write API")

        if self.client:
            try:
                self.client.close()
            except Exception:
                logging.exception("Error closing InfluxDB client")

    def _write_metrics(self, data: MetricsData) -> None:
        """メトリクスをInfluxDBに書き込み"""
        if not self.write_api:
            logging.error("Write API is not initialized")
            return

        try:
            point = influxdb_client.Point(data.measurement)

            for key, value in data.tags.items():
                point.tag(key, value)

            for key, value in data.fields.items():
                point.field(key, value)

            if data.timestamp:
                point.time(data.timestamp)

            self.write_api.write(bucket=self.db_config["bucket"], record=point)

        except Exception:
            logging.exception("Failed to write metrics to InfluxDB")

    def get_queue_size(self) -> int:
        """現在のキューサイズを取得"""
        return self.queue.qsize()


# グローバルなワーカーインスタンス（シングルトン）
_worker_instance: Optional[MetricsWorker] = None
_worker_lock = threading.Lock()


def get_worker(db_config: Optional[Dict[str, Any]] = None) -> Optional[MetricsWorker]:
    """
    グローバルなワーカーインスタンスを取得

    マルチプロセス環境での使用に注意：
    - 各プロセスは独立したワーカーインスタンスを持ちます
    - プロセス終了時には必ずshutdown_worker()を呼び出してください

    Args:
        db_config: 初回呼び出し時に必要なInfluxDBの設定

    Returns:
        MetricsWorkerインスタンス（初期化に失敗した場合はNone）
    """
    global _worker_instance

    if _worker_instance is None and db_config is not None:
        with _worker_lock:
            # ダブルチェックロッキング
            if _worker_instance is None:
                try:
                    # プロセスIDをログに記録
                    pid = os.getpid()
                    logging.info("Creating MetricsWorker in process %d", pid)
                    _worker_instance = MetricsWorker(db_config)
                    _worker_instance.start()
                except Exception:
                    logging.exception("Failed to create MetricsWorker")
                    return None

    return _worker_instance


def shutdown_worker() -> None:
    """グローバルなワーカーをシャットダウン"""
    global _worker_instance

    with _worker_lock:
        if _worker_instance:
            pid = os.getpid()
            logging.info("Shutting down MetricsWorker in process %d", pid)
            _worker_instance.stop()
            _worker_instance = None
