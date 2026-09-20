#!/usr/bin/env python3
"""Reusable project team monitor: init, start, team and status."""
import argparse
import json
import os
from pathlib import Path
import shlex
import sys

WORKFLOW = Path(__file__).resolve().parent
sys.path.insert(0, str(WORKFLOW / 'tools/team'))
import project


def initialize(root):
    root = root.resolve()
    root.mkdir(parents=True, exist_ok=True)
    created = []
    for source in sorted((WORKFLOW / 'templates/project').rglob('*')):
        if not source.is_file():
            continue
        target = root / source.relative_to(WORKFLOW / 'templates/project')
        if target.exists():
            continue
        # Never follow an existing directory symlink while initializing a project.
        if any(parent.is_symlink() for parent in [target, *target.parents] if parent == root or root in parent.parents):
            raise ValueError('초기화 대상에 심볼릭 링크가 있습니다: ' + str(target))
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(source.read_text().replace('vive-', project.session_prefix(root) + '-'))
        created.append(target.relative_to(root).as_posix())
    for name in ('app', 'backend'):
        (root / name).mkdir(exist_ok=True)
    runtime = root / '.team-runtime'
    if runtime.is_symlink():
        raise ValueError('로컬 설정 폴더가 심볼릭 링크입니다.')
    runtime.mkdir(exist_ok=True, mode=0o700)
    runtime.chmod(0o700)
    ignore = root / '.gitignore'
    if ignore.is_symlink():
        raise ValueError('.gitignore 심볼릭 링크는 수정하지 않습니다.')
    content = ignore.read_text() if ignore.exists() else ''
    for line in ('/.team-runtime/', '/.claude/worktrees/'):
        if line not in content.splitlines():
            content = content.rstrip() + '\n' + line + '\n'
    ignore.write_text(content)
    # A wrapper uses an absolute path so spaces and alternate clone names work.
    command = shlex.join(['python3', str(WORKFLOW / 'workflow.py'), 'team', '--project', str(root)])
    for provider in ('.agents', '.claude'):
        target = root / provider / 'skills/setup/SKILL.md'
        if target.exists():
            continue
        if any(parent.is_symlink() for parent in target.parents if root in parent.parents):
            raise ValueError('스킬 경로의 심볼릭 링크는 허용되지 않습니다.')
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text('---\nname: setup\ndescription: 프로젝트 팀 초기화 전용\n---\n\n'
                          '# 팀 세션 시작\n\n아래 명령으로 팀만 초기화한다. 기능 구현·Commit·배포 요청이 아니다.\n\n'
                          '```bash\n' + command + '\n```\n\n'
                          '실행 결과를 보고하고 docs/README.md 및 docs/agents/TEAM_SETUP.md를 따른다.\n')
    project.CONFIG.write_text(json.dumps({'project': str(root)}, ensure_ascii=False) + '\n')
    print(f'Project: {root}\n새 문서 {len(created)}개 생성. 기존 문서와 PR 규칙 유지.', flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['init', 'start', 'team', 'status'])
    parser.add_argument('--project', type=Path)
    parser.add_argument('--port', type=int, default=8765)
    parser.add_argument('--provider', choices=['all', 'claude', 'codex'], default='all')
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args()
    root = args.project.expanduser().resolve() if args.project else project.root()
    if not args.project and not project.CONFIG.exists() and WORKFLOW.name == 'workflow':
        root = WORKFLOW.parent
    if args.action in ('init', 'start'):
        initialize(root)
    os.environ['TEAM_PROJECT_ROOT'] = str(root)
    if args.action == 'init':
        return
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
