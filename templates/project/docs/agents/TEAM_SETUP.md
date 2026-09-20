# 팀 세션 시작

## 실행

프로젝트 루트에서 시작한 세션에 입력한다.

- Claude Code: `/setup team`
- Astra를 선택한 Codex: `$setup team` — 공식 스킬 호출 문법
- Codex가 `/setup`을 인식하지 않는 경우 `$setup team`을 사용한다. 이 설정은 Codex의 내장 슬래시 명령 파서를 변경하지 않는다.

두 진입점은 같은 실행기를 호출한다. 어느 쪽에서 먼저 실행해도 아래 역할 세션을 시작한다. Claude 역할은 background 세션으로 뜨고 창이 없다. QA는 Codex라 macOS Terminal 창으로 뜬다. 두 번째 호출은 실행 중인 역할을 재사용한다. 명령을 입력한 기존 세션은 실행 관리용이며 별도의 역할로 중복 배정하지 않는다.

| 역할 | 실행 도구 | 지정 모델 |
| --- | --- | --- |
| PM | Claude Code | fable |
| Designer | Claude Code | opus |
| Frontend | Claude Code | opus |
| Backend | Claude Code | opus |
| QA | Codex | gpt-6-astra |
| Git Manager | Claude Code | sonnet |
| DevOps | Claude Code | fable |

역할·모델 매핑의 실행 원본은 `workflow/tools/team/launch.py`다. 역할의 권한과 책임은 각 역할 문서를 따른다. 사용 불가능한 모델을 다른 모델로 자동 대체하지 않는다.

## 준비 조건

- macOS, Python 3, PATH에서 찾을 수 있는 `claude`와 `codex`. Terminal 창은 QA 세션에만 쓴다.
- 각 CLI 로그인과 해당 모델 사용 권한
- 명령·스킬이 보이지 않으면 프로젝트 루트에서 새 세션을 시작한다.
- Terminal 실행 시 OS 자동화 권한 또는 호스트 실행 승인이 필요할 수 있다. 실행기는 권한 검사를 우회하지 않는다.

## 동작과 상태 확인

각 세션은 진입점·자신의 역할·ACTIVE를 읽고 준비 상태를 보고한 뒤 다음 입력을 기다린다. 미정 요구사항을 채우거나 기능 구현, Git 변경, 배포를 자동으로 시작하지 않는다.

```bash
python3 workflow/workflow.py status
python3 workflow/workflow.py team --dry-run
claude agents            # 살아 있는 background 세션 목록
claude attach <id>       # 해당 역할 세션을 이 터미널에서 열기
claude logs <id>         # 해당 역할의 최근 출력만 보기
claude stop <id>         # 해당 역할 종료
```

명령을 제공하는 스킬이 없는 환경에서도 `python3 workflow/workflow.py team`으로 동일하게 시작할 수 있다. 특정 도구만 시작할 때는 `--provider claude` 또는 `--provider codex`를 사용한다.

- `.team-runtime/`은 로컬 프로세스 식별·중복 실행 방지 정보다. 프로젝트 설계·Issue 상태는 저장하지 않으며 Git에서 제외한다.
- RUNNING은 세션 생존만 뜻한다. 로그인 성공·모델 사용 가능·역할 준비 완료는 `claude logs <id>`와 QA Terminal의 실제 응답으로 확인한다.
- STARTING은 실행 대기다. 60초 뒤에도 시작되지 않으면 `claude logs <id>` 또는 Terminal 오류를 확인하고 재실행한다.
- 역할별 잠금으로 동시 호출의 중복 실행을 막는다. 종료된 역할만 다음 호출에서 새로 시작한다.
- 세션 종료는 Claude 역할은 `claude stop <id>`, QA는 해당 Terminal의 종료 명령을 사용한다. 이전 대화의 자동 복원은 하지 않으며 새 세션은 `/docs`에서 재개한다.

## 협업 범위

Claude 역할 세션은 서로 이름으로 메시지를 주고받는다. 이름은 `vive-<role>`이며 PM이 담당 역할에 직접 할당을 전달할 수 있다.

- 메시지 대상: `vive-pm`, `vive-design`, `vive-frontend`, `vive-backend`, `vive-git`, `vive-devops`
- QA는 Codex라 이 통신망 밖이다. QA 전달과 결과 회수는 PM 책임이다. 현재 연결 부재는 차단 사유이며 사용자에게 중계를 요구하지 않는다.
- background 세션만 대상으로 등록된다. Terminal 창으로 띄운 Claude 세션은 이름이 있어도 도달하지 않는다.

문서 변경만으로 대기 중인 세션이 깨어나지는 않는다. 상태 기록은 문서에 남기고, 실행을 시작시키는 것은 메시지다. 완료 감지·자동 재할당 데몬은 없으므로 각 역할은 작업이 끝나면 요청한 역할에 결과를 회신한다.

## 참고

- [Claude 사용자 스킬](https://code.claude.com/docs/en/skills)
- [Codex 스킬 생성·호출](https://learn.chatgpt.com/docs/build-skills)

확인 기준: 로컬 Claude Code 2.1.275, Codex CLI 0.154.0-alpha.6.2

## 로컬 웹 모니터

```bash
python3 workflow/workflow.py start
```

[Team Monitor](http://127.0.0.1:8765)에서 역할 상태, Claude 최근 출력, 진행 Issue를 확인한다. `--port 8766`으로 포트를 변경할 수 있다. Python 표준 라이브러리만 사용한다.

- 5초 자동 조회, 역할 선택, 갱신 일시정지, 수동 새로고침, PM 접속 명령 복사 지원.
- Claude 세션은 현재 프로젝트 경로와 역할 이름으로 제한한다. 조회 실패는 `확인 불가`로 표시한다.
- QA는 Codex에 저장된 대화·명령 실행 기록을 읽기 전용으로 조회한다. 같은 프로젝트의 QA 초기화 문구로 식별한 최신 세션만 표시하며, 역할의 실행 상태는 실행기 잠금으로 따로 확인한다. 종료된 세션도 마지막 기록을 볼 수 있다.
- 조회는 `codex app-server --listen stdio://`의 `thread/list`·`thread/read` API를 사용한다. 모델 세션을 생성하거나 재개하지 않는다. 저장 전 출력은 다음 갱신에 반영되며 QA 메시지 전송·PM 자동 중계는 별도 기능이다.
- PM은 웹의 `PM 연결` 버튼으로 대화한다. 다른 역할은 관찰 전용이다. 서버 종료 시 웹 연결만 닫고 팀 세션은 유지한다.
- 127.0.0.1에만 바인딩한다. 외부 공개용이 아니다. 로그는 로컬 브라우저에 전달하고 별도 저장하지 않는다.
- 설계·검증 기록: [ISSUE-0001](../issues/ACTIVE.md#issue-0001)

### PM 웹 대화 (2026-09-21)

- PM 선택 → PM 연결 → 하단 입력창에서 전송. Enter는 전송, Shift+Enter는 줄바꿈이며 한글 조합 중 Enter는 전송하지 않는다.
- 기존 `vive-pm` background 세션에 PTY로 attach한다. 프로젝트 내부 `.claude/worktrees`로 이동한 PM도 연결한다. PM이 없거나 여러 개면 자동 생성·선택하지 않고 오류를 표시한다.
- 기존 CLI 권한 요청은 웹 터미널에 그대로 표시된다. 사용자가 화면 안에서 직접 선택하며 승인 절차를 자동 처리하지 않는다.
- 브라우저 높이 안에 화면을 고정하고 대화·역할 목록·Issue는 내부 스크롤을 사용한다. 좁은 화면에서는 Issue를 숨긴다.
- POST 입력은 Host, 동일 Origin, 서버별 토큰을 검증한다. 대상은 PM뿐이며 임의 명령·실행 파일·세션 선택을 받지 않는다.
- 탭당 attach 연결, 최대 4개, 60초 비활성 연결 정리. 재연결 때 메시지를 자동 재전송하지 않는다.
- 웹 터미널 라이브러리: @xterm/xterm 5.5.0, @xterm/addon-fit 0.10.0. 배포 파일과 라이선스는 tools/team/web/vendor에 보관하며 CDN 없이 로컬 제공한다.

### 프로젝트 문서 창

- 상단 `프로젝트 문서` 버튼으로 연다. 오른쪽에는 프로젝트 URL·시크릿·토큰 관리 버튼이 있다.
- docs 아래 Markdown과 MyIdea.md를 분류해서 표시한다. MyIdea는 미확정 메모로 표시한다. 제목·파일명·분류 검색, 수정 시각, 새로고침, 내부 문서 링크를 지원한다.
- 읽기 전용이며 실제 원본 파일을 조회한다. HTML은 실행하지 않고 이미지 자동 로드를 사용하지 않는다. 문서 폴더 밖 경로와 심볼릭 링크는 제공하지 않는다.
- Markdown 렌더러: markdown-it 14.1.0, vendor에 배포본 및 라이선스 보관.
