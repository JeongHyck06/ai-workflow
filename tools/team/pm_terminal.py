"""Attach-only PTY bridge. Never launches or stops the PM itself."""
import base64
import fcntl
import os
import pty
import select
import re
import secrets
import shutil
import struct
import subprocess
import termios
import threading
import time
import json
import launch
from pathlib import Path


def belongs_to_project(session):
    cwd = Path(session.get('cwd') or '/').resolve()
    root = launch.ROOT.resolve()
    return cwd == root or (root / '.claude/worktrees') in cwd.parents


class Terminal:
    def __init__(self, executable, session):
        master, slave = pty.openpty()
        self.fd = master
        os.set_blocking(master, False)
        self.lock = threading.Lock()
        self.buffer = bytearray()
        self.closed = False
        self.touched = time.monotonic()
        self.resize(90, 26)
        env = launch.clean_env()
        env.update(TERM='xterm-256color', COLORTERM='truecolor')
        try:
            self.process = subprocess.Popen([executable, 'attach', session], cwd=launch.ROOT,
                env=env, stdin=slave, stdout=slave, stderr=slave, start_new_session=True)
        except Exception:
            os.close(master)
            raise
        finally:
            os.close(slave)
        threading.Thread(target=self.read, daemon=True).start()

    def read(self):
        try:
            while not self.closed:
                if not select.select([self.fd], [], [], 0.5)[0]:
                    continue
                try:
                    chunk = os.read(self.fd, 65536)
                except BlockingIOError:
                    continue
                if not chunk:
                    break
                with self.lock:
                    if len(self.buffer) + len(chunk) > 2_000_000:
                        break
                    self.buffer.extend(chunk)
        except (OSError, ValueError):
            pass
        finally:
            self.close()

    def poll(self):
        with self.lock:
            chunk = bytes(self.buffer)
            self.buffer.clear()
            self.touched = time.monotonic()
            return dict(output=base64.b64encode(chunk).decode(), closed=self.closed)

    def write(self, data):
        with self.lock:
            if self.closed:
                raise RuntimeError('PM 연결이 종료됐습니다. 다시 연결하세요.')
            self.touched = time.monotonic()
            remaining = memoryview(data.encode())
            deadline = time.monotonic() + 5
            while remaining:
                if time.monotonic() >= deadline:
                    raise RuntimeError("PM input timed out; inspect the terminal before retrying")
                if select.select([], [self.fd], [], 0.2)[1]:
                    try:
                        remaining = remaining[os.write(self.fd, remaining):]
                    except BlockingIOError:
                        continue

    def resize(self, cols, rows):
        if type(cols) is not int or type(rows) is not int or not (20 <= cols <= 300 and 5 <= rows <= 150):
            raise ValueError('Invalid terminal size')
        fcntl.ioctl(self.fd, termios.TIOCSWINSZ, struct.pack('HHHH', rows, cols, 0, 0))

    def close(self):
        with self.lock:
            if self.closed:
                return
            self.closed = True
            os.close(self.fd)
        if self.process.poll() is None:
            self.process.terminate()
            try:
                self.process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait()


class Connections:
    def __init__(self):
        self.lock = threading.Lock()
        self.items = {}

    def connect(self):
        executable = shutil.which('claude')
        if not executable:
            raise RuntimeError('Claude CLI를 찾을 수 없습니다.')
        result = subprocess.run([executable, 'agents', '--json'], cwd=launch.ROOT,
            env=launch.clean_env(), capture_output=True, text=True, timeout=10, check=True)
        sessions = json.loads(result.stdout)
        matches = [s for s in sessions if s.get('name') == launch.session_name('pm') and
                   belongs_to_project(s) and s.get('kind') == 'background']
        if len(matches) != 1 or not re.fullmatch(r'[a-zA-Z0-9-]+', matches[0].get('id', '')):
            raise RuntimeError('실행 중인 PM 세션을 하나로 확인할 수 없습니다. 팀 실행 상태를 확인하세요.')
        with self.lock:
            self.reap()
            if len(self.items) >= 4:
                raise RuntimeError('열려 있는 PM 연결이 많습니다. 사용하지 않는 탭을 닫아주세요.')
            key = secrets.token_urlsafe(24)
            self.items[key] = Terminal(executable, matches[0]['id'])
            return key

    def reap(self):
        for key, term in list(self.items.items()):
            if time.monotonic() - term.touched > 60 or term.closed:
                term.close()
                del self.items[key]

    def get(self, key):
        with self.lock:
            term = self.items.get(key)
        if term is None:
            raise RuntimeError('연결이 만료됐습니다. 다시 연결하세요.')
        return term

    def disconnect(self, key):
        with self.lock:
            term = self.items.pop(key, None)
        if term:
            term.close()

    def close(self):
        for key in list(self.items):
            self.disconnect(key)
