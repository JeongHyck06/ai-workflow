#!/usr/bin/env python3
"""Launch persistent, interactive role sessions in macOS Terminal using installed CLIs."""
import argparse
import fcntl
import json
import os
from pathlib import Path
import shlex
import shutil
import subprocess
import sys
import time
import project

PRODUCT_ROOT = project.root()
ROOT = project.WORKFLOW
STATE = ROOT / '.team-runtime'
ROLES = {
    'pm': ('claude', 'fable', 'PM'),
    'design': ('claude', 'opus', 'DESIGN'),
    'frontend': ('claude', 'opus', 'FRONTEND'),
    'backend': ('claude', 'opus', 'BACKEND'),
    'qa': ('codex', 'gpt-6-astra', 'QA'),
    'git': ('claude', 'sonnet', 'GIT'),
    'devops': ('claude', 'fable', 'DEVOPS'),
}
def session_name(role):
    return project.session_prefix(PRODUCT_ROOT) + '-' + role


def prompt_for(role):
    _, model, document = ROLES[role]
    sendable = ', '.join(session_name(r) for r, spec in ROLES.items() if spec[0] == 'claude')
    return (
        f'이 프로젝트의 {document} 역할 세션이다. 요청 모델은 {model}이다. '
        f'제품 루트는 {PRODUCT_ROOT}이며 협업 작업 경로는 {ROOT}이다. '
        f'프론트엔드 코드는 {PRODUCT_ROOT / "app"}, 백엔드 코드는 {PRODUCT_ROOT / "backend"}에 작성한다. '
        f'협업 문서·설정·작업 트리는 이 작업 경로 안에서만 관리하고 제품 루트에 복사하지 마라. '
        f'제품 Git 작업 대상은 {PRODUCT_ROOT}이며 협업 도구 저장소와 혼동하지 마라. '
        f'docs/README.md, docs/agents/{document}.md, '
        'docs/issues/ACTIVE.md, docs/agents/TEAM_SETUP.md를 읽어라. '
        '이번 입력은 팀 초기화만 요청한다. 역할, 모델, 읽은 문서, 할당 Issue 유무를 보고하고 '
        '다음 입력을 기다려라. 요구사항·기술 스택·Issue를 임의로 만들거나 기능 구현, '
        'Git 변경, 배포를 시작하지 마라. 다른 세션을 추가 생성하거나 setup을 재호출하지 마라. '
        '실제 작업은 이후 PM의 명시적 할당과 사용자 요청 범위에 따라 진행한다. '
        '세션 간 공유 기록은 docs를 사용한다. 민감값을 기록하지 마라. '
        f'다른 역할 세션의 이름은 {project.session_prefix(PRODUCT_ROOT)}-<role>이며 {sendable}에 메시지를 보낼 수 있다. '
        '사용자와 직접 소통하는 역할은 PM뿐이다. PM은 요청·질문·진행·승인·결과를 취합한다. '
        '다른 역할은 준비 상태와 질문·완료·차단 사유를 PM에게 보고하고 사용자에게 직접 입력을 요구하지 마라. '
        'QA는 Codex라 메시지 대상이 아니다. PM이 통신 연결 부재를 차단 사유로 관리하며 사용자에게 중계를 요구하지 마라.'
    )


def command_for(role, executable):
    provider, model, _ = ROLES[role]
    if provider == 'claude':
        # --bg 세션만 세션 간 메시지 대상으로 등록된다. Terminal 창 세션은 등록되지 않는다.
        return [executable, '--bg', '--name', session_name(role), '--model', model,
                '--settings', '{"attribution":{"commit":"","pr":""}}', prompt_for(role)]
    return [executable, '--model', model, '--cd', str(ROOT), prompt_for(role)]


def clean_env():
    # An independent session must not inherit its caller's nesting marker.
    env = os.environ.copy()
    for key in ('CLAUDECODE', 'CLAUDE_CODE_ENTRYPOINT', 'CODEX_THREAD_ID'):
        env.pop(key, None)
    env['TEAM_PROJECT_ROOT'] = str(PRODUCT_ROOT)
    return env


def bg_names(executable):
    """이 프로젝트에서 살아 있는 background 세션 이름."""
    try:
        out = subprocess.run([executable, 'agents', '--json'], cwd=ROOT, env=clean_env(),
                             capture_output=True, text=True, timeout=30).stdout
        return {s.get('name') for s in json.loads(out)
                if (Path(s.get('cwd') or '/').resolve() == ROOT or
                    ROOT / '.claude/worktrees' in Path(s.get('cwd') or '/').resolve().parents)
                and s.get('kind') == 'background'}
    except (subprocess.SubprocessError, OSError, ValueError):
        return set()


def start_bg(role, executable):
    result = subprocess.run(command_for(role, executable), cwd=ROOT, env=clean_env(),
                            capture_output=True, text=True, timeout=120)
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or f'{executable} --bg failed')
    fields = result.stdout.split('\n')[0].split('·')
    session = fields[1].strip() if len(fields) > 1 else ''
    write_state(role, dict(role=role, provider='claude', model=ROLES[role][1],
                           status='RUNNING', time=time.time(), session=session))
    return session


def read_state(role):
    try:
        return json.loads((STATE / f'{role}.json').read_text())
    except FileNotFoundError:
        return {}


def write_state(role, data):
    target = STATE / f'{role}.json'
    temporary = STATE / f'{role}.{os.getpid()}.tmp'
    temporary.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n')
    temporary.replace(target)


def lock_held(role):
    with (STATE / f'{role}.lock').open('a') as handle:
        try:
            fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            return True
        fcntl.flock(handle, fcntl.LOCK_UN)
        return False


def status_for(role, bg=None):
    data = read_state(role)
    if ROLES[role][0] == 'claude':
        if bg is None:
            bg = bg_names(shutil.which('claude') or 'claude')
        if session_name(role) in bg:
            return 'RUNNING', data
        return ('STOPPED' if data else 'NOT_STARTED'), data
    if lock_held(role):
        return 'RUNNING', data
    if data.get('status') == 'STARTING' and time.time() - data.get('time', 0) < 60:
        return 'STARTING', data
    return ('STOPPED' if data else 'NOT_STARTED'), data


def run_role(role, executable):
    STATE.mkdir(exist_ok=True, mode=0o700)
    with (STATE / f'{role}.lock').open('a') as handle:
        try:
            fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            print(f'{role}: existing session is running; no duplicate created')
            return 0
        data = dict(role=role, provider=ROLES[role][0], model=ROLES[role][1],
                    status='RUNNING', time=time.time(), supervisor_pid=os.getpid())
        write_state(role, data)
        result = 1
        process = None
        try:
            process = subprocess.Popen(command_for(role, executable), cwd=ROOT, env=clean_env())
            write_state(role, dict(data, process_pid=process.pid))
            result = process.wait()
        except KeyboardInterrupt:
            if process is not None and process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()
            result = 130
        finally:
            write_state(role, dict(data, status='STOPPED', time=time.time(), exit_code=result))
        return result


def open_terminal(role, executable):
    command = shlex.join(['env', 'TEAM_PROJECT_ROOT=' + str(PRODUCT_ROOT), sys.executable, str(Path(__file__).resolve()),
                         'run-role', role, '--executable', executable])
    # Pass the shell command as an AppleScript argument, never interpolate script source.
    script = ('on run argv\n'
              'tell application "Terminal"\n'
              'activate\n'
              'do script (item 1 of argv)\n'
              'end tell\n'
              'end run\n')
    subprocess.run(['osascript', '-e', script, command], check=True,
                   capture_output=True, text=True, timeout=20)


def launch(provider, dry_run=False):
    roles = [r for r, spec in ROLES.items() if provider == 'all' or spec[0] == provider]
    executables = {p: shutil.which(p) for p in {ROLES[r][0] for r in roles}}
    missing = [p for p, executable in executables.items() if not executable]
    if missing:
        raise RuntimeError('CLI not found in PATH: ' + ', '.join(missing))
    if dry_run:
        for role in roles:
            print(json.dumps(dict(role=role, command=command_for(role, executables[ROLES[role][0]])),
                             ensure_ascii=False))
        return 0
    if sys.platform != 'darwin' or not shutil.which('osascript'):
        raise RuntimeError('This launcher requires macOS Terminal and osascript')
    STATE.mkdir(exist_ok=True, mode=0o700)
    # A shared lock serializes setup calls from Claude and Codex.
    with (STATE / 'setup.lock').open('a') as handle:
        fcntl.flock(handle, fcntl.LOCK_EX)
        failed = []
        started = []
        for role in roles:
            status, _ = status_for(role)
            if status in ('RUNNING', 'STARTING'):
                print(f'{role}: {status}; reused')
                continue
            write_state(role, dict(status='STARTING', time=time.time()))
            try:
                if ROLES[role][0] == 'claude':
                    start_bg(role, executables['claude'])
                else:
                    open_terminal(role, executables[ROLES[role][0]])
                started.append(role)
            except (subprocess.SubprocessError, OSError) as error:
                write_state(role, dict(status='FAILED', time=time.time()))
                failed.append(role)
                print(f'{role}: launch failed: {error}', file=sys.stderr)
        windowed = [role for role in started if ROLES[role][0] != 'claude']
        deadline = time.monotonic() + 10
        while windowed and time.monotonic() < deadline:
            if all(lock_held(role) or read_state(role).get('status') == 'STOPPED' for role in windowed):
                break
            time.sleep(0.2)
        bg = bg_names(executables['claude']) if 'claude' in executables else set()
        for role in started:
            status, data = status_for(role, bg)
            session = data.get('session')
            where = f'claude attach {session}' if role == 'pm' and session else 'monitor only; contact PM'
            print(f'{role}: {status}; model={ROLES[role][1]}; {where}')
            if status != 'RUNNING':
                failed.append(role)
                print(f'  did not start: {data.get("exit_code", status)}')
        print('RUNNING means the session is alive, not that login/model access or role initialization succeeded.')
        sendable = ', '.join(session_name(r) for r, spec in ROLES.items() if spec[0] == 'claude')
        print(f'Claude roles run in the background and accept messages at {sendable}.')
        print('QA runs in a Terminal window and is not a message target. No implementation or deployment was requested.')
        return 1 if failed else 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='action', required=True)
    setup = sub.add_parser('team')
    setup.add_argument('--provider', choices=['all', 'claude', 'codex'], default='all')
    setup.add_argument('--dry-run', action='store_true')
    sub.add_parser('status')
    runner = sub.add_parser('run-role')
    runner.add_argument('role', choices=ROLES)
    runner.add_argument('--executable', required=True)
    args = parser.parse_args()
    if args.action == 'team':
        return launch(args.provider, args.dry_run)
    if args.action == 'run-role':
        return run_role(args.role, args.executable)
    if not STATE.exists():
        print('No team has been launched')
        return 0
    bg = bg_names(shutil.which('claude') or 'claude')
    for role in ROLES:
        status, data = status_for(role, bg)
        session = data.get('session')
        print(f'{role}: {status}' + (f'; claude attach {session}' if role == 'pm' and session else ''))
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except (RuntimeError, OSError, ValueError) as error:
        print(str(error), file=sys.stderr)
        sys.exit(1)
