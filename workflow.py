#!/usr/bin/env python3
"""Reusable project team monitor: init, start, team and status."""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import socket
import sys

WORKFLOW = Path(__file__).resolve().parent
sys.path.insert(0, str(WORKFLOW / 'tools/team'))
import project


def skill_targets():
    """Resolve shared skill links before any initialization changes."""
    targets = []
    for provider in ('.agents', '.claude'):
        path = WORKFLOW / provider / 'skills/setup/SKILL.md'
        try:
            target = path.resolve()
        except (OSError, RuntimeError) as error:
            raise ValueError('스킬 링크를 확인할 수 없습니다: ' + str(path)) from error
        if WORKFLOW.resolve() not in target.parents:
            raise ValueError('스킬 경로가 ai-workflow 폴더 밖을 가리킵니다: ' + str(path))
        if target.exists() and not target.is_file():
            raise ValueError('스킬 경로가 파일이 아닙니다: ' + str(path))
        targets.append(target)
    return targets


def initialize(root):
    skills = skill_targets()
    root = root.resolve()
    root.mkdir(parents=True, exist_ok=True)
    runtime = WORKFLOW / '.team-runtime'
    if runtime.is_symlink():
        raise ValueError('로컬 설정 폴더가 심볼릭 링크입니다.')
    runtime.mkdir(exist_ok=True, mode=0o700)
    runtime.chmod(0o700)
    config = json.loads(project.CONFIG.read_text()) if project.CONFIG.exists() else {}
    if config.get('layout') == 2 and Path(config['project']).resolve() != root:
        raise ValueError('이 도구 폴더는 다른 프로젝트에 연결되어 있습니다. 새 프로젝트에는 새 사본을 사용하세요.')
    if root != WORKFLOW and config.get('layout') != 2:
        # Keep the downloaded tool's example documents before installing clean
        # project documents. Never overwrite the source checkout's own docs.
        backup = runtime / 'bootstrap-backup'
        # An earlier version could fail at skill installation after already
        # creating this backup and project docs. Resume without replacing either.
        resuming = backup.exists()
        for name in ('docs', 'AGENTS.md', 'CLAUDE.md', 'MyIdea.md'):
            current = WORKFLOW / name
            if current.is_symlink():
                raise ValueError('초기화 대상에 심볼릭 링크가 있습니다: ' + str(current))
            if current.exists() and not resuming:
                backup.mkdir(exist_ok=True)
                if (backup / name).exists():
                    raise ValueError('이전 초기화 백업이 있습니다. 먼저 상태를 확인하세요.')
                shutil.move(str(current), str(backup / name))
    created = []
    for source in sorted((WORKFLOW / 'templates/project').rglob('*')):
        if not source.is_file():
            continue
        target = WORKFLOW / source.relative_to(WORKFLOW / 'templates/project')
        if any(p.is_symlink() for p in [target, *target.parents] if p == WORKFLOW or WORKFLOW in p.parents):
            raise ValueError('초기화 대상에 심볼릭 링크가 있습니다: ' + str(target))
        if target.exists():
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        text = source.read_text().replace('vive-', project.session_prefix(root) + '-')
        if root != WORKFLOW:
            text = text.replace('/app', str(root / 'app')).replace('/backend', str(root / 'backend'))
        target.write_text(text)
        created.append(target.relative_to(WORKFLOW).as_posix())
    for name in ('app', 'backend'):
        (root / name).mkdir(exist_ok=True)
    ignore = WORKFLOW / '.gitignore'
    if ignore.is_symlink():
        raise ValueError('.gitignore 심볼릭 링크는 수정하지 않습니다.')
    content = ignore.read_text() if ignore.exists() else ''
    for line in ('/.team-runtime/', '/.claude/worktrees/', '/.workflow-project.json'):
        if line not in content.splitlines():
            content = content.rstrip() + '\n' + line + '\n'
    ignore.write_text(content)
    for target in skills:
        if not target.exists():
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text('---\nname: setup\ndescription: 팀 세션 초기화\n---\n\n'
                              'ai-workflow 작업 경로에서 `python3 workflow.py team`을 실행한다.\n'
                              '팀 초기화만 수행하며 기능 구현·Commit·배포는 요청하지 않는다.\n')
    project.CONFIG.write_text(json.dumps({'project': str(root), 'layout': 2}, ensure_ascii=False) + '\n')
    print(f'Project: {root}\nWorkflow: {WORKFLOW}\n협업 파일은 도구 폴더 내부에만 저장합니다. 새 문서 {len(created)}개.', flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['init', 'start', 'team', 'status'])
    parser.add_argument('--project', type=Path)
    parser.add_argument('--port', type=int, default=8765)
    parser.add_argument('--provider', choices=['all', 'claude', 'codex'], default='all')
    parser.add_argument('--dry-run', action='store_true')
    parser.add_argument('--monitor-only', action='store_true', help='팀 초기화 없이 모니터만 실행')
    args = parser.parse_args()
    if args.dry_run and args.action != 'team':
        parser.error('--dry-run은 team 명령에서만 사용할 수 있습니다.')
    root = args.project.expanduser().resolve() if args.project else project.root()
    if not args.project and not project.CONFIG.exists() and WORKFLOW.name in ('workflow', 'ai-workflow'):
        root = WORKFLOW.parent
    if args.action in ('init', 'start'):
        initialize(root)
    os.environ['TEAM_PROJECT_ROOT'] = str(root)
    if args.action == 'init':
        return
    if args.action == 'start' and not args.monitor_only:
        # Fail before starting roles when another monitor already owns the port.
        with socket.socket() as probe:
            probe.bind(('127.0.0.1', args.port))
        result = subprocess.run([sys.executable, str(WORKFLOW / 'tools/team/launch.py'),
                                 'team', '--provider', args.provider], cwd=WORKFLOW)
        if result.returncode:
            print('일부 역할을 시작하지 못했습니다. 모니터에서 상태를 확인하세요.', flush=True)
    script = 'dashboard.py' if args.action == 'start' else 'launch.py'
    tail = ['--port', str(args.port)] if args.action == 'start' else [args.action]
    if args.action == 'team':
        tail += ['--provider', args.provider]
        if args.dry_run:
            tail.append('--dry-run')
    os.execv(sys.executable, [sys.executable, str(WORKFLOW / 'tools/team' / script), *tail])


if __name__ == '__main__':
    try:
        main()
    except (OSError, ValueError) as error:
        sys.exit(str(error))
