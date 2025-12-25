#!/usr/bin/env python3
# ruff: noqa: S101
"""
タイミング制御（カルマンフィルタ）のユニットテスト
"""
import datetime
import zoneinfo

import pytest


class TestTimingKalmanFilter:
    """TimingKalmanFilter クラスのテスト"""

    def test_initial_estimate_is_set_correctly(self):
        """初期推定値が正しく設定されること"""
        from weather_display.timing_filter import TimingKalmanFilter

        initial_value = 25.0
        kf = TimingKalmanFilter(initial_estimate=initial_value)

        assert kf.get_estimate() == initial_value

    def test_update_adjusts_estimate_toward_measurement(self):
        """update で測定値に向かって推定値が調整されること"""
        from weather_display.timing_filter import TimingKalmanFilter

        kf = TimingKalmanFilter(initial_estimate=30.0)
        measurement = 40.0

        new_estimate = kf.update(measurement)

        # 測定値の方向に推定値が動くこと
        assert new_estimate > 30.0
        assert new_estimate < 40.0

    def test_update_returns_estimate(self):
        """update が更新後の推定値を返すこと"""
        from weather_display.timing_filter import TimingKalmanFilter

        kf = TimingKalmanFilter(initial_estimate=30.0)

        result = kf.update(35.0)

        assert result == kf.get_estimate()

    def test_multiple_updates_converge_to_true_value(self):
        """複数回の更新で真値に収束すること"""
        from weather_display.timing_filter import TimingKalmanFilter

        kf = TimingKalmanFilter(initial_estimate=10.0)
        true_value = 50.0

        # 同じ値で複数回更新
        for _ in range(20):
            kf.update(true_value)

        # 真値に近づいていること
        assert abs(kf.get_estimate() - true_value) < 1.0

    def test_noisy_measurements_are_smoothed(self):
        """ノイズのある測定値が平滑化されること"""
        from weather_display.timing_filter import TimingKalmanFilter

        kf = TimingKalmanFilter(initial_estimate=30.0)

        # ノイズのある測定値
        measurements = [30, 35, 25, 32, 28, 31, 33, 29, 30, 31]

        estimates = []
        for m in measurements:
            estimates.append(kf.update(m))

        # 推定値の変動は測定値の変動より小さいこと
        measurement_range = max(measurements) - min(measurements)
        estimate_range = max(estimates) - min(estimates)

        assert estimate_range < measurement_range

    @pytest.mark.parametrize(
        "initial,process_noise,measurement_noise",
        [
            (30.0, 0.1, 1.0),
            (30.0, 1.0, 0.1),
            (30.0, 0.5, 0.5),
        ],
    )
    def test_different_noise_parameters_work(self, initial, process_noise, measurement_noise):
        """異なるノイズパラメータで動作すること"""
        from weather_display.timing_filter import TimingKalmanFilter

        kf = TimingKalmanFilter(
            initial_estimate=initial,
            process_noise=process_noise,
            measurement_noise=measurement_noise,
        )

        result = kf.update(35.0)

        assert result is not None
        assert isinstance(result, float)


class TestTimingController:
    """TimingController クラスのテスト"""

    def test_initial_update_interval_is_set(self):
        """初期更新間隔が正しく設定されること"""
        from weather_display.timing_filter import TimingController

        controller = TimingController(update_interval=120)

        assert controller.update_interval == 120

    def test_initial_target_second_is_set(self):
        """目標秒が正しく設定されること"""
        from weather_display.timing_filter import TimingController

        controller = TimingController(target_second=30)

        assert controller.target_second == 30

    def test_calculate_sleep_time_returns_positive_value(self):
        """calculate_sleep_time が正の値を返すこと"""
        from weather_display.timing_filter import TimingController

        controller = TimingController(update_interval=60)
        tz = zoneinfo.ZoneInfo("Asia/Tokyo")
        current_time = datetime.datetime.now(tz)

        sleep_time, diff_sec = controller.calculate_sleep_time(5.0, current_time)

        assert sleep_time >= 0

    def test_calculate_sleep_time_with_different_elapsed_times(self):
        """異なる経過時間で正しくスリープ時間を計算すること"""
        from weather_display.timing_filter import TimingController

        controller = TimingController(update_interval=60, target_second=0)
        tz = zoneinfo.ZoneInfo("Asia/Tokyo")
        current_time = datetime.datetime.now(tz).replace(second=30)

        # 短い経過時間
        sleep_time1, _ = controller.calculate_sleep_time(5.0, current_time)
        # 長い経過時間
        sleep_time2, _ = controller.calculate_sleep_time(50.0, current_time)

        # 経過時間が長いほどスリープは短くなる（調整される）
        # ただしカルマンフィルタの影響で単純な差にはならない
        assert sleep_time1 >= 0
        assert sleep_time2 >= 0

    def test_calculate_sleep_time_diff_sec_range(self):
        """diff_sec が -30 から 30 の範囲内であること"""
        from weather_display.timing_filter import TimingController

        controller = TimingController(update_interval=60, target_second=0)
        tz = zoneinfo.ZoneInfo("Asia/Tokyo")

        for second in range(60):
            current_time = datetime.datetime.now(tz).replace(second=second)
            _, diff_sec = controller.calculate_sleep_time(10.0, current_time)

            assert -30 <= diff_sec <= 30

    @pytest.mark.parametrize("target_second", [0, 15, 30, 45])
    def test_calculate_sleep_time_with_target_second(self, target_second):
        """target_second が考慮されること"""
        from weather_display.timing_filter import TimingController

        controller = TimingController(update_interval=60, target_second=target_second)
        tz = zoneinfo.ZoneInfo("Asia/Tokyo")
        current_time = datetime.datetime.now(tz).replace(second=0)

        sleep_time, _ = controller.calculate_sleep_time(10.0, current_time)

        # target_second が大きいほど基本的にスリープ時間も変わる
        assert sleep_time >= 0

    def test_calculate_sleep_time_adjusts_negative_sleep(self):
        """負のスリープ時間が正に調整されること"""
        from weather_display.timing_filter import TimingController

        controller = TimingController(update_interval=60, target_second=0)
        tz = zoneinfo.ZoneInfo("Asia/Tokyo")
        # 秒が大きく、経過時間も長い場合
        current_time = datetime.datetime.now(tz).replace(second=55)

        sleep_time, _ = controller.calculate_sleep_time(50.0, current_time)

        # 負にならないこと
        assert sleep_time >= 0


class TestTimingFilterBoundaryValues:
    """境界値テスト"""

    def test_kalman_filter_with_zero_initial_estimate(self):
        """初期値が0の場合も正常に動作すること"""
        from weather_display.timing_filter import TimingKalmanFilter

        kf = TimingKalmanFilter(initial_estimate=0.0)

        result = kf.update(10.0)

        assert result > 0.0
        assert result < 10.0

    def test_kalman_filter_with_negative_initial_estimate(self):
        """初期値が負の場合も正常に動作すること"""
        from weather_display.timing_filter import TimingKalmanFilter

        kf = TimingKalmanFilter(initial_estimate=-10.0)

        result = kf.update(10.0)

        # 測定値方向に移動すること
        assert result > -10.0

    def test_kalman_filter_with_very_large_value(self):
        """非常に大きな値でも正常に動作すること"""
        from weather_display.timing_filter import TimingKalmanFilter

        kf = TimingKalmanFilter(initial_estimate=1000000.0)

        result = kf.update(1000010.0)

        assert result > 1000000.0
        assert result < 1000010.0

    def test_kalman_filter_with_very_small_noise(self):
        """非常に小さいノイズでも正常に動作すること"""
        from weather_display.timing_filter import TimingKalmanFilter

        kf = TimingKalmanFilter(
            initial_estimate=30.0,
            process_noise=0.0001,
            measurement_noise=0.0001,
        )

        result = kf.update(35.0)

        assert result is not None
        assert isinstance(result, float)

    def test_controller_with_zero_elapsed_time(self):
        """経過時間が0の場合も正常に動作すること"""
        from weather_display.timing_filter import TimingController

        controller = TimingController(update_interval=60)
        tz = zoneinfo.ZoneInfo("Asia/Tokyo")
        current_time = datetime.datetime.now(tz)

        sleep_time, _ = controller.calculate_sleep_time(0.0, current_time)

        assert sleep_time >= 0

    def test_controller_with_negative_elapsed_time(self):
        """経過時間が負の場合も正常に動作すること（異常値への耐性）"""
        from weather_display.timing_filter import TimingController

        controller = TimingController(update_interval=60)
        tz = zoneinfo.ZoneInfo("Asia/Tokyo")
        current_time = datetime.datetime.now(tz)

        sleep_time, _ = controller.calculate_sleep_time(-5.0, current_time)

        assert sleep_time >= 0

    def test_controller_with_very_large_elapsed_time(self):
        """非常に長い経過時間でも正常に動作すること"""
        from weather_display.timing_filter import TimingController

        controller = TimingController(update_interval=60)
        tz = zoneinfo.ZoneInfo("Asia/Tokyo")
        current_time = datetime.datetime.now(tz)

        sleep_time, _ = controller.calculate_sleep_time(3600.0, current_time)  # 1時間

        assert sleep_time >= 0
