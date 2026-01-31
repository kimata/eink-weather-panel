#!/usr/bin/env python3
"""
Liveness のチェックを行います

Usage:
  healthz.py [-c CONFIG] [-D]

Options:
  -c CONFIG         : CONFIG を設定ファイルとして読み込んで実行します。[default: config.yaml]
  -D                : デバッグモードで動作します。
"""

from __future__ import annotations

import logging
import pathlib
import sys

import my_lib.healthz

import weather_display.config

SCHEMA_CONFIG = "schema/config.schema"


if __name__ == "__main__":
    import docopt
    import my_lib.logger

    assert __doc__ is not None  # noqa: S101
    args = docopt.docopt(__doc__)

    config_file = args["-c"]
    debug_mode = args["-D"]

    my_lib.logger.init("panel.e-ink.weather", level=logging.DEBUG if debug_mode else logging.INFO)

    config = weather_display.config.load(config_file, pathlib.Path(SCHEMA_CONFIG))

    target_list = [
        my_lib.healthz.HealthzTarget(
            name="display",
            liveness_file=config.liveness.file.display,
            interval=config.panel.update.interval,
        )
    ]

    failed_targets = my_lib.healthz.check_liveness_all_with_ports(target_list)

    if not failed_targets:
        logging.info("OK.")
        sys.exit(0)
    else:
        sys.exit(-1)
