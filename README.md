# 프로젝트별 AI Workflow

각 프로젝트 안에 이 저장소를 `ai-workflow`로 클론해 PM 대화, 역할 상태와 로그, 프로젝트 문서, URL·시크릿·토큰 기록을 한 화면에서 확인합니다. Python 3.9 이상과 macOS, 사용 중인 Claude Code·Codex CLI가 필요합니다. 프론트엔드 빌드나 npm 설치는 필요하지 않습니다.

```text
todo/
├── ai-workflow/       # 모니터·문서·규칙·설정·로그 전체
├── app/          # 제품 프론트엔드
└── backend/           # 제품 백엔드
```

## 복사하고 한 번에 실행

새 프로젝트 폴더에 이 저장소를 `ai-workflow`라는 이름으로 복사하거나 클론합니다.

```bash
mkdir todo
cd todo
git clone https://github.com/JeongHyck06/ai-workflow.git ai-workflow
python3 ai-workflow/workflow.py start
```

`start`는 `app`·`backend` 폴더 준비 → 팀 세션 초기화 → 모니터 실행을 순서대로 처리합니다. [Team Monitor](http://127.0.0.1:8765/)에서 PM → PM 연결을 누릅니다. 기능 구현은 PM에게 요구사항을 전달한 뒤 시작합니다. 제품 Git 저장소 생성·Commit·Push·PR·배포는 자동 수행하지 않습니다.

`docs`, `.agents`, `.claude`, `.team-runtime`, `AGENTS.md`, `CLAUDE.md`, `.gitignore`는 **ai-workflow 안에서만** 관리합니다. 제품 루트에 복사하지 않습니다. 팀 CLI도 ai-workflow를 작업 경로로 사용하며, 제품 코드는 상위 `app`·`backend`에 작성하도록 경로를 전달합니다. Git·Figma·배포 URL은 제품 프로젝트의 설정입니다.

처음 사용할 때 다운로드한 도구의 예제 문서는 `ai-workflow/.team-runtime/bootstrap-backup`에 보존하고 깨끗한 프로젝트 템플릿을 설치합니다. 이후 초기화는 실제 프로젝트 문서·PR 규칙을 덮어쓰지 않습니다. 기존 버전이 제품 루트에 생성했던 파일은 이 명령이 자동 삭제하거나 이동하지 않습니다.

`ai-workflow` 또는 `workflow` 폴더 이름에서는 기본 제품 경로가 상위 폴더입니다. 다른 이름으로 복사했다면 첫 실행에 `--project .`를 지정하세요. 경로는 도구 내부 `.workflow-project.json`에 저장됩니다. 초기화가 끝난 도구 사본을 다른 프로젝트에 재사용하지 말고 새 사본을 복사하세요.

## 실행 옵션

```bash
# 다른 모니터와 동시에 실행
python3 ai-workflow/workflow.py start --port 8766
# 팀을 시작하지 않고 모니터만 실행
python3 ai-workflow/workflow.py start --monitor-only
# 팀 상태 확인
python3 ai-workflow/workflow.py status
# 실행할 역할 명령만 확인
python3 ai-workflow/workflow.py team --dry-run
```

팀 초기화만 다시 실행하려면 `python3 ai-workflow/workflow.py team`을 사용합니다. 스킬을 사용할 경우에는 제품 루트가 아닌 **ai-workflow 안에서** Claude의 `/setup team` 또는 Codex의 `$setup team`을 실행합니다. 사용자의 대화 창구는 PM뿐입니다. QA 로그 조회는 지원하며 PM↔QA 자동 메시지 중계는 별도 기능입니다.

역할 이름에는 제품 경로 해시가 포함되어 같은 이름의 프로젝트도 구분합니다. 팀 상태와 사용량은 해당 도구 작업 경로의 세션을 조회합니다. 시크릿과 런타임 파일은 도구의 `.gitignore`에서 제외합니다.

## 프로젝트 관리

- **프로젝트 URL**: Git, Figma, 배포 URL을 저장하고 엽니다. Git은 현재 프로젝트의 `origin`에서 기본값을 읽습니다. 인증정보가 포함된 URL은 허용하지 않습니다.
- **시크릿 키**: `ai-workflow/.team-runtime/resources.json`에 로컬로 저장합니다. 디렉터리는 700, 파일은 600 권한이며 Git에서 제외됩니다. 암호화 저장소가 아니라 평문 로컬 파일입니다. 기본 목록에는 값이 전달되지 않고, 표시 요청 때만 값을 조회합니다. 30초 후, 탭 전환 또는 창을 닫으면 표시를 지웁니다. 앱 환경 변수나 모델 입력으로 자동 전달하지 않습니다.
- **토큰 사용량**: 프로젝트의 로컬 Claude·Codex 기록을 집계합니다. 입력·출력·캐시 읽기를 구분하고, 동일 Claude 메시지의 반복 기록은 한 번만 셉니다. Codex는 각 세션의 마지막 누적값을 사용합니다. 계정 잔여 한도·청구 금액이 아니며, 미수집 기록을 0으로 간주하지 않습니다. Claude 작업 트리는 포함하며 하위 에이전트, 다른 호스트, Codex 보관 세션은 제외합니다.
- **프로젝트 문서**: 상단 버튼에서 기획, Issue, 커밋·PR 규칙, 디자인 시스템 등을 조회합니다.

서버는 `127.0.0.1`에만 바인딩됩니다. 시크릿 변경·표시와 PM 입력에는 동일 Origin 및 실행마다 바뀌는 토큰이 필요합니다.

## 협업 규칙과 검증

새 프로젝트의 기본 [커밋·PR 규칙](templates/project/docs/agents/GIT.md)은 기존 규칙과 동일합니다. QA_PASSED → PM의 READY_FOR_PR 확인 → Commit·Push·PR 순서를 유지합니다. 초기 문서의 원본은 `templates/project`이며 이 도구 개발 이슈나 프로젝트별 Figma 링크는 복사하지 않습니다.

```bash
python3 -m unittest discover -s tools/team -p 'test_*.py'
```

Codex 기록 조회는 [공식 App Server API](https://learn.chatgpt.com/docs/app-server)의 `thread/list`와 `thread/read`를 사용합니다. 조회용 프로세스는 모델 대화를 시작하거나 재개하지 않습니다.
