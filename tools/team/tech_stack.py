"""The shared Markdown document is the only source of truth for stack settings."""
import documents
import launch

PATH = 'docs/architecture/TECH_STACK.md'


def read(path=PATH, default=None):
    try:
        return documents.read(path)
    except FileNotFoundError:
        return dict(path=path, revision='', content=default or '# 프로젝트 기술스택\n\n## Frontend\n미정\n\n## Backend\n미정\n\n## App\n미정\n\n## 공통 환경\n미정\n', updated=0)


def save(body, path=PATH):
    content = body.get('content')
    if not isinstance(content, str) or len(content.encode()) > 50000:
        raise ValueError('문서는 50KB 이하로 입력하세요.')
    with documents.LOCK:
        target = launch.ROOT / path
        if any(p.is_symlink() for p in (target, target.parent, target.parent.parent)):
            raise ValueError('공용 문서의 링크 경로는 저장할 수 없습니다.')
        if not target.exists():
            if body.get('revision') != '':
                raise RuntimeError('공용 문서가 변경되었습니다. 다시 불러오세요.')
            target.parent.mkdir(parents=True, exist_ok=True)
            try:
                with target.open('x', encoding='utf-8') as handle:
                    handle.write(content)
            except FileExistsError:
                raise RuntimeError('공용 문서가 생성되었습니다. 다시 불러오세요.')
            return read(path)
        return documents.save(dict(path=path,content=content,revision=body.get('revision')))
