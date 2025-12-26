#!/usr/bin/env python3
# ruff: noqa: S101
"""
共通テストフィクスチャ

テスト全体で使用する共通のフィクスチャとヘルパーを定義します。
"""
import datetime
import logging
import pathlib
import unittest.mock
import zoneinfo

# NOTE: 先に pandas を import しないと、下記のエラーがでる
# TypeError: type 'pandas._libs.tslibs.base.ABCTimestamp' is not dynamically allocated
# but its base type 'FakeDatetime' is dynamically...
import pandas as pd  # noqa: F401
import pytest

# === 定数 ===
CONFIG_FILE = "config.example.yaml"
CONFIG_SMALL_FILE = "config-small.example.yaml"
# プロジェクトルートの reports/evidence/ に画像を保存
EVIDENCE_DIR = pathlib.Path(__file__).parent.parent / "reports" / "evidence"
EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)


# === pytest コマンドラインオプション ===
def pytest_addoption(parser):
    """E2E テスト用のコマンドラインオプションを追加"""
    parser.addoption("--host", default="127.0.0.1", help="E2E テスト対象のホスト")
    parser.addoption("--port", default="5000", help="E2E テスト対象のポート")


# === 環境モック ===
@pytest.fixture(scope="session", autouse=True)
def env_mock():
    """テスト環境用の環境変数モック"""
    with unittest.mock.patch.dict(
        "os.environ",
        {
            "TEST": "true",
            "NO_COLORED_LOGS": "true",
            "DUMMY_MODE": "true",
        },
    ) as fixture:
        yield fixture


@pytest.fixture(scope="session", autouse=True)
def slack_mock():
    """Slack API のモック"""
    with (
        unittest.mock.patch(
            "my_lib.notify.slack.slack_sdk.web.client.WebClient.chat_postMessage",
            return_value={"ok": True, "ts": "1234567890.123456"},
        ),
        unittest.mock.patch(
            "my_lib.notify.slack.slack_sdk.web.client.WebClient.files_upload_v2",
            return_value={"ok": True, "files": [{"id": "test_file_id"}]},
        ),
        unittest.mock.patch(
            "my_lib.notify.slack.slack_sdk.web.client.WebClient.files_getUploadURLExternal",
            return_value={"ok": True, "upload_url": "https://example.com"},
        ) as fixture,
    ):
        yield fixture


# === 設定フィクスチャ ===
@pytest.fixture(scope="session")
def app():
    """Flask アプリケーションを作成"""
    import my_lib.webapp.config

    my_lib.webapp.config.URL_PREFIX = "/panel"

    import webui

    with unittest.mock.patch.dict("os.environ", {"WERKZEUG_RUN_MAIN": "true"}):
        app = webui.create_app(CONFIG_FILE, CONFIG_SMALL_FILE, dummy_mode=True)
        yield app


@pytest.fixture
def config():
    """通常設定を読み込む"""
    import weather_display.config

    return weather_display.config.load(CONFIG_FILE)


@pytest.fixture
def config_small():
    """小型ディスプレイ用設定を読み込む"""
    import weather_display.config

    return weather_display.config.load(CONFIG_SMALL_FILE)


@pytest.fixture(autouse=True)
def _clear(config):
    """各テスト前にステートをクリア"""
    import my_lib.footprint
    import my_lib.notify.slack

    my_lib.footprint.clear(config.liveness.file.display)

    my_lib.notify.slack._interval_clear()
    my_lib.notify.slack._hist_clear()


@pytest.fixture
def client(app):
    """Flask テストクライアント"""
    test_client = app.test_client()
    yield test_client
    test_client.delete()


# === センサーデータモック ===
def _gen_sensor_data(value: list[float] | None = None, valid: bool = True):
    """センサーデータを生成するヘルパー（内部用）"""
    from my_lib.sensor_data import SensorDataResult

    if value is None:
        value = [30.0, 34.0, 25.0, 20.0]

    time_list = [
        datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=i - len(value))
        for i in range(len(value))
    ]

    return SensorDataResult(value=value, time=time_list, valid=valid)


class _FetchDataMock:
    """センサーデータ取得のモッククラス"""

    def __init__(self):
        self.count: dict[str, int] = {}

    def __call__(  # noqa: PLR0911, PLR0912, PLR0913
        self,
        db_config,  # noqa: ARG002
        measure,  # noqa: ARG002
        hostname,  # noqa: ARG002
        field,
        start="-30h",  # noqa: ARG002
        stop="now()",  # noqa: ARG002
        every_min=1,  # noqa: ARG002
        window_min=3,  # noqa: ARG002
        create_empty=True,  # noqa: ARG002
        last=False,  # noqa: ARG002
    ):
        if field in self.count:
            self.count[field] += 1
        else:
            self.count[field] = 1

        count = self.count[field]

        if field == "temp":
            return _gen_sensor_data([30.0, 20.0, 15.0, 0.0])
        elif field == "power":
            if count % 3 == 1:
                return _gen_sensor_data([1500.0, 500.0, 750.0, 0.0])
            elif count % 3 == 2:
                return _gen_sensor_data([20.0, 15.0, 10.0, 0.0])
            else:
                return _gen_sensor_data([1000.0, 750.0, 500.0, 0.0], False)
        elif field == "lux":
            if count % 3 == 0:
                return _gen_sensor_data([0.0, 250.0, 400.0, 500.0])
            elif count % 3 == 1:
                return _gen_sensor_data([0.0, 4.0, 6.0, 8.0])
            else:
                return _gen_sensor_data([0.0, 25.0, 200.0, 500.0], False)
        elif field == "solar_rad":
            return _gen_sensor_data([300.0, 150.0, 50.0, 0.0])
        else:
            return _gen_sensor_data([30.0, 20.0, 15.0, 0.0])


@pytest.fixture
def mock_sensor_fetch_data(mocker):
    """センサーデータ取得のモック"""

    def create_mock():
        fetch_data_mock = _FetchDataMock()

        async def fetch_data_parallel_mock(db_config, requests):
            results = []
            for request in requests:
                result = fetch_data_mock(
                    db_config,
                    request.measure,
                    request.hostname,
                    request.field,
                    request.start,
                    request.stop,
                    request.every_min,
                    request.window_min,
                    request.create_empty,
                    request.last,
                )
                results.append(result)
            return results

        mocker.patch(
            "weather_display.panel.sensor_graph.fetch_data_parallel",
            side_effect=fetch_data_parallel_mock,
        )
        mocker.patch("weather_display.panel.power_graph.fetch_data", side_effect=fetch_data_mock)

        return fetch_data_mock

    return create_mock


# === SSH モック ===
@pytest.fixture
def ssh_mock(mocker):
    """SSH 接続のモック"""
    ssh = mocker.MagicMock()
    stdin = mocker.MagicMock()
    stdout = mocker.MagicMock()
    stderr = mocker.MagicMock()
    stdout.channel.recv_exit_status.return_value = 0
    ssh.exec_command.return_value = (stdin, stdout, stderr)

    mocker.patch("paramiko.RSAKey.from_private_key")
    mocker.patch("paramiko.SSHClient", return_value=ssh)

    return {
        "ssh": ssh,
        "stdin": stdin,
        "stdout": stdout,
        "stderr": stderr,
    }


# === 画像検証ヘルパー ===
class ImageChecker:
    """画像検証ヘルパークラス"""

    def __init__(self, request, evidence_dir):
        self.request = request
        self.evidence_dir = evidence_dir

    def save(self, img, index=None):
        """画像を保存"""
        import my_lib.pil_util

        file_name = (
            f"{self.request.node.name}.png"
            if index is None
            else f"{self.request.node.name}_{index}.png"
        )
        my_lib.pil_util.convert_to_gray(img).save(self.evidence_dir / file_name, "PNG")

    def check(self, img, panel_size, index=None):
        """画像サイズを検証して保存"""
        self.save(img, index)

        # NOTE: matplotlib で生成した画像の場合、期待値より 1pix 小さい場合がある
        assert abs(img.size[0] - panel_size.width) < 2
        assert abs(img.size[1] - panel_size.height) < 2, (
            f"画像サイズが期待値と一致しません。"
            f"(期待値: {panel_size.width} x {panel_size.height}, "
            f"実際: {img.size[0]} x {img.size[1]})"
        )


@pytest.fixture
def image_checker(request):
    """画像検証ヘルパーを返す"""
    return ImageChecker(request, EVIDENCE_DIR)


# === Slack 通知検証 ===
@pytest.fixture
def slack_checker():
    """Slack 通知検証ヘルパーを返す"""
    import my_lib.notify.slack

    class SlackChecker:
        def assert_notified(self, message, index=-1):
            notify_hist = my_lib.notify.slack._hist_get(is_thread_local=False)
            assert len(notify_hist) != 0, "エラー通知がされていません。"
            assert notify_hist[index].find(message) != -1, f"「{message}」が通知されていません。"

        def assert_not_notified(self):
            notify_hist = my_lib.notify.slack._hist_get(is_thread_local=False)
            assert notify_hist == [], "エラー通知がされています。"

    return SlackChecker()


# === ロギング設定 ===
logging.getLogger("selenium.webdriver.remote").setLevel(logging.WARNING)
logging.getLogger("selenium.webdriver.common").setLevel(logging.DEBUG)
