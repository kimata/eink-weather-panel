#!/usr/bin/env python3
# ruff: noqa: S101
"""
Web アプリケーション E2E テスト

Playwright を使用して Web アプリケーションの E2E テストを実行します。
"""

import base64
import logging
import pathlib

import pytest
from playwright.sync_api import expect

# プロジェクトルートの reports/evidence/ に保存
EVIDENCE_DIR = pathlib.Path(__file__).parent.parent.parent / "reports" / "evidence"

APP_URL_TMPL = "http://{host}:{port}/panel/"


def app_url(host, port):
    """テスト対象の URL を生成"""
    return APP_URL_TMPL.format(host=host, port=port)


@pytest.mark.e2e
class TestWebappE2E:
    """Web アプリケーション E2E テスト"""

    def test_webapp_image_generation(self, page, host, port):
        """画像生成機能の E2E テスト

        1. Web アプリにアクセス
        2. 生成ボタンをクリック
        3. 画像生成完了を待機
        4. エラーログがないことを確認
        5. 生成された画像を検証
        """
        import PIL.Image

        page.set_viewport_size({"width": 2400, "height": 1600})

        # コンソールログをキャプチャ
        page.on(
            "console",
            lambda message: logging.error(message) if message.type == "error" else logging.info(message),
        )

        # アプリにアクセス
        page.goto(app_url(host, port), wait_until="domcontentloaded")

        # 生成ボタンをクリック
        page.get_by_test_id("button").click()
        expect(page.get_by_test_id("button")).to_contain_text("生成中")

        # 画像生成完了を待機（最大4分）
        expect(page.get_by_test_id("button")).to_be_enabled(timeout=240000)

        # ログにエラーがないことを確認
        # ログフォーマット: "YYYY-MM-DD HH:MM:SS LEVEL [file:line func] message"
        # ログレベルの ERROR のみをチェックし、例外クラス名 (ConnectionResetError 等) は無視
        log_list = page.locator('//div[contains(@data-testid,"log")]/small/span')
        for i in range(log_list.count()):
            expect(log_list.nth(i)).not_to_contain_text(" ERROR ")

        # 生成された画像を取得
        img_elem = page.get_by_test_id("image")
        img_base64 = img_elem.evaluate(
            """
            element => {
                var canvas = document.createElement('canvas');
                canvas.width = element.naturalWidth;
                canvas.height = element.naturalHeight;
                canvas.getContext('2d').drawImage(
                    element, 0, 0, element.naturalWidth, element.naturalHeight
                );
                return canvas.toDataURL().substring("data:image/png;base64,".length)
            }
            """
        )

        # 画像を保存
        img_path = EVIDENCE_DIR / "e2e_generated.png"
        with pathlib.Path(img_path).open("wb") as f:
            f.write(base64.b64decode(img_base64))

        # 画像サイズが一定以上あること（256KB以上）
        assert img_path.stat().st_size > (256 * 1024), (
            f"画像サイズが小さすぎます: {img_path.stat().st_size} bytes"
        )

        # 画像として正常に認識できること
        img_size = PIL.Image.open(img_path).size
        assert img_size[0] > 100, f"画像幅が小さすぎます: {img_size[0]}"
        assert img_size[1] > 100, f"画像高さが小さすぎます: {img_size[1]}"
