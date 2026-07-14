#!/usr/bin/env python3
"""
Liveness のチェックを行います

Usage:
  healthz.py [-c CONFIG] [-S] [-D]

Options:
  -c CONFIG         : CONFIG を設定ファイルとして読み込んで実行します。[default: config.yaml]
  -S                : 小型ディスプレイモードで実行します。
  -D                : デバッグモードで動作します。
"""

from __future__ import annotations

import pathlib

import my_lib.healthz
import my_lib.healthz.cli

import weather_display.config

SCHEMA_CONFIG = "schema/config.schema"
SCHEMA_CONFIG_SMALL = "schema/config-small.schema"


def _load_config(config_file, args):
    return weather_display.config.load(
        config_file, pathlib.Path(SCHEMA_CONFIG_SMALL if args["-S"] else SCHEMA_CONFIG)
    )


def _targets(config, args):
    return [
        my_lib.healthz.HealthzTarget(
            name="display",
            liveness_file=config.liveness.file.display,
            interval=config.panel.update.interval,
        )
    ]


SPEC = my_lib.healthz.cli.HealthzCliSpec(
    logger_name="panel.e-ink.weather",
    config_loader=_load_config,
    targets_builder=_targets,
)

if __name__ == "__main__":
    assert __doc__ is not None  # noqa: S101
    my_lib.healthz.cli.run(SPEC, __doc__)
