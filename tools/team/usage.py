"""Recorded project token usage, not billing or account quota estimates."""
import json
from pathlib import Path
import re
import threading
import time
import launch
from pm_terminal import belongs_to_project
from qa_logs import Reader


def records(path):
    with path.open(encoding='utf-8') as handle:
        for line in handle:
            try:
                value = json.loads(line)
                if isinstance(value, dict):
                    yield value
            except ValueError:
                continue  # The active process may still be appending a record.


def number(value):
    return value if isinstance(value, int) and value >= 0 else 0


def claude_usage(base=None):
    base = base or Path.home() / '.claude/projects'
    prefix = re.sub(r'[^a-zA-Z0-9-]', '-', str(launch.ROOT))
    messages = {}
    sessions = set()
    failures = 0
    for folder in base.glob(prefix + '*'):
        if folder.name != prefix and not folder.name.startswith(prefix + '--claude-worktrees-'):
            continue
        for path in folder.glob('*.jsonl'):
            if path.is_symlink():
                continue
            try:
                for record in records(path):
                    if record.get('type') != 'assistant' or not belongs_to_project(record):
                        continue
                    message = record.get('message') or {}
                    values = message.get('usage')
                    key = (record.get('sessionId'), message.get('id'))
                    if not isinstance(values, dict) or not all(key):
                        continue
                    sessions.add(key[0])
                    previous = messages.setdefault(key, {})
                    # Multiple content blocks can repeat one API message's usage.
                    for field in ('input_tokens', 'output_tokens', 'cache_read_input_tokens', 'cache_creation_input_tokens'):
                        previous[field] = max(previous.get(field, 0), number(values.get(field)))
            except OSError:
                failures += 1
    totals = {key: sum(m.get(key, 0) for m in messages.values()) for key in
              ('input_tokens', 'output_tokens', 'cache_read_input_tokens', 'cache_creation_input_tokens')}
    return dict(provider='Claude', sessions=len(sessions), available=bool(messages),
                input=totals['input_tokens'] + totals['cache_read_input_tokens'] + totals['cache_creation_input_tokens'],
                output=totals['output_tokens'], cached=totals['cache_read_input_tokens'],
                cacheWrite=totals['cache_creation_input_tokens'], partial=bool(failures))


def codex_file_usage(thread, base=None):
    base = (base or Path.home() / '.codex/sessions').resolve()
    path = Path(thread.get('path') or '/')
    if path.is_symlink() or base not in path.resolve().parents:
        return None
    matched = False
    latest = None
    for record in records(path):
        payload = record.get('payload') or {}
        if record.get('type') == 'session_meta':
            matched = payload.get('id') == thread['id'] and Path(payload.get('cwd') or '/').resolve() == launch.ROOT
        if matched and record.get('type') == 'event_msg' and payload.get('type') == 'token_count':
            info = payload.get('info') or {}
            if isinstance(info.get('total_token_usage'), dict):
                latest = info['total_token_usage']
    return latest


def codex_usage():
    totals = dict(provider='Codex', sessions=0, available=False, input=0, output=0, cached=0, cacheWrite=None, partial=False)
    with Reader() as client:
        cursor = None
        seen = set()
        for _ in range(20):
            result = client.request('thread/list', dict(cwd=str(launch.ROOT), cursor=cursor, limit=100))
            for thread in result['data']:
                if Path(thread.get('cwd') or '/').resolve() != launch.ROOT or thread['id'] in seen:
                    continue
                seen.add(thread['id'])
                try:
                    values = codex_file_usage(thread)
                except OSError:
                    totals['partial'] = True
                    continue
                if values is None:
                    continue
                totals['available'] = True
                totals['sessions'] += 1
                for target, source in (('input', 'input_tokens'), ('output', 'output_tokens'), ('cached', 'cached_input_tokens')):
                    totals[target] += number(values.get(source))
            cursor = result.get('nextCursor')
            if not cursor:
                break
        else:
            totals['partial'] = True
    return totals


_lock = threading.Lock()
_cached = None
_updated = 0


def snapshot():
    global _cached, _updated
    with _lock:
        if _cached is not None and time.monotonic() - _updated < 30:
            return _cached
        rows = []
        for provider, reader in [('Claude', claude_usage), ('Codex', codex_usage)]:
            try:
                rows.append(reader())
            except (OSError, ValueError, KeyError, TypeError, RuntimeError):
                rows.append(dict(provider=provider, available=False, partial=True, sessions=0))
        _cached = dict(providers=rows, updated=time.time(),
                       scope='이 프로젝트의 로컬 주 세션 기록 누적 (Claude 작업 트리 포함). 삭제·미저장·하위 에이전트·별도 호스트와 Codex 보관 세션은 제외됩니다.',
                       note='입력에는 캐시 읽기·쓰기가 포함됩니다. 캐시 읽기는 입력의 일부이며 합계에 다시 더하지 않습니다. 계정 잔여 한도·청구 금액이 아닙니다.')
        _updated = time.monotonic()
        return _cached
