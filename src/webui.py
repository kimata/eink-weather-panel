#!/usr/bin/env python3
"""
電子ペーパ表示用の画像を表示する簡易的な Web サーバです。

Usage:
  webapp.py [-c CONFIG] [-s CONFIG] [-p PORT] [-d] [-D]

Options:
  -c CONFIG         : 通常モードで使う設定ファイルを指定します。[default: config.yaml]
  -s CONFIG         : 小型ディスプレイモード使う設定ファイルを指定します。[default: config-small.yaml]
  -p PORT           : WEB サーバのポートを指定します。[default: 5000]
  -d                : ダミーモードで実行します。
  -D                : デバッグモードで動作します。
"""

import atexit
import logging
import os
import pathlib
import signal

import flask
import flask_cors
import my_lib.config
import my_lib.logger
import my_lib.webapp.base

import weather_display.metrics.webapi.page
import weather_display.runner.webapi.run

SCHEMA_CONFIG = "config.schema"


def term():
    weather_display.runner.webapi.run.term()

    # 子プロセスを終了
    my_lib.proc_util.kill_child()

    # プロセス終了
    logging.info("Graceful shutdown completed")
    os._exit(0)


def sig_handler(num, frame):  # noqa: ARG001
    global should_terminate

    logging.warning("receive signal %d", num)

    if num == signal.SIGTERM:
        term()


def create_app(config_file_normal, config_file_small, dummy_mode=False):
    # # NOTE: アクセスログは無効にする
    # logging.getLogger("werkzeug").setLevel(logging.ERROR)

    import my_lib.webapp.config

    my_lib.webapp.config.URL_PREFIX = "/panel"
    my_lib.webapp.config.init(my_lib.config.load(config_file_normal, pathlib.Path(SCHEMA_CONFIG)))

    if os.environ.get("WERKZEUG_RUN_MAIN") == "true":
        # NOTE: オプションでダミーモードが指定された場合、環境変数もそれに揃えておく
        if dummy_mode:
            logging.warning("Set dummy mode")
            os.environ["DUMMY_MODE"] = "true"
        else:  # pragma: no cover
            pass

        weather_display.runner.webapi.run.init(pathlib.Path(__file__).parent / "create_image.py")

        def notify_terminate():  # pragma: no cover
            weather_display.runner.webapi.run.term()

        atexit.register(notify_terminate)
    else:  # pragma: no cover
        pass

    app = flask.Flask("unit_cooler")

    flask_cors.CORS(app)

    app.config["CONFIG_FILE_NORMAL"] = config_file_normal
    app.config["CONFIG_FILE_SMALL"] = config_file_small
    app.config["DUMMY_MODE"] = dummy_mode

    app.register_blueprint(my_lib.webapp.base.blueprint, url_prefix=my_lib.webapp.config.URL_PREFIX)
    app.register_blueprint(my_lib.webapp.base.blueprint_default)
    app.register_blueprint(
        weather_display.runner.webapi.run.blueprint, url_prefix=my_lib.webapp.config.URL_PREFIX
    )
    app.register_blueprint(
        weather_display.metrics.webapi.page.blueprint, url_prefix=my_lib.webapp.config.URL_PREFIX
    )

    my_lib.webapp.config.show_handler_list(app)

    return app


if __name__ == "__main__":
    import docopt

    args = docopt.docopt(__doc__)

    config_file_normal = args["-c"]
    config_file_small = args["-s"]
    port = args["-p"]
    dummy_mode = args["-d"]
    debug_mode = args["-D"]

    my_lib.logger.init("panel.e-ink.weather", level=logging.DEBUG if debug_mode else logging.INFO)

    app = create_app(config_file_normal, config_file_small, dummy_mode)

    signal.signal(signal.SIGTERM, sig_handler)

    # Flaskアプリケーションを実行
    try:
        # NOTE: スクリプトの自動リロード停止したい場合は use_reloader=False にする
        app.run(host="0.0.0.0", port=port, threaded=True, use_reloader=True, debug=debug_mode)  # noqa: S104
    except KeyboardInterrupt:
        logging.info("Received KeyboardInterrupt, shutting down...")
        sig_handler(signal.SIGINT, None)
