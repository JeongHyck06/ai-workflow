"""Project-local URLs and opt-in secrets. Secret values never appear in lists."""
import json
import os
import re
import tempfile
import threading
from urllib.parse import urlsplit
import subprocess
from urllib.request import Request, build_opener, HTTPRedirectHandler
from urllib.error import HTTPError, URLError
from concurrent.futures import ThreadPoolExecutor
import launch

LOCK = threading.RLock()
LINKS = ('git', 'backend', 'frontend', 'app', 'figma', 'deploy')


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


def git_url(folder=None):
    folder = folder or launch.PRODUCT_ROOT
    if not (folder / '.git').exists():
        return ''
    try:
        value = subprocess.run(['git', 'remote', 'get-url', 'origin'], cwd=folder,
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
        return dict(name=launch.PRODUCT_ROOT.name, root=str(launch.PRODUCT_ROOT),
                    links={key: data['links'].get(key, git_url() if key == 'git' else git_url(launch.PRODUCT_ROOT / key) if key in ('backend', 'frontend', 'app') else '') for key in LINKS},
                    secrets=[dict(name=name, masked='••••••••') for name in sorted(data['secrets'])])


def update(body):
    with LOCK:
        data = read_store()
        action = body.get('action')
        if action == 'links':
            links = body.get('links')
            if not isinstance(links, dict) or not set(links).issubset(LINKS):
                raise ValueError('프로젝트 URL을 확인하세요.')
            data['links'].update({key: valid_url(value) for key, value in links.items()})
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


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def check_link(item):
    key, url = item
    if not url:
        return key, '미등록'
    try:
        request = Request(valid_url(url), method='HEAD', headers={'User-Agent': 'TeamMonitor/1.0'})
        with build_opener(NoRedirect).open(request, timeout=5) as response:
            code = response.status
    except HTTPError as error:
        code = error.code
    except (OSError, ValueError, URLError):
        return key, '연결 확인 실패 · 주소 또는 네트워크 확인'
    if 200 <= code < 300:
        return key, '연결 확인됨'
    if 300 <= code < 400:
        return key, '응답 확인 · 이동 또는 로그인 필요'
    if code in (401, 403):
        return key, '로그인 또는 접근 권한 필요'
    if code == 404:
        return key, '찾을 수 없음 · 비공개 저장소는 로그인 후 확인'
    return key, f'자동 확인 불가 (HTTP {code}) · 열기로 확인'


def check_links():
    links = overview()['links']
    with ThreadPoolExecutor(max_workers=6) as pool:
        return dict(pool.map(check_link, links.items()))
