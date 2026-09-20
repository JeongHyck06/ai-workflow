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

ROOT = Path(__file__).resolve().parents[2]
STATE = ROOT / '.team-runtime'
ROLES = {
    'pm': ('claude', 'fable', 'PM'),
    'frontend': ('claude', 'opus', 'FRONTEND'),
    'backend': ('claude', 'opus', 'BACKEND'),
    'qa': ('codex', 'gpt-6-astra', 'QA'),
    'git': ('claude', 'sonnet', 'GIT'),
    'devops': ('claude', 'fable', 'DEVOPS'),
}


def prompt_for(role):
    _, model, document = ROLES[role]
    return (
        f'이 프로젝트의 {document} 역할 세션이다. 요청 모델은 {model}이다. '
        f'프로젝트 루트는 {ROOT}이다. docs/README.md, docs/agents/{document}.md, '
        'docs/issues/ACTIVE.md, docs/agents/TEAM_SETUP.md를 읽어라. '
        '이번 입력은 팀 초기화만 요청한다. 역할, 모델, 읽은 문서, 할당 Issue 유무를 보고하고 '
        '다음 입력을 기다려라. 요구사항·기술 스택·Issue를 임의로 만들거나 기능 구현, '
        'Git 변경, 배포를 시작하지 마라. 다른 세션을 추가 생성하거나 setup을 재호출하지 마라. '
        '실제 작업은 이후 PM의 명시적 할당과 사용자 요청 범위에 따라 진행한다. '
        '세션 간 공유 기록은 docs를 사용한다. 민감값을 기록하지 마라.'
    )


def command_for(role, executable):
    provider, model, _ = ROLES[role]
    if provider == 'claude':
        return [executable, '--model', model, '--name', f'vive-{role}',
                '--settings', '{"attribution":{"commit":"","pr":""}}', prompt_for(role)]
    return [executable, '--model', model, '--cd', str(ROOT), prompt_for(role)]


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


def status_for(role):
    data = read_state(role)
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
            env = os.environ.copy()
            # An independent Claude session must not inherit its caller's nesting marker.
            for key in ('CLAUDECODE', 'CLAUDE_CODE_ENTRYPOINT', 'CODEX_THREAD_ID'):
                env.pop(key, None)
            process = subprocess.Popen(command_for(role, executable), cwd=ROOT, env=env)
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
    command = shlex.join([sys.executable, str(Path(__file__).resolve()),
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
                open_terminal(role, executables[ROLES[role][0]])
                started.append(role)
            except (subprocess.SubprocessError, OSError) as error:
                write_state(role, dict(status='FAILED', time=time.time()))
                failed.append(role)
                print(f'{role}: launch failed: {error}', file=sys.stderr)
        deadline = time.monotonic() + 10
        while started and time.monotonic() < deadline:
            if all(lock_held(role) or read_state(role).get('status') == 'STOPPED' for role in started):
                break
            time.sleep(0.2)
        for role in started:
            status, data = status_for(role)
            print(f'{role}: {status}; model={ROLES[role][1]}')
            if status == 'STOPPED':
                failed.append(role)
                print(f'  CLI exited: {data.get("exit_code")}; inspect its Terminal window')
        print('RUNNING means the CLI process is alive, not that login/model access or role initialization succeeded.')
        print('Check each Terminal for the role readiness response. No implementation or deployment was requested.')
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
    for role in ROLES:
        print(f'{role}: {status_for(role)[0]}')
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except (RuntimeError, OSError, ValueError) as error:
        print(str(error), file=sys.stderr)
        sys.exit(1)
