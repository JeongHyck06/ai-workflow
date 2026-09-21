"""Serve only project documentation, never arbitrary workspace files."""
from pathlib import Path
import re
import hashlib
import threading
import os
import tempfile

LOCK = threading.RLock()
import launch

GROUPS = {'product': '기획·디자인', 'issues': 'Issue', 'architecture': '기술 설계',
          'agents': '역할·운영 규칙', 'qa': 'QA', 'domains': 'Domain'}
LABELS = {'docs/product/DESIGN_PROMPT.md': '디자인 프롬프트', 'docs/architecture/TECH_STACK.md': '기술스택', 'docs/agents/GIT.md': '커밋·PR·Git 규칙',
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
    content = target.read_text(encoding='utf-8')
    return dict(path=path, content=content, revision=hashlib.sha256(content.encode()).hexdigest(),
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
        result.append(dict(path=path, title=title, group=group, updated=target.stat().st_mtime,
                           revision=hashlib.sha256(target.read_bytes()).hexdigest()))
    return result


def save(body):
    path, content, revision = body.get('path'), body.get('content'), body.get('revision')
    if not isinstance(path, str) or not isinstance(content, str) or len(content.encode()) > 1_000_000:
        raise ValueError('문서 입력 또는 크기를 확인하세요.')
    with LOCK:
        current = read(path)
        if revision != current['revision']:
            raise RuntimeError('다른 변경이 있습니다. 입력 내용을 복사한 뒤 문서를 다시 불러와 비교하세요.')
        target = files()[path]
        fd, name = tempfile.mkstemp(prefix='.document-', dir=target.parent)
        try:
            with os.fdopen(fd, 'w', encoding='utf-8') as handle:
                handle.write(content)
            os.chmod(name, target.stat().st_mode & 0o777)
            if read(path)['revision'] != revision:
                raise RuntimeError('저장 중 문서가 변경되었습니다. 다시 확인하세요.')
            os.replace(name, target)
        finally:
            if os.path.exists(name):
                os.unlink(name)
        return read(path)
