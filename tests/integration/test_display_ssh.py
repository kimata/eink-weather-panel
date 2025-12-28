#!/usr/bin/env python3
# ruff: noqa: S101, S603, S607
"""
SSH 接続の統合テスト（Docker ベース）
"""
import socket
import subprocess
import tempfile
import time
import uuid
from pathlib import Path

import paramiko
import pytest


def generate_ssh_key_pair(key_path: Path, pub_key_path: Path) -> None:
    """paramiko を使用して SSH キーペアを生成"""
    # RSA キーを生成
    key = paramiko.RSAKey.generate(2048)

    # 秘密鍵を保存
    key.write_private_key_file(str(key_path))

    # 公開鍵を OpenSSH 形式で保存
    pub_key_str = f"{key.get_name()} {key.get_base64()} test@test\n"
    pub_key_path.write_text(pub_key_str)


def wait_for_ssh_ready(host: str, port: int, timeout: int = 60) -> bool:
    """SSH サーバーが SSH プロトコルバナーを返すまで待機"""
    start = time.time()
    while time.time() - start < timeout:
        try:
            with socket.create_connection((host, port), timeout=5) as sock:
                # SSH プロトコルバナーを読み取る
                sock.settimeout(5)
                banner = sock.recv(256)
                if banner.startswith(b"SSH-"):
                    return True
        except (OSError, ConnectionRefusedError, TimeoutError):
            pass
        time.sleep(2)
    return False


def get_worker_port(worker_id: str) -> int:
    """xdist ワーカー ID からユニークなポート番号を取得"""
    if worker_id == "master":
        return 2222
    # gw0, gw1, gw2, ... -> 2223, 2224, 2225, ...
    worker_num = int(worker_id.replace("gw", ""))
    return 2223 + worker_num


@pytest.fixture(scope="module")
def ssh_server(request):
    """Docker で SSH サーバーを起動"""
    # xdist ワーカー ID を取得（並列実行時はユニークなポートを使用）
    worker_id = getattr(request.config, "workerinput", {}).get("workerid", "master")

    # ユニークなコンテナ名とポートを使用
    container_name = f"test-ssh-server-{uuid.uuid4().hex[:8]}"
    port = get_worker_port(worker_id)

    # 既存のコンテナを削除（念のため）
    subprocess.run(
        ["docker", "rm", "-f", container_name],
        check=False,
        capture_output=True,
    )

    with tempfile.TemporaryDirectory() as tmpdir:
        key_path = Path(tmpdir) / "test_ssh_key"
        pub_key_path = Path(tmpdir) / "test_ssh_key.pub"

        # テスト用の SSH キーを生成（paramiko を使用）
        generate_ssh_key_pair(key_path, pub_key_path)

        # SSH サーバーコンテナを起動
        result = subprocess.run(
            [
                "docker",
                "run",
                "-d",
                "--name",
                container_name,
                "-p",
                f"{port}:2222",
                "-v",
                f"{pub_key_path}:/config/.ssh/authorized_keys:ro",
                "-e",
                "PUID=1000",
                "-e",
                "PGID=1000",
                "-e",
                "USER_NAME=testuser",
                "-e",
                "PASSWORD_ACCESS=false",
                "linuxserver/openssh-server:latest",
            ],
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            pytest.skip(f"Failed to start SSH server: {result.stderr}")

        # サーバー起動を待機
        if not wait_for_ssh_ready("localhost", port, timeout=30):
            subprocess.run(["docker", "rm", "-f", container_name], check=False, capture_output=True)
            pytest.skip("SSH server did not become ready in time")

        try:
            yield {
                "hostname": "localhost",
                "port": port,
                "username": "testuser",
                "key_path": str(key_path),
            }
        finally:
            # クリーンアップ
            subprocess.run(
                ["docker", "rm", "-f", container_name],
                check=False,
                capture_output=True,
            )


@pytest.mark.skipif(
    subprocess.run(["docker", "info"], capture_output=True).returncode != 0,
    reason="Docker is not available",
)
class TestSshConnectIntegration:
    """SSH 接続の統合テスト"""

    def test_ssh_connect_real_server(self, ssh_server):
        """実際の SSH サーバーに接続できること"""
        import paramiko

        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        with open(ssh_server["key_path"]) as f:
            ssh.connect(
                ssh_server["hostname"],
                port=ssh_server["port"],
                username=ssh_server["username"],
                pkey=paramiko.RSAKey.from_private_key(f),
                allow_agent=False,
                look_for_keys=False,
                timeout=10,
            )

        assert ssh is not None
        transport = ssh.get_transport()
        assert transport is not None
        assert transport.is_active()

        # 実際にコマンドを実行
        stdin, stdout, stderr = ssh.exec_command("echo 'hello'")
        result = stdout.read().decode().strip()

        assert result == "hello"

        ssh.close()

    def test_ssh_exec_command_and_close(self, ssh_server):
        """SSH でコマンド実行後に正常終了できること"""
        from weather_display import display

        import paramiko

        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        with open(ssh_server["key_path"]) as f:
            ssh.connect(
                ssh_server["hostname"],
                port=ssh_server["port"],
                username=ssh_server["username"],
                pkey=paramiko.RSAKey.from_private_key(f),
                allow_agent=False,
                look_for_keys=False,
                timeout=10,
            )

        # バックグラウンドプロセスを起動
        ssh.exec_command("sleep 100 &")

        # 終了処理（sleep プロセスを kill して接続を閉じる）
        display.ssh_kill_and_close(ssh, "sleep")

        # 接続が閉じられていること
        transport = ssh.get_transport()
        assert transport is None or not transport.is_active()

    def test_ssh_kill_and_close_with_no_process(self, ssh_server):
        """対象プロセスがなくても正常終了できること"""
        from weather_display import display

        import paramiko

        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        with open(ssh_server["key_path"]) as f:
            ssh.connect(
                ssh_server["hostname"],
                port=ssh_server["port"],
                username=ssh_server["username"],
                pkey=paramiko.RSAKey.from_private_key(f),
                allow_agent=False,
                look_for_keys=False,
                timeout=10,
            )

        # 存在しないプロセスを指定しても例外が発生しないこと
        display.ssh_kill_and_close(ssh, "nonexistent_process_12345")

        # 接続が閉じられていること
        transport = ssh.get_transport()
        assert transport is None or not transport.is_active()
