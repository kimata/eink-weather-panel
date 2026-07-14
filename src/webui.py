#!/usr/bin/env python3
"""
電子ペーパ表示用の画像を表示する簡易的な Web サーバです。

Usage:
  webui.py [-c CONFIG] [-s CONFIG] [-p PORT] [-d] [-D]

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

import flask
import flask_cors
import my_lib.config
import my_lib.webapp.runner

import weather_display.metrics.webapi.page
import weather_display.runner.webapi.run

SCHEMA_CONFIG = "schema/config.schema"
URL_PREFIX = "/panel"


def create_app(config_file_normal, config_file_small, dummy_mode=False, use_reloader=False):
    # NOTE: 関数内 import は my_lib をローカル変数にするため、モジュールレベルの
    # my_lib.* 参照より先にまとめて行う
    import my_lib.webapp.base
    import my_lib.webapp.config
    import my_lib.webapp.util

    # NOTE: アクセスログは無効にする
    my_lib.webapp.runner.silence_werkzeug_log()

    config_data = my_lib.config.load(config_file_normal, pathlib.Path(SCHEMA_CONFIG))
    webapp_config = my_lib.webapp.config.WebappConfig.parse(config_data["webapp"])
    environment = my_lib.webapp.config.build_environment(webapp_config, url_prefix=URL_PREFIX)

    # NOTE: werkzeug リローダー使用時はリローダーの子プロセス (WERKZEUG_RUN_MAIN=true) でのみ
    # 初期化する。それ以外 (gunicorn 等の WSGI サーバーやテスト) では常に初期化する。
    if my_lib.webapp.runner.should_init(use_reloader):
        # NOTE: オプションでダミーモードが指定された場合、環境変数もそれに揃えておく
        if dummy_mode:
            logging.warning("Set dummy mode")
            os.environ["DUMMY_MODE"] = "true"

        weather_display.runner.webapi.run.init(pathlib.Path(__file__).parent / "create_image.py")

        def notify_terminate():  # pragma: no cover
            weather_display.runner.webapi.run.term()

        atexit.register(notify_terminate)

    app = flask.Flask("eink-weather-panel")

    flask_cors.CORS(app)

    app.config["CONFIG_FILE_NORMAL"] = config_file_normal
    app.config["CONFIG_FILE_SMALL"] = config_file_small
    app.config["DUMMY_MODE"] = dummy_mode

    app.register_blueprint(
        my_lib.webapp.base.create_static_blueprint(environment=environment), url_prefix=URL_PREFIX
    )
    app.register_blueprint(my_lib.webapp.base.create_root_redirect_blueprint(url_prefix=URL_PREFIX))
    app.register_blueprint(my_lib.webapp.util.blueprint, url_prefix=URL_PREFIX)
    app.register_blueprint(weather_display.runner.webapi.run.blueprint, url_prefix=URL_PREFIX)
    app.register_blueprint(weather_display.metrics.webapi.page.blueprint, url_prefix=URL_PREFIX)

    my_lib.webapp.config.show_handler_list(app)

    return app


SPEC = my_lib.webapp.runner.WebAppSpec(
    logger_name="panel.e-ink.weather",
    # create_app が設定ファイルパスを直接受けるため、ここでは読み込まずパスのまま渡す
    config_loader=lambda config_file, args: config_file,
    app_factory=lambda config, ctx: create_app(
        config, ctx.args["-s"], ctx.dummy_mode, use_reloader=ctx.use_reloader
    ),
    term_hooks=(weather_display.runner.webapi.run.term,),
)

if __name__ == "__main__":
    assert __doc__ is not None  # noqa: S101
    my_lib.webapp.runner.run(SPEC, __doc__)
