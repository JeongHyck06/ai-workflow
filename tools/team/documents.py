"""Serve only project documentation, never arbitrary workspace files."""
from pathlib import Path
import re
import launch

GROUPS = {'product': '기획·디자인', 'issues': 'Issue', 'architecture': '기술 설계',
          'agents': '역할·운영 규칙', 'qa': 'QA', 'domains': 'Domain'}
LABELS = {'docs/agents/GIT.md': '커밋·PR·Git 규칙',
          'docs/product/DESIGN_SYSTEM.md': '디자인 시스템',
          'docs/product/REQUIREMENTS.md': '요구사항',
          'docs/product/FEATURES.md': '기능 목록',
          'docs/product/USER_FLOW.md': '사용자 흐름',
          'docs/issues/ACTIVE.md': '진행 Issue',
          'docs/issues/DONE.md': '완료 Issue',
          'docs/README.md': '프로젝트 안내·협업 규칙'}


def files():
    root = launch.ROOT.resolve()
    result = {}
    for path in sorted((root / 'docs').rglob('*.md')):
        if path.is_symlink() or (root / 'docs') not in path.resolve().parents:
            continue
        if path.is_file():
            result[path.relative_to(root).as_posix()] = path
    idea = root / 'MyIdea.md'
    if idea.is_file() and not idea.is_symlink():
        result['MyIdea.md'] = idea
    return result


def read(path):
    target = files().get(path)
    if target is None:
        raise FileNotFoundError(path)
    if target.stat().st_size > 1_000_000:
        raise ValueError('문서 크기가 표시 한도를 초과했습니다.')
    return dict(path=path, content=target.read_text(encoding='utf-8'),
                updated=target.stat().st_mtime)


def index():
    result = []
    for path, target in files().items():
        parts = Path(path).parts
        group = GROUPS.get(parts[1], '프로젝트 안내') if len(parts) > 2 else '프로젝트 안내'
        with target.open(encoding='utf-8') as handle:
            first = handle.readline().strip()
        title = LABELS.get(path, re.sub(r'^#+\s*', '', first) or target.stem)
        if path == 'MyIdea.md':
            title = '아이디어 메모 (미확정)'
        result.append(dict(path=path, title=title, group=group, updated=target.stat().st_mtime))
    return result
