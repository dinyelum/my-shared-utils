import subprocess
import time
import socket
import atexit


class SSHTunnel:
    def __init__(self, config: dict):
        self.proc = None
        self.atexit_registered = False
        self.local_port = config['DB_PORT']
        self.local_host = config['DB_HOST']
        self.destination_host = config['DB_HOST']
        self.destination_port = config['REMOTE_DB_PORT']
        self.server = f"{config['SSH_USER']}@{config['SSH_HOST']}"
        self.ssh_port = config['SSH_PORT']
        self.ssh_log_file = config['SSH_LOG_FILE']

    def print(self):
        print("Yes")

    def start(self):
        if not self.atexit_registered:
            atexit.register(self.stop)
            self.atexit_registered = True

        if self.proc and self.proc.poll() is None:
            return

        self.proc = subprocess.Popen(
            [
                "ssh",
                "-N",
                "-L", f"{self.local_port}:{self.destination_host}:{self.destination_port}",
                self.server,
                "-p", self.ssh_port,
                "-o", "ExitOnForwardFailure=yes",
                "-o", "ServerAliveInterval=20",
                "-o", "ServerAliveCountMax=6",
            ],
            stdout=subprocess.DEVNULL,
            stderr=open(self.ssh_log_file, "a"),
        )

        # Wait until tunnel is usable
        for _ in range(10):
            if self.is_port_open():
                return
            time.sleep(1)

        raise RuntimeError("SSH tunnel failed to start")

    def ensure_tunnel_alive(self):
        if self.proc.poll() is not None:
            self.start()

    def stop(self):
        if self.proc and self.proc.poll() is None:
            self.proc.terminate()

    def is_port_open(self):
        try:
            with socket.create_connection((self.local_host, self.local_port), 1):
                return True
        except OSError:
            return False
