#!/usr/bin/env python3
from __future__ import annotations

import concurrent.futures
import io
import logging
import pathlib
import queue
import subprocess
import threading
import time
import traceback
import uuid
from typing import Any, NotRequired, TypedDict

import flask
import my_lib.flask_util
import my_lib.webapp.config

blueprint = flask.Blueprint("webapi-run", __name__, url_prefix=my_lib.webapp.config.URL_PREFIX)


class PanelData(TypedDict):
    lock: threading.Lock
    log: queue.Queue[bytes | None]
    image: bytes | None
    time: float
    future: NotRequired[concurrent.futures.Future[None] | None]


_thread_pool: concurrent.futures.ThreadPoolExecutor | None = None
_panel_data_map: dict[str, PanelData] = {}
_create_image_path: pathlib.Path | str | None = None


def init(create_image_path_: pathlib.Path | str) -> None:
    global _thread_pool
    global _create_image_path

    # ThreadPoolExecutorに変更してより効率的な非同期処理を実現
    _thread_pool = concurrent.futures.ThreadPoolExecutor(max_workers=3, thread_name_prefix="image_gen")
    _create_image_path = create_image_path_


def term() -> None:
    global _thread_pool

    if _thread_pool:
        _thread_pool.shutdown(wait=True)


def _image_reader(proc: subprocess.Popen[bytes], token: str) -> None:
    global _panel_data_map
    panel_data = _panel_data_map[token]
    img_stream = io.BytesIO()

    stdout = proc.stdout
    if stdout is None:
        return

    try:
        while True:
            state = proc.poll()
            if state is not None:
                # プロセス終了後の残りデータを読み取り
                remaining = stdout.read()
                if remaining:
                    img_stream.write(remaining)
                break
            try:
                buf = stdout.read(8192)
                if buf:
                    img_stream.write(buf)
                else:
                    time.sleep(0.1)
            except OSError:
                # パイプが閉じられた場合
                break
        panel_data["image"] = img_stream.getvalue()
    except Exception:
        logging.exception("Failed to generate image")


def _log_reader(proc: subprocess.Popen[bytes], token: str) -> None:
    global _panel_data_map

    panel_data = _panel_data_map[token]
    stderr = proc.stderr
    if stderr is None:
        return

    try:
        while True:
            line = stderr.readline()
            if not line:
                break
            panel_data["log"].put(line)
    except Exception:
        logging.exception("Failed to read log")


def _generate_image_impl(
    config_file: str, is_small_mode: bool, is_dummy_mode: bool, is_test_mode: bool, token: str
) -> None:
    global _panel_data_map

    panel_data = _panel_data_map[token]
    if _create_image_path is None:
        logging.error("create_image_path is not initialized")
        panel_data["log"].put(None)
        return

    cmd: list[str | pathlib.Path] = ["python3", _create_image_path, "-c", config_file]
    if is_small_mode:
        cmd.append("-S")
    if is_dummy_mode:
        cmd.append("-d")
    if is_test_mode:
        cmd.append("-t")

    try:
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=False)  # noqa: S603

        # 非同期でstdoutとstderrを読み取り
        stdout_thread = threading.Thread(target=_image_reader, args=(proc, token))
        stderr_thread = threading.Thread(target=_log_reader, args=(proc, token))

        stdout_thread.start()
        stderr_thread.start()

        # プロセス終了を非ブロッキングで監視
        while proc.poll() is None:
            time.sleep(0.1)

        # プロセス終了を待機（タイムアウト付き）
        try:
            proc.wait(timeout=120)
        except subprocess.TimeoutExpired:
            logging.warning("Subprocess timed out, terminating")
            proc.terminate()
            try:
                proc.wait(timeout=10)
            except subprocess.TimeoutExpired:
                proc.kill()

        # スレッドの終了を待機（タイムアウト付き）
        stdout_thread.join(timeout=30)
        stderr_thread.join(timeout=30)

        # NOTE: None を積むことで、実行完了を通知
        panel_data["log"].put(None)
    except Exception:
        logging.exception("Failed to execute subprocess")
        panel_data["log"].put(None)


def _clean_map() -> None:
    global _panel_data_map

    remove_token: list[str] = []
    for token, panel_data in _panel_data_map.items():
        if (time.time() - panel_data["time"]) > 60:
            remove_token.append(token)

    for token in remove_token:
        del _panel_data_map[token]


def generate_image(config_file: str, is_small_mode: bool, is_dummy_mode: bool, is_test_mode: bool) -> str:
    global _thread_pool
    global _panel_data_map

    if _thread_pool is None:
        msg = "_thread_pool is not initialized. Call init() first."
        raise RuntimeError(msg)

    _clean_map()

    token = str(uuid.uuid4())
    log_queue: queue.Queue[bytes | None] = queue.Queue()

    panel_data: PanelData = {
        "lock": threading.Lock(),
        "log": log_queue,
        "image": None,
        "time": time.time(),
        "future": None,
    }
    _panel_data_map[token] = panel_data

    # ThreadPoolExecutorのsubmitを使用して非同期実行
    future = _thread_pool.submit(
        _generate_image_impl, config_file, is_small_mode, is_dummy_mode, is_test_mode, token
    )
    _panel_data_map[token]["future"] = future

    return token


@blueprint.route("/api/image", methods=["POST"])
@my_lib.flask_util.gzipped
def api_image() -> flask.Response | str:
    global _panel_data_map

    # NOTE: @gzipped をつけた場合、キャッシュ用のヘッダを付与しているので、
    # 無効化する。
    flask.g.disable_cache = True

    token = flask.request.form.get("token", "")

    if token not in _panel_data_map:
        return f"Invalid token: {token}"

    image_data = _panel_data_map[token]["image"]

    return flask.Response(image_data, mimetype="image/png")


@blueprint.route("/api/log", methods=["POST"])
def api_log() -> flask.Response | str:
    global _panel_data_map

    token = flask.request.form.get("token", "")

    if token not in _panel_data_map:
        return f"Invalid token: {token}"

    log_queue = _panel_data_map[token]["log"]

    def generate() -> Any:
        try:
            while True:
                try:
                    log = log_queue.get(timeout=0.1)
                except queue.Empty:
                    continue
                if log is None:
                    break
                log_str = log.decode("utf-8")
                yield log_str
        except Exception:
            logging.exception("Failed to read log")

    res = flask.Response(flask.stream_with_context(generate()), mimetype="text/plain")
    res.headers.add("Access-Control-Allow-Origin", "*")
    res.headers.add("Cache-Control", "no-cache")
    res.headers.add("X-Accel-Buffering", "no")

    return res


@blueprint.route("/api/run", methods=["GET"])
@my_lib.flask_util.support_jsonp
def api_run() -> flask.Response:
    mode = flask.request.args.get("mode", "")
    is_small_mode = mode == "small"
    is_test_mode = flask.request.args.get("test", False, type=bool)

    config_file = (
        flask.current_app.config["CONFIG_FILE_SMALL"]
        if is_small_mode
        else flask.current_app.config["CONFIG_FILE_NORMAL"]
    )
    is_dummy_mode = flask.current_app.config["DUMMY_MODE"]

    try:
        token = generate_image(config_file, is_small_mode, is_dummy_mode, is_test_mode)

        return flask.jsonify({"token": token})
    except Exception:
        return flask.jsonify({"token": "", "error": traceback.format_exc()})
