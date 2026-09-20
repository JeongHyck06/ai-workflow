"""Read persisted QA history through Codex's local app-server API.

No thread is started or resumed. Runtime liveness comes from the launcher lock,
not the read-only app-server instance (where every thread is notLoaded).
"""
import json
import os
from pathlib import Path
import select
import shutil
import subprocess
import time

import launch


class Reader:
    def __enter__(self):
        executable = shutil.which('codex')
        if not executable:
            raise RuntimeError('Codex CLI를 찾을 수 없습니다.')
        self.deadline = time.monotonic() + 10
        self.buffer = b''
        self.sequence = 0
        self.process = subprocess.Popen(
            [executable, 'app-server', '--listen', 'stdio://'],
            cwd=launch.ROOT, env=launch.clean_env(), stdin=subprocess.PIPE,
            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
        try:
            self.request('initialize', {'clientInfo': {'name': 'team_monitor', 'version': '0.1.0'}})
            self.send({'method': 'initialized'})
        except BaseException:
            self.__exit__(None, None, None)
            raise
        return self

    def send(self, message):
        self.process.stdin.write((json.dumps(message) + '\n').encode())
        self.process.stdin.flush()

    def request(self, method, params):
        if method not in ('initialize', 'thread/list', 'thread/read'):
            raise ValueError('Only read-only methods are allowed')
        self.sequence += 1
        self.send(dict(id=self.sequence, method=method, params=params))
        while time.monotonic() < self.deadline:
            if b'\n' not in self.buffer:
                if not select.select([self.process.stdout], [], [], max(0, self.deadline - time.monotonic()))[0]:
                    break
                part = os.read(self.process.stdout.fileno(), 65536)
                if not part:
                    raise RuntimeError('Codex 기록 조회 연결이 종료되었습니다.')
                self.buffer += part
                if len(self.buffer) > 32 * 1024 * 1024:
                    raise RuntimeError('QA 기록이 조회 크기 제한을 초과했습니다.')
                continue
            line, self.buffer = self.buffer.split(b'\n', 1)
            message = json.loads(line)
            if message.get('id') != self.sequence:
                continue
            if 'error' in message:
                raise RuntimeError('Codex 기록 조회에 실패했습니다. CLI 버전을 확인하세요.')
            return message['result']
        raise RuntimeError('Codex 기록 조회 시간이 초과되었습니다.')

    def __exit__(self, *args):
        if self.process.poll() is None:
            self.process.terminate()
            try:
                self.process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait(timeout=2)
        self.process.stdin.close()
        self.process.stdout.close()


def is_qa(thread):
    return (Path(thread.get('cwd', '')).resolve() == launch.ROOT.resolve()
            and thread.get('preview', '').startswith('이 프로젝트의 QA 역할 세션이다.'))


def format_history(thread):
    blocks = []
    for turn in thread.get('turns', []):
        for item in turn.get('items', []):
            kind = item.get('type')
            if kind == 'userMessage':
                value = '\n'.join(c.get('text', '') for c in item.get('content', []) if c.get('type') == 'text')
                blocks.append('[요청]\n' + value)
            elif kind == 'agentMessage':
                blocks.append('[QA]\n' + item.get('text', ''))
            elif kind == 'commandExecution':
                output = item.get('aggregatedOutput') or ''
                if len(output) > 2000:
                    output = '[출력 앞부분 생략]\n' + output[-2000:]
                blocks.append('[실행 · ' + item.get('status', '') + '] ' + item.get('command', '') + '\n' + output)
        if turn.get('error'):
            blocks.append('[오류]\n' + str(turn['error'].get('message', '실행 오류')))
    return '\n\n'.join(blocks)[-24000:]


def read():
    with Reader() as client:
        cursor = None
        # Only this project's sessions are requested; only a role-marked QA
        # session's full history is read. Newest initialization wins.
        for _ in range(20):
            result = client.request('thread/list', dict(cwd=str(launch.ROOT),
                                    limit=100, sortKey='created_at', cursor=cursor))
            candidates = [t for t in result['data'] if is_qa(t)]
            if candidates:
                selected = max(candidates, key=lambda t: t.get('createdAt', 0))
                thread = client.request('thread/read', dict(threadId=selected['id'], includeTurns=True))['thread']
                if not is_qa(thread) or thread['id'] != selected['id']:
                    raise RuntimeError('QA 세션 식별 정보를 확인할 수 없습니다.')
                return dict(session=thread['id'], log=format_history(thread),
                            logUpdated=thread.get('updatedAt'), model=thread.get('model'))
            cursor = result.get('nextCursor')
            if not cursor:
                return None
        raise RuntimeError('QA 세션을 조회 범위 안에서 찾지 못했습니다.')


def populate(row):
    row['status'] = launch.status_for('qa', set())[0] if launch.STATE.exists() else 'NOT_STARTED'
    try:
        history = read()
        if history is None:
            row['message'] = '저장된 QA 대화가 아직 없습니다.'
            return
        model = history.pop('model')
        row.update(history)
        if model:
            row['model'] = model
        row['message'] = '저장된 QA 대화와 실행 기록입니다. 자동 갱신 시 최신 기록을 확인합니다.'
        if not row['log']:
            row['message'] = 'QA 세션을 찾았습니다. 아직 저장된 출력이 없습니다.'
    except (OSError, ValueError, KeyError, TypeError, RuntimeError, subprocess.SubprocessError):
        row['message'] = 'QA 기록을 조회할 수 없습니다. Codex CLI 설치·버전과 로컬 기록 접근 권한을 확인하세요.'
    return row
