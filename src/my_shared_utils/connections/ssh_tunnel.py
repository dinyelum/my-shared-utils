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

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()

    def print(self):
        print("Yes")

    def start(self):
        if not self.atexit_registered:
            atexit.register(self.stop)
            self.atexit_registered = True

        # 1. Do we have an active connection?
        if self.proc and self.proc.poll() is None:
            if self.is_port_open():
                return  # our own process, confirmed alive and listening
            else:
                print("Tunnel process is alive but port is unresponsive. Restarting...")
                self.stop()

        # 2. Is the port occupied by something that isn't us? (e.g. XAMPP)
        if self.is_port_open():
            raise RuntimeError(
                f"""
                Port {self.local_port} is already occupied by another process 
                (not our tunnel). Refusing to start — check for a local service 
                like XAMPP/MySQL bound to this port.
                """
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
