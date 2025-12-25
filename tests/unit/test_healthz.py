#!/usr/bin/env python3
# ruff: noqa: S101
"""
healthz.py のユニットテスト
"""
import pytest


class TestCheckLiveness:
    """check_liveness 関数のテスト"""

    def test_check_liveness_returns_true_when_no_failures(self, mocker):
        """すべてのターゲットが正常な場合に True を返すこと"""
        import healthz

        mocker.patch("my_lib.healthz.check_liveness_all", return_value=[])

        result = healthz.check_liveness([])

        assert result is True

    def test_check_liveness_returns_false_when_failures_exist(self, mocker):
        """失敗したターゲットがある場合に False を返すこと"""
        import healthz

        mocker.patch("my_lib.healthz.check_liveness_all", return_value=["target1"])

        result = healthz.check_liveness([])

        assert result is False

    def test_check_liveness_with_single_target(self, mocker):
        """単一ターゲットで正常にチェックできること"""
        from my_lib.healthz import HealthzTarget

        import healthz

        mock_check = mocker.patch("my_lib.healthz.check_liveness_all", return_value=[])

        target = HealthzTarget(name="test", liveness_file="/tmp/test", interval=60)
        result = healthz.check_liveness([target])

        assert result is True
        mock_check.assert_called_once_with([target])

    def test_check_liveness_with_multiple_targets(self, mocker):
        """複数ターゲットで正常にチェックできること"""
        from my_lib.healthz import HealthzTarget

        import healthz

        mock_check = mocker.patch("my_lib.healthz.check_liveness_all", return_value=[])

        targets = [
            HealthzTarget(name="target1", liveness_file="/tmp/test1", interval=60),
            HealthzTarget(name="target2", liveness_file="/tmp/test2", interval=120),
        ]
        result = healthz.check_liveness(targets)

        assert result is True
        mock_check.assert_called_once_with(targets)
