#!/usr/bin/env python3
"""Loopback-only team monitor with a PM-only terminal connection."""
import argparse
import errno
import fcntl
import sys
from concurrent.futures import ThreadPoolExecutor
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import re
import shutil
import subprocess
import threading
import time
import launch
import documents
import tech_stack
import design_prompt
import qa_logs
import resources
import usage
import secrets
from urllib.parse import urlparse, parse_qs
from pm_terminal import Connections, belongs_to_project

WEB = Path(__file__).with_name('web')
TEAM_START = {'message': ''}
ANSI = re.compile(r'\x1b\][^\x07]*(?:\x07|\x1b\\)|\x1b\[[0-?]*[ -/]*[@-~]')


def command(args):
    result = subprocess.run(args, cwd=launch.ROOT, env=launch.clean_env(),
                            capture_output=True, text=True, timeout=10)
    if result.returncode:
        raise RuntimeError('CLI 조회 실패. 해당 CLI의 로그인과 실행 상태를 확인하세요.')
    return result.stdout


def clean_log(value):
    return ANSI.sub('', value).replace('\r', '')[-24000:]


def snapshot():
    executable = shutil.which('claude')
    error = None
    sessions = []
    try:
        if not executable:
            raise RuntimeError('claude CLI를 찾을 수 없습니다.')
        sessions = json.loads(command([executable, 'agents', '--json']))
        if not isinstance(sessions, list):
            raise ValueError('Invalid session list')
        sessions = [s for s in sessions if isinstance(s, dict) and
                    belongs_to_project(s) and s.get('kind') == 'background']
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError):
        error = 'Claude 상태를 조회할 수 없습니다. CLI 설치·로그인 상태를 확인하세요.'
    live = {s.get('name'): s for s in sessions}

    def role_data(item):
        role, (provider, model, label) = item
        row = dict(role=role, label=label, provider=provider, model=model,
                   status='NOT_STARTED', log='', message='', session='')
        try:
            state = launch.read_state(role)
            if provider == 'codex':
                qa_logs.populate(row)
                row['log'] = clean_log(row['log'])
                return row
            current = live.get(launch.session_name(role))
            row['status'] = 'UNKNOWN' if error else ('RUNNING' if current else ('STOPPED' if state else 'NOT_STARTED'))
            owned_state = (state.get('project') == str(launch.PRODUCT_ROOT) and
                           state.get('sessionName') == launch.session_name(role))
            session = (current or {}).get('id') or (state.get('session', '') if owned_state else '')
            if session and re.fullmatch(r'[a-zA-Z0-9-]+', session):
                row['session'] = session
            if error:
                row['message'] = error
            elif row['session']:
                try:
                    row['log'] = clean_log(command([executable, 'logs', row['session']]))
                    if not row['log'].strip():
                        row['message'] = '아직 출력이 없습니다.'
                except (OSError, RuntimeError, subprocess.SubprocessError):
                    row['message'] = '최근 출력을 가져올 수 없습니다. 종료된 세션의 로그는 보관되지 않을 수 있습니다.'
            else:
                row['message'] = '아직 시작하지 않은 역할입니다.'
        except (OSError, ValueError, TypeError):
            row.update(status='UNKNOWN', message='역할 상태 파일을 읽을 수 없습니다.')
        return row

    with ThreadPoolExecutor(max_workers=7) as pool:
        rows = list(pool.map(role_data, launch.ROLES.items()))
    try:
        issues = (launch.ROOT / 'docs/issues/ACTIVE.md').read_text()
        issues = re.sub(r'```[\s\S]*?```', '', issues).strip()
    except OSError:
        issues = '진행 Issue 문서를 읽을 수 없습니다.'
    questions = re.findall(r'^\[PM_QUESTION\](.+?)\[/PM_QUESTION\]\s*$',
                           next((r['log'] for r in rows if r['role'] == 'pm'), ''), re.MULTILINE)
    return dict(questions=questions[-20:], roles=rows, issues=issues, updated=time.time(), error=error or TEAM_START['message'],
                project=dict(name=launch.PRODUCT_ROOT.name, root=str(launch.PRODUCT_ROOT)))


class Monitor:
    def __init__(self):
        self.lock = threading.Lock()
        self.data = None
        self.updated = 0

    def get(self):
        with self.lock:
            if self.data is None or time.monotonic() - self.updated >= 4:
                self.data = snapshot()
                self.updated = time.monotonic()
            return self.data


monitor = Monitor()
connections = Connections()
csrf_token = secrets.token_urlsafe(32)


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        allowed = {f'127.0.0.1:{self.server.server_port}', f'localhost:{self.server.server_port}'}
        if self.headers.get('Host') not in allowed:
            self.send_error(403)
            return
        path = self.path.split('?', 1)[0]
        assets = {'/': ('index.html', 'text/html; charset=utf-8'),
                  '/app.js': ('app.js', 'text/javascript; charset=utf-8'),
                  '/style.css': ('style.css', 'text/css; charset=utf-8'),
                  '/terminal.js': ('terminal.js', 'text/javascript; charset=utf-8'),
                  '/documents.js': ('documents.js', 'text/javascript; charset=utf-8'),
                  '/resources.js': ('resources.js', 'text/javascript; charset=utf-8'),
                  '/markdown-it.js': ('vendor/markdown-it.min.js', 'text/javascript; charset=utf-8'),
                  '/xterm.js': ('vendor/xterm.js', 'text/javascript; charset=utf-8'),
                  '/xterm.css': ('vendor/xterm.css', 'text/css; charset=utf-8'),
                  '/addon-fit.js': ('vendor/addon-fit.js', 'text/javascript; charset=utf-8')}
        if path in ('/api/resources', '/api/usage'):
            try:
                self.json_response(resources.overview() if path == '/api/resources' else usage.snapshot())
            except (OSError, ValueError, KeyError, TypeError):
                self.json_response(dict(error='프로젝트 설정을 읽을 수 없습니다.'), 500)
            return
        if path in ('/api/stack', '/api/design-prompt'):
            try:
                self.json_response((tech_stack if path == '/api/stack' else design_prompt).read())
            except (OSError, ValueError):
                self.json_response(dict(error='공용 문서를 읽지 못했습니다.'), 400)
            return
        if path in ('/api/docs', '/api/doc'):
            try:
                if path == '/api/docs':
                    self.json_response(dict(documents=documents.index(), project=str(launch.ROOT.resolve())))
                else:
                    name = parse_qs(urlparse(self.path).query).get('path', [''])[0]
                    self.json_response(documents.read(name))
            except (OSError, ValueError, UnicodeError):
                self.json_response(dict(error='문서를 읽을 수 없습니다. 파일 경로와 내용을 확인하세요.'), 404)
            return
        if path == '/api/session':
            self.json_response(dict(token=csrf_token))
            return
        if path == '/api/pm/output':
            try:
                key = parse_qs(urlparse(self.path).query).get('connection', [''])[0]
                self.json_response(connections.get(key).poll())
            except RuntimeError as error:
                self.json_response(dict(error=str(error)), 409)
            return
        if path == '/api/state':
            payload = json.dumps(monitor.get(), ensure_ascii=False).encode()
            content_type = 'application/json; charset=utf-8'
        elif path in assets:
            filename, content_type = assets[path]
            payload = (WEB / filename).read_bytes()
        else:
            self.send_error(404)
            return
        self.send_response(200)
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', str(len(payload)))
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('Content-Security-Policy', "default-src 'self'; style-src 'self' 'unsafe-inline'; frame-ancestors 'none'; base-uri 'none'")
        self.end_headers()
        try:
            self.wfile.write(payload)
        except (BrokenPipeError, ConnectionResetError):
            pass

    def json_response(self, data, status=200):
        payload = json.dumps(data, ensure_ascii=False).encode()
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('Content-Length', str(len(payload)))
        self.end_headers()
        try:
            self.wfile.write(payload)
        except (BrokenPipeError, ConnectionResetError):
            pass

    def do_POST(self):
        host = self.headers.get('Host', '')
        allowed = {f'127.0.0.1:{self.server.server_port}', f'localhost:{self.server.server_port}'}
        if (host not in allowed or self.headers.get('Origin') != 'http://' + host or
                not secrets.compare_digest(self.headers.get('X-Team-Token', ''), csrf_token)):
            self.json_response(dict(error='허용되지 않은 요청입니다.'), 403)
            return
        try:
            length = int(self.headers.get('Content-Length', '0'))
            if not 0 < length <= (6_100_000 if self.path == '/api/doc' else 65536) or self.headers.get('Content-Type') != 'application/json':
                raise ValueError('Invalid request')
            body = json.loads(self.rfile.read(length))
            if not isinstance(body, dict):
                raise ValueError('Invalid body')
            if self.path == '/api/resources':
                result = resources.update(body)
                if body.get('action') == 'links':
                    result['checks'] = resources.check_links()
                self.json_response(result)
                return
            if self.path in ('/api/stack', '/api/design-prompt'):
                self.json_response((tech_stack if self.path == '/api/stack' else design_prompt).save(body))
                return
            if self.path == '/api/doc':
                self.json_response(documents.save(body))
                return
            if self.path == '/api/pm/connect':
                self.json_response(dict(connection=connections.connect()))
                return
            key = body.get('connection', '')
            if not isinstance(key, str):
                raise ValueError('Invalid connection')
            if self.path == '/api/pm/disconnect':
                connections.disconnect(key)
            elif self.path == '/api/pm/input':
                value = body.get('data')
                if not isinstance(value, str) or len(value) > 16000:
                    raise ValueError('Invalid input')
                connections.get(key).write(value)
            elif self.path == '/api/pm/resize':
                connections.get(key).resize(body.get('cols'), body.get('rows'))
            else:
                self.json_response(dict(error='Not found'), 404)
                return
            self.json_response(dict(ok=True))
        except (ValueError, TypeError):
            self.json_response(dict(error='입력 형식이 올바르지 않습니다.'), 400)
        except (RuntimeError, OSError, subprocess.SubprocessError) as error:
            self.json_response(dict(error=str(error) if isinstance(error, RuntimeError) else 'PM 연결에 실패했습니다. 다시 연결하세요.'), 409)

    def log_message(self, *args):
        pass


def bind_monitor(port=None):
    ports = range(8765, 8865) if port is None else [port]
    for candidate in ports:
        try:
            return ThreadingHTTPServer(('127.0.0.1', candidate), Handler)
        except OSError as error:
            if port is not None or error.errno != errno.EADDRINUSE:
                raise
    raise OSError('사용 가능한 웹 포트가 없습니다. --port로 지정하세요.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port', type=int)
    parser.add_argument('--launch-team', action='store_true')
    parser.add_argument('--provider', choices=['all', 'claude', 'codex'], default='all')
    args = parser.parse_args()
    launch.STATE.mkdir(exist_ok=True, mode=0o700)
    # Keep the lock for the complete server lifetime; stale metadata alone is not ownership.
    with (launch.STATE / 'monitor.lock').open('a') as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            try:
                info = json.loads((launch.STATE / 'monitor.json').read_text())
                print(f"이미 실행 중입니다. Team Monitor: {info['url']}", flush=True)
            except (OSError, ValueError, KeyError):
                print('이 프로젝트의 모니터가 시작 중입니다. 기존 터미널의 주소를 확인하세요.', flush=True)
            return
        serve_monitor(args)


def serve_monitor(args):
    server = bind_monitor(args.port)
    url = f'http://127.0.0.1:{server.server_port}'
    (launch.STATE / 'monitor.json').write_text(json.dumps(dict(
        url=url, project=str(launch.PRODUCT_ROOT), workflow=str(launch.ROOT))))
    def cleanup():
        while True:
            time.sleep(15)
            with connections.lock:
                connections.reap()
    threading.Thread(target=cleanup, daemon=True).start()
    print(f'Project: {launch.PRODUCT_ROOT}\nTeam Monitor: {url}', flush=True)
    if args.launch_team:
        def start_team():
            TEAM_START['message'] = '팀 세션을 초기화하고 있습니다. 준비된 역할부터 표시됩니다.'
            try:
                result = subprocess.run([sys.executable, str(launch.ROOT / 'tools/team/launch.py'),
                                     'team', '--provider', args.provider], cwd=launch.ROOT,
                                        env=launch.clean_env())
                TEAM_START['message'] = ('팀 초기화에 실패했습니다. 실행 터미널의 CLI 오류를 확인하세요.'
                                         if result.returncode else '')
            except OSError:
                TEAM_START['message'] = '팀 실행 프로세스를 시작하지 못했습니다. 실행 환경을 확인하세요.'
            if TEAM_START['message']:
                print(TEAM_START['message'], flush=True)
        threading.Thread(target=start_team, daemon=True).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        connections.close()
        server.server_close()


if __name__ == '__main__':
    main()
