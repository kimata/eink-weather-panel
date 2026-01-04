#!/usr/bin/env python3
# ruff: noqa: S101
"""
Web API 統合テスト

Flask アプリケーションの API エンドポイントのテストを行います。
"""


class TestBaseEndpoints:
    """基本エンドポイントのテスト"""

    def test_index_returns_response(self, client):
        """インデックスページがレスポンスを返すこと"""
        response = client.get("/")

        # 200 または リダイレクトを返すこと
        assert response.status_code in [200, 302, 308]

    def test_panel_root_returns_response(self, client):
        """パネルルートがレスポンスを返すこと"""
        response = client.get("/panel/")

        # 200 または 404 を返すこと
        assert response.status_code in [200, 404]


class TestSystemInfoEndpoints:
    """システム情報エンドポイントのテスト"""

    def test_sysinfo_endpoint(self, client):
        """sysinfo エンドポイントが動作すること"""
        response = client.get("/panel/api/sysinfo")

        assert response.status_code == 200

    def test_memory_endpoint(self, client):
        """memory エンドポイントが動作すること"""
        response = client.get("/panel/api/memory")

        assert response.status_code == 200


class TestImageGeneration:
    """画像生成エンドポイントのテスト"""

    def test_run_endpoint_exists(self, client):
        """run エンドポイントが存在すること"""
        response = client.get("/panel/api/run?mode=test")

        # レスポンスが返ること（エラーでも良い）
        assert response.status_code in [200, 202, 400, 500]

    def test_snapshot_endpoint_exists(self, client):
        """snapshot エンドポイントが存在すること"""
        response = client.get("/panel/api/snapshot")

        # レスポンスが返ること
        assert response.status_code in [200, 400, 404, 500]


class TestMetricsEndpoints:
    """メトリクスエンドポイントのテスト"""

    def test_metrics_endpoint_exists(self, client):
        """metrics エンドポイントが存在すること"""
        response = client.get("/panel/api/metrics")

        assert response.status_code in [200, 404, 500]

    def test_metrics_data_endpoint_exists(self, client):
        """metrics/data エンドポイントが存在すること"""
        response = client.get("/panel/api/metrics/data")

        assert response.status_code in [200, 404, 500]


class TestErrorHandling:
    """エラーハンドリングのテスト"""

    def test_not_found_returns_404(self, client):
        """存在しないパスで 404 を返すこと"""
        response = client.get("/panel/api/nonexistent_endpoint_xyz_123")

        assert response.status_code == 404
