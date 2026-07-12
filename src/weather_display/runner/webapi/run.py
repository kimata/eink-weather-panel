#!/usr/bin/env python3
# NOTE: `from __future__ import annotations` を付けると注釈が文字列になり、
# flask_pydantic の validate() がモデルを解決できなくなるため付けないこと
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
from dataclasses import dataclass
from typing import Any

import flask
import my_lib.flask_util
from flask_pydantic import validate

import weather_display.runner.webapi.schemas as schemas

# NOTE: URL prefix はアプリ側の register_blueprint(url_prefix=...) で指定する
blueprint = flask.Blueprint("webapi-run", __name__)


@dataclass
class PanelData:
    log: queue.Queue[bytes | None]
    time: float
    image: bytes = b""
    future: concurrent.futures.Future[None] | None = None
    # NOTE: 生成完了時刻。トークンの有効期限はこの時刻を起点に計算する
    completed_time: float | None = None


# NOTE: create_image.py の終了コード。220 (一部パネル失敗)・222 (全パネル失敗) でも
# 画像自体は生成される
_ERROR_CODE_MINOR = 220
_ERROR_CODE_MAJOR = 222

_thread_pool: concurrent.futures.ThreadPoolExecutor | None = None
_panel_data_map: dict[str, PanelData] = {}
# NOTE: webui は threaded=True で動作するため、_panel_data_map の操作はこのロックで保護する
_map_lock = threading.Lock()
_create_image_path: pathlib.Path | str | None = None


def _get_panel_data(token: str) -> PanelData | None:
    with _map_lock:
        return _panel_data_map.get(token)


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
    panel_data = _get_panel_data(token)
    if panel_data is None:
        return
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
        panel_data.image = img_stream.getvalue()
    except Exception:
        logging.exception("Failed to generate image")


def _log_reader(proc: subprocess.Popen[bytes], token: str) -> None:
    panel_data = _get_panel_data(token)
    if panel_data is None:
        return
    stderr = proc.stderr
    if stderr is None:
        return

    try:
        while True:
            line = stderr.readline()
            if not line:
                break
            panel_data.log.put(line)
    except Exception:
        logging.exception("Failed to read log")


def _generate_image_impl(
    config_file: str, is_small_mode: bool, is_dummy_mode: bool, is_test_mode: bool, token: str
) -> None:
    panel_data = _get_panel_data(token)
    if panel_data is None:
        return

    try:
        if _create_image_path is None:
            logging.error("create_image_path is not initialized")
            return

        cmd: list[str | pathlib.Path] = ["python3", _create_image_path, "-c", config_file]
        if is_small_mode:
            cmd.append("-S")
        if is_dummy_mode:
            cmd.append("-d")
        if is_test_mode:
            cmd.append("-t")

        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=False)  # noqa: S603

        # 非同期でstdoutとstderrを読み取り
        stdout_thread = threading.Thread(target=_image_reader, args=(proc, token))
        stderr_thread = threading.Thread(target=_log_reader, args=(proc, token))

        stdout_thread.start()
        stderr_thread.start()

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
                proc.wait()

        # スレッドの終了を待機（タイムアウト付き）
        stdout_thread.join(timeout=30)
        stderr_thread.join(timeout=30)

        # NOTE: 220/222 は一部/全パネル失敗でも画像自体は生成されるため正常扱いとする。
        # それ以外の異常終了 (タイムアウト kill 含む) はログに積んでクライアントに伝える
        if proc.returncode not in (0, _ERROR_CODE_MINOR, _ERROR_CODE_MAJOR):
            logging.warning("create_image.py exited abnormally (code: %s)", proc.returncode)
            panel_data.log.put(
                f"ERROR: 画像生成プロセスが異常終了しました (code: {proc.returncode})\n".encode()
            )
    except Exception:
        logging.exception("Failed to execute subprocess")
    finally:
        # NOTE: 完了時刻を記録し (トークン期限の起点)、None を積んで実行完了を通知
        panel_data.completed_time = time.time()
        panel_data.log.put(None)


_TOKEN_EXPIRE_SEC = 300


def _clean_map() -> None:
    # NOTE: 生成中 (future 未完了) のトークンを削除すると、クライアントがログ・画像を
    # 取得できなくなるため、生成完了かつ期限切れのものだけを削除する。
    # 期限はキュー滞留や長時間生成を考慮し、生成完了時刻を起点に計算する
    def _is_expired(panel_data: PanelData, now: float) -> bool:
        if panel_data.future is not None and not panel_data.future.done():
            return False
        base_time = panel_data.completed_time if panel_data.completed_time is not None else panel_data.time
        return (now - base_time) > _TOKEN_EXPIRE_SEC

    now = time.time()

    with _map_lock:
        remove_token: list[str] = [
            token for token, panel_data in _panel_data_map.items() if _is_expired(panel_data, now)
        ]

        for token in remove_token:
            del _panel_data_map[token]


def generate_image(config_file: str, is_small_mode: bool, is_dummy_mode: bool, is_test_mode: bool) -> str:
    global _thread_pool

    if _thread_pool is None:
        msg = "_thread_pool is not initialized. Call init() first."
        raise RuntimeError(msg)

    _clean_map()

    token = str(uuid.uuid4())
    log_queue: queue.Queue[bytes | None] = queue.Queue()

    panel_data = PanelData(
        log=log_queue,
        time=time.time(),
    )
    with _map_lock:
        _panel_data_map[token] = panel_data

    # ThreadPoolExecutorのsubmitを使用して非同期実行
    future = _thread_pool.submit(
        _generate_image_impl, config_file, is_small_mode, is_dummy_mode, is_test_mode, token
    )
    panel_data.future = future

    return token


@blueprint.route("/api/image", methods=["POST"])
@my_lib.flask_util.gzipped
@validate()
def api_image(form: schemas.TokenRequest) -> flask.Response | str:
    # NOTE: @gzipped をつけた場合、キャッシュ用のヘッダを付与しているので、
    # 無効化する。
    flask.g.disable_cache = True

    panel_data = _get_panel_data(form.token)
    if panel_data is None:
        return f"Invalid token: {form.token}"

    # NOTE: 生成失敗 (タイムアウト kill 等) や未完了で画像が空の場合、空バイト列を
    # image/png の 200 で返すとフロントの Content-Type チェックをすり抜けるため、404 を返す
    if not panel_data.image:
        return flask.Response("Image is not available", status=404, mimetype="text/plain")

    return flask.Response(panel_data.image, mimetype="image/png")


@blueprint.route("/api/log", methods=["POST"])
@validate()
def api_log(form: schemas.TokenRequest) -> flask.Response | str:
    panel_data = _get_panel_data(form.token)
    if panel_data is None:
        return f"Invalid token: {form.token}"

    log_queue = panel_data.log

    def generate() -> Any:
        try:
            while True:
                try:
                    log = log_queue.get(timeout=0.1)
                except queue.Empty:
                    # NOTE: 終端センチネル (None) は一度しか取り出せないため、生成完了後に
                    # 再度ログを取得された場合はここで終端させる (無限ループ防止)
                    if panel_data.future is None or panel_data.future.done():
                        break
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
@validate()
def api_run(query: schemas.RunRequest) -> flask.Response | tuple[flask.Response, int]:
    is_small_mode = query.mode == "small"
    is_test_mode = query.test

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
        logging.exception("Failed to start image generation")
        return flask.jsonify({"token": "", "error": traceback.format_exc()}), 500
