#!/usr/bin/env python3
# ruff: noqa: S101
"""
E2E テスト用フィクスチャ

Playwright を使用した E2E テストのためのフィクスチャを定義します。
"""
import pathlib

import pytest
from playwright.sync_api import expect

# プロジェクトルートの reports/evidence/ に保存
EVIDENCE_DIR = pathlib.Path(__file__).parent.parent.parent / "reports" / "evidence"
EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)


@pytest.fixture
def host(request):
    """E2E テスト対象のホストを返す"""
    return request.config.getoption("--host")


@pytest.fixture
def port(request):
    """E2E テスト対象のポートを返す"""
    return request.config.getoption("--port")


@pytest.fixture
def page(page):
    """Playwright ページにデフォルトタイムアウトを設定"""
    timeout = 30000
    page.set_default_navigation_timeout(timeout)
    page.set_default_timeout(timeout)
    expect.set_options(timeout=timeout)

    return page


@pytest.fixture
def browser_context_args(browser_context_args, request):
    """ブラウザコンテキストに動画録画設定を追加"""
    video_dir = pathlib.Path("reports/videos") / request.node.name
    video_dir.mkdir(parents=True, exist_ok=True)

    return {
        **browser_context_args,
        "record_video_dir": str(video_dir),
        "record_video_size": {"width": 2400, "height": 1600},
    }
