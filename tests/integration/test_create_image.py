#!/usr/bin/env python3
# ruff: noqa: S101
"""
create_image.py 統合テスト

画像生成の統合テストを行います。
"""


class TestCreateImage:
    """create_image 関数の統合テスト"""

    def test_create_image_test_mode(self, config):
        """テストモードで白画像を生成できること"""
        from create_image import create_image

        img, status = create_image(config, test_mode=True)

        assert img is not None
        assert status == 0
        assert img.size == (config.panel.device.width, config.panel.device.height)

    def test_create_image_normal_mode(self, config, image_checker, mock_sensor_fetch_data):
        """通常モードで画像を生成できること"""
        from create_image import create_image

        mock_sensor_fetch_data()

        img, status = create_image(config, small_mode=False)

        assert img is not None
        assert img.size == (config.panel.device.width, config.panel.device.height)
        image_checker.save(img)

    def test_create_image_small_mode(self, config_small, image_checker, mock_sensor_fetch_data):
        """小型ディスプレイモードで画像を生成できること"""
        from create_image import create_image

        mock_sensor_fetch_data()

        img, status = create_image(config_small, small_mode=True)

        assert img is not None
        assert img.size == (config_small.panel.device.width, config_small.panel.device.height)
        image_checker.save(img)


class TestDrawWall:
    """draw_wall 関数のテスト"""

    def test_draw_wall_applies_background(self, config):
        """背景画像を適用できること"""
        import PIL.Image

        from create_image import draw_wall

        img = PIL.Image.new(
            "RGBA",
            (config.panel.device.width, config.panel.device.height),
            (255, 255, 255, 255),
        )

        # draw_wall がエラーなく実行されること
        draw_wall(config, img)

        assert img is not None


class TestErrorHandling:
    """エラーハンドリングのテスト"""

    def test_create_image_handles_exception(self, config, mocker, slack_checker):
        """例外発生時にエラー画像を生成すること"""
        from create_image import ERROR_CODE_MAJOR, create_image

        # draw_panel で例外を発生させる
        mocker.patch(
            "create_image.draw_panel",
            side_effect=Exception("Test exception"),
        )

        img, status = create_image(config)

        # エラーコードを返すこと
        assert status == ERROR_CODE_MAJOR

        # 画像は生成されていること
        assert img is not None

    def test_create_image_metrics_log_failure(self, config, mocker, mock_sensor_fetch_data, caplog):
        """メトリクスログ失敗時も処理を継続すること (lines 148-149)"""
        import logging

        mock_sensor_fetch_data()

        # Note: test_mode=False にして draw_panel を実行し、
        # そこで metrics logging の例外をテストする
        mocker.patch(
            "weather_display.metrics.collector.collect_draw_panel_metrics",
            side_effect=Exception("Metrics log failed"),
        )

        from create_image import create_image

        with caplog.at_level(logging.WARNING):
            img, status = create_image(config, test_mode=False)

        # 例外が発生してもエラーにならず処理が完了すること
        assert img is not None

        # 警告メッセージが記録されていること
        assert any("Failed to log draw_panel metrics" in record.message for record in caplog.records)

    def test_create_image_with_dummy_mode(self, config, mocker, mock_sensor_fetch_data):
        """ダミーモードで画像が生成されること"""
        import os

        mock_sensor_fetch_data()

        from create_image import create_image

        img, status = create_image(config, dummy_mode=True, test_mode=True)

        # ダミーモードでも画像が生成されること
        assert img is not None
        assert status == 0

        # 環境変数が設定されていること
        assert os.environ.get("DUMMY_MODE") == "true"

    def test_create_image_panel_error_notification(self, config, mocker, mock_sensor_fetch_data):
        """パネル生成エラー時にSlack通知が呼ばれること (lines 114-119)"""
        import my_lib.panel_util
        import PIL.Image

        mock_sensor_fetch_data()

        # multiprocessing.Pool をモックして、エラータプルを返すようにする
        mock_img = PIL.Image.new("RGBA", (100, 100), (255, 255, 255, 255))
        mock_task = mocker.MagicMock()
        # 3要素タプル = エラーあり
        mock_task.get.return_value = (mock_img, 1.0, "Test error message")

        mock_pool = mocker.MagicMock()
        mock_pool.apply_async.return_value = mock_task
        mock_pool.__enter__ = mocker.MagicMock(return_value=mock_pool)
        mock_pool.__exit__ = mocker.MagicMock(return_value=None)

        mocker.patch("multiprocessing.Pool", return_value=mock_pool)

        # notify_error をモック
        mock_notify = mocker.patch.object(my_lib.panel_util, "notify_error")

        from create_image import ERROR_CODE_MINOR, create_image

        img, status = create_image(config)

        # エラーコードが返されること
        assert status == ERROR_CODE_MINOR

        # notify_error が呼ばれること
        mock_notify.assert_called()
