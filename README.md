# 프로젝트별 AI Workflow

각 프로젝트 안에 이 저장소를 `workflow`로 클론해 PM 대화, 역할 상태와 로그, 프로젝트 문서, URL·시크릿·토큰 기록을 한 화면에서 확인합니다. Python 3.9 이상과 macOS, 사용 중인 Claude Code·Codex CLI가 필요합니다. 프론트엔드 빌드나 npm 설치는 필요하지 않습니다.

```text
todo/
├── workflow/          # 이 저장소를 클론한 도구
├── app/               # 제품 프론트엔드
├── backend/           # 제품 백엔드
├── docs/              # 이 프로젝트의 문서와 PR 규칙
├── AGENTS.md
├── CLAUDE.md
└── .team-runtime/     # 로컬 설정·시크릿·팀 상태, Git 제외
```

## 클론하고 실행

새 프로젝트 폴더에서 실행합니다.

```bash
mkdir todo
cd todo
git clone https://github.com/JeongHyck06/ai-workflow.git workflow
python3 workflow/workflow.py start --project .
```

[Team Monitor](http://127.0.0.1:8765/)를 엽니다. 첫 실행은 문서 템플릿과 `app`·`backend`를 준비합니다. 이미 존재하는 문서·코드·PR 규칙은 덮어쓰지 않습니다. 제품 코드나 모델 세션을 자동 생성하지 않습니다.

다음 실행부터는 `cd workflow` 후 `python3 workflow.py start`만 실행하면 됩니다. 지정한 프로젝트는 이 클론의 `.workflow-project.json`에 저장되며 Git에서 제외됩니다. 도구와 프로젝트를 다른 위치로 옮겼다면 `--project`를 다시 지정하세요. 별도 설정이 없는 `workflow` 폴더에서는 상위 폴더를 기본 프로젝트로 사용합니다. 기존 저장소 루트에서 `python3 tools/team/dashboard.py`로 실행하는 방식도 유지됩니다.

## 팀 초기화와 프로젝트 분리

모니터와 팀 초기화는 별도 명령입니다. 팀 시작이 필요할 때:

```bash
python3 workflow/workflow.py team --project .
python3 workflow/workflow.py status --project .
# 실제 실행 전 명령 확인
python3 workflow/workflow.py team --project . --dry-run
```

프로젝트 루트에서 Claude의 `/setup team`, Codex의 `$setup team`도 사용할 수 있도록 초기화 시 스킬을 설치합니다. 기존 스킬은 보존합니다. 사용자와 소통하는 역할은 PM뿐이며, 다른 역할은 읽기 전용으로 관찰합니다. QA 로그 조회는 연결되어 있지만 PM↔QA 자동 메시지 중계는 별도 기능입니다.

동시에 다른 프로젝트를 열려면 다른 포트를 지정합니다.

```bash
python3 /path/to/another/workflow/workflow.py start --project /path/to/another --port 8766
```

역할 세션·문서·로컬 설정·사용량은 지정한 프로젝트 경로로 구분합니다. 새 프로젝트의 역할 이름에는 프로젝트 경로 해시를 포함해 이름이 같은 프로젝트도 구분합니다. 제품 저장소에서 도구를 따로 관리하려면 `/workflow/`를 제품 `.gitignore`에 추가하거나 submodule로 관리할 수 있습니다. 초기화는 제품 Git 저장소 생성이나 원격 연결, Commit·Push·PR을 수행하지 않습니다.

## 프로젝트 관리

- **프로젝트 URL**: Git, Figma, 배포 URL을 저장하고 엽니다. Git은 현재 프로젝트의 `origin`에서 기본값을 읽습니다. 인증정보가 포함된 URL은 허용하지 않습니다.
- **시크릿 키**: `.team-runtime/resources.json`에 로컬로 저장합니다. 디렉터리는 700, 파일은 600 권한이며 Git에서 제외됩니다. 암호화 저장소가 아니라 평문 로컬 파일입니다. 기본 목록에는 값이 전달되지 않고, 표시 요청 때만 값을 조회합니다. 30초 후, 탭 전환 또는 창을 닫으면 표시를 지웁니다. 앱 환경 변수나 모델 입력으로 자동 전달하지 않습니다.
- **토큰 사용량**: 프로젝트의 로컬 Claude·Codex 기록을 집계합니다. 입력·출력·캐시 읽기를 구분하고, 동일 Claude 메시지의 반복 기록은 한 번만 셉니다. Codex는 각 세션의 마지막 누적값을 사용합니다. 계정 잔여 한도·청구 금액이 아니며, 미수집 기록을 0으로 간주하지 않습니다. Claude 작업 트리는 포함하며 하위 에이전트, 다른 호스트, Codex 보관 세션은 제외합니다.
- **프로젝트 문서**: 상단 버튼에서 기획, Issue, 커밋·PR 규칙, 디자인 시스템 등을 조회합니다.

서버는 `127.0.0.1`에만 바인딩됩니다. 시크릿 변경·표시와 PM 입력에는 동일 Origin 및 실행마다 바뀌는 토큰이 필요합니다.

## 협업 규칙과 검증

새 프로젝트의 기본 [커밋·PR 규칙](templates/project/docs/agents/GIT.md)은 기존 규칙과 동일합니다. QA_PASSED → PM의 READY_FOR_PR 확인 → Commit·Push·PR 순서를 유지합니다. 초기 문서의 원본은 `templates/project`이며 이 도구 개발 이슈나 프로젝트별 Figma 링크는 복사하지 않습니다.

```bash
python3 -m unittest discover -s tools/team -p 'test_*.py'
```

Codex 기록 조회는 [공식 App Server API](https://learn.chatgpt.com/docs/app-server)의 `thread/list`와 `thread/read`를 사용합니다. 조회용 프로세스는 모델 대화를 시작하거나 재개하지 않습니다.
