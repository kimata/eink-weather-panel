#!/usr/bin/env python3
# ruff: noqa: S101
"""
healthz.py のユニットテスト

NOTE: Liveness チェック機能は my_lib.healthz で提供されるため、
      そのテストは my_lib で行われます。
      ここでは healthz モジュールのインポート確認のみを行います。
"""


class TestHealthzModule:
    """healthz モジュールのテスト"""

    def test_module_import(self):
        """healthz モジュールがインポートできること"""
        import healthz  # noqa: F401

    def test_has_schema_config(self):
        """SCHEMA_CONFIG が定義されていること"""
        import healthz

        assert hasattr(healthz, "SCHEMA_CONFIG")
        assert healthz.SCHEMA_CONFIG == "schema/config.schema"
