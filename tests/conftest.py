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
EVIDENCE_DIR = pathlib.Path(__file__).parent / "evidence" / "image"
EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
TIMEZONE = zoneinfo.ZoneInfo("Asia/Tokyo")


# === pytest オプション ===
def pytest_addoption(parser):
    parser.addoption("--host", default="127.0.0.1")
    parser.addoption("--port", default="5000")


@pytest.fixture
def host(request):
    return request.config.getoption("--host")


@pytest.fixture
def port(request):
    return request.config.getoption("--port")


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


@pytest.fixture
def config_dict():
    """互換性のために辞書形式の設定を返す"""
    import my_lib.config

    config_ = my_lib.config.load(CONFIG_FILE)
    config_["panel"]["update"]["interval"] = 60

    return config_


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
def gen_sensor_data(value=None, valid=True):
    """センサーデータを生成するヘルパー"""
    from my_lib.sensor_data import SensorDataResult

    if value is None:
        value = [30, 34, 25, 20]

    time_list = []
    for i in range(len(value)):
        time_list.append(
            datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=i - len(value))
        )

    return SensorDataResult(value=value, time=time_list, valid=valid)


@pytest.fixture
def sensor_data_factory():
    """センサーデータファクトリを返す"""
    return gen_sensor_data


@pytest.fixture
def mock_sensor_fetch_data(mocker):
    """センサーデータ取得のモック"""

    def create_mock():
        def fetch_data_mock(  # noqa: PLR0911, PLR0912, PLR0913
            db_config,  # noqa: ARG001
            measure,  # noqa: ARG001
            hostname,  # noqa: ARG001
            field,
            start="-30h",  # noqa: ARG001
            stop="now(TIMEZONE)",  # noqa: ARG001
            every_min=1,  # noqa: ARG001
            window_min=3,  # noqa: ARG001
            create_empty=True,  # noqa: ARG001
            last=False,  # noqa: ARG001
        ):
            if field in fetch_data_mock.count:
                fetch_data_mock.count[field] += 1
            else:
                fetch_data_mock.count[field] = 1

            count = fetch_data_mock.count[field]

            if field == "temp":
                return gen_sensor_data([30, 20, 15, 0])
            elif field == "power":
                if count % 3 == 1:
                    return gen_sensor_data([1500, 500, 750, 0])
                elif count % 3 == 2:
                    return gen_sensor_data([20, 15, 10, 0])
                else:
                    return gen_sensor_data([1000, 750, 500, 0], False)
            elif field == "lux":
                if count % 3 == 0:
                    return gen_sensor_data([0, 250, 400, 500])
                elif count % 3 == 1:
                    return gen_sensor_data([0, 4, 6, 8])
                else:
                    return gen_sensor_data([0, 25, 200, 500], False)
            elif field == "solar_rad":
                return gen_sensor_data([300, 150, 50, 0])
            else:
                return gen_sensor_data([30, 20, 15, 0])

        fetch_data_mock.count = {}

        # Mock for parallel fetch
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


@pytest.fixture
def open_mock(mocker):
    """builtins.open のモック"""
    import builtins

    orig_open = builtins.open

    def open_mock_impl(
        file,
        mode="r",
        buffering=-1,
        encoding=None,
        errors=None,
        newline=None,
        closefd=True,
        opener=None,
    ):
        if file == "TEST":
            return mocker.MagicMock()
        else:
            return orig_open(file, mode, buffering, encoding, errors, newline, closefd, opener)

    mocker.patch("builtins.open", side_effect=open_mock_impl)
    return open_mock_impl


# === WBGT データ ===
@pytest.fixture
def wbgt_info_factory():
    """WBGT 情報を生成するファクトリ"""

    def create(current=32):
        return {
            "current": current,
            "daily": {
                "today": list(range(18, 34, 2)),
                "tommorow": list(range(18, 34, 2)),
            },
        }

    return create


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

    def check(self, img, size, index=None):
        """画像サイズを検証して保存"""
        self.save(img, index)

        # size は PanelGeometry dataclass または dict を受け付ける
        width = size.width if hasattr(size, "width") else size["width"]
        height = size.height if hasattr(size, "height") else size["height"]

        # NOTE: matplotlib で生成した画像の場合、期待値より 1pix 小さい場合がある
        assert abs(img.size[0] - width) < 2
        assert abs(img.size[1] - height) < 2, (
            "画像サイズが期待値と一致しません。"
            f"(期待値: {width} x {height}, 実際: {img.size[0]} x {img.size[1]})"
        )


@pytest.fixture
def image_checker(request):
    """画像検証ヘルパーを返す"""
    return ImageChecker(request, EVIDENCE_DIR)


# === Slack 通知検証 ===
class SlackChecker:
    """Slack 通知検証ヘルパークラス"""

    def assert_notified(self, message, index=-1):
        """指定したメッセージが通知されていることを確認"""
        import my_lib.notify.slack

        notify_hist = my_lib.notify.slack._hist_get(is_thread_local=False)

        assert len(notify_hist) != 0, "異常が発生したはずなのに、エラー通知がされていません。"
        assert notify_hist[index].find(message) != -1, f"「{message}」が Slack で通知されていません。"

    def assert_not_notified(self):
        """通知されていないことを確認"""
        import my_lib.notify.slack

        notify_hist = my_lib.notify.slack._hist_get(is_thread_local=False)
        assert notify_hist == [], "正常なはずなのに、エラー通知がされています。"


@pytest.fixture
def slack_checker():
    """Slack 通知検証ヘルパーを返す"""
    return SlackChecker()


# === Liveness 検証 ===
class LivenessChecker:
    """Liveness 検証ヘルパークラス"""

    def check(self, config, should_be_healthy):
        """Liveness 状態を検証"""
        import healthz
        from my_lib.healthz import HealthzTarget

        target_list = [
            HealthzTarget(
                name="display",
                liveness_file=config.liveness.file.display,
                interval=config.panel.update.interval,
            )
        ]

        liveness = healthz.check_liveness(target_list)

        if should_be_healthy:
            assert liveness, "Liveness が更新されていません。"
        else:
            assert not liveness, "Liveness が更新されてしまっています。"


@pytest.fixture
def liveness_checker():
    """Liveness 検証ヘルパーを返す"""
    return LivenessChecker()


# === Playwright 用フィクスチャ ===
@pytest.fixture
def page(page):
    """Playwright ページ設定"""
    from playwright.sync_api import expect

    timeout = 30000
    page.set_default_navigation_timeout(timeout)
    page.set_default_timeout(timeout)
    expect.set_options(timeout=timeout)

    return page


@pytest.fixture
def browser_context_args(browser_context_args, request):
    """Playwright ブラウザコンテキスト設定"""
    return {
        **browser_context_args,
        "record_video_dir": f"tests/evidence/{request.node.name}",
        "record_video_size": {"width": 2400, "height": 1600},
    }


# === ロギング設定 ===
logging.getLogger("selenium.webdriver.remote").setLevel(logging.WARNING)
logging.getLogger("selenium.webdriver.common").setLevel(logging.DEBUG)
