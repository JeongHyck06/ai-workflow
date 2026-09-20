"""Project-local URLs and opt-in secrets. Secret values never appear in lists."""
import json
import os
import re
import tempfile
import threading
from urllib.parse import urlsplit
import subprocess
import launch

LOCK = threading.RLock()
LINKS = ('git', 'figma', 'deploy')


def read_store():
    target = launch.STATE / 'resources.json'
    if launch.STATE.is_symlink() or target.is_symlink():
        raise ValueError('설정 파일의 심볼릭 링크는 허용되지 않습니다.')
    if not target.exists():
        return {'links': {}, 'secrets': {}}
    with os.fdopen(os.open(target, os.O_RDONLY | os.O_NOFOLLOW), encoding='utf-8') as handle:
        return json.load(handle)


def write_store(data):
    launch.STATE.mkdir(exist_ok=True, mode=0o700)
    if launch.STATE.is_symlink():
        raise ValueError('설정 폴더의 심볼릭 링크는 허용되지 않습니다.')
    launch.STATE.chmod(0o700)
    fd, name = tempfile.mkstemp(prefix='.resources-', dir=launch.STATE)
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as handle:
            json.dump(data, handle, ensure_ascii=False)
        os.replace(name, launch.STATE / 'resources.json')
    finally:
        if os.path.exists(name):
            os.unlink(name)


def valid_url(value):
    if not isinstance(value, str) or len(value) > 2000:
        raise ValueError('URL 형식을 확인하세요.')
    if not value:
        return value
    parsed = urlsplit(value)
    if parsed.scheme not in ('http', 'https') or not parsed.hostname or parsed.username or parsed.password or any(c.isspace() for c in value):
        raise ValueError('인증정보가 없는 http 또는 https URL을 입력하세요.')
    return value


def git_url():
    try:
        value = subprocess.run(['git', 'remote', 'get-url', 'origin'], cwd=launch.ROOT,
                               capture_output=True, text=True, timeout=2, check=True).stdout.strip()
        match = re.fullmatch(r'git@([^:]+):(.+)', value)
        if match:
            value = 'https://' + match[1] + '/' + match[2]
        return valid_url(value.removesuffix('.git'))
    except (OSError, ValueError, subprocess.SubprocessError):
        return ''


def overview():
    with LOCK:
        data = read_store()
        return dict(name=launch.ROOT.name, root=str(launch.ROOT),
                    links={key: data['links'].get(key, git_url() if key == 'git' else '') for key in LINKS},
                    secrets=[dict(name=name, masked='••••••••') for name in sorted(data['secrets'])])


def update(body):
    with LOCK:
        data = read_store()
        action = body.get('action')
        if action == 'links':
            links = body.get('links')
            if not isinstance(links, dict) or set(links) != set(LINKS):
                raise ValueError('프로젝트 URL을 확인하세요.')
            data['links'] = {key: valid_url(value) for key, value in links.items()}
        elif action in ('save-secret', 'delete-secret', 'reveal-secret'):
            name = body.get('name')
            if not isinstance(name, str) or not re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]{0,127}', name):
                raise ValueError('키 이름은 영문·숫자·밑줄을 사용하세요.')
            if action == 'reveal-secret':
                if name not in data['secrets']:
                    raise ValueError('저장된 키를 찾을 수 없습니다.')
                return dict(name=name, value=data['secrets'][name])
            if action == 'delete-secret':
                data['secrets'].pop(name, None)
            else:
                value = body.get('value')
                if not isinstance(value, str) or not 0 < len(value) <= 16000:
                    raise ValueError('키 값을 입력하세요. 최대 16,000자입니다.')
                if len(data['secrets']) >= 100 and name not in data['secrets']:
                    raise ValueError('키는 최대 100개까지 저장할 수 있습니다.')
                data['secrets'][name] = value
        else:
            raise ValueError('허용되지 않은 설정 작업입니다.')
        write_store(data)
        return {'ok': True}
