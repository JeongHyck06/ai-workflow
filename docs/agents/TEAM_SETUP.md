# 팀 세션 시작

## 실행

프로젝트 루트에서 시작한 세션에 입력한다.

- Claude Code: `/setup team`
- Astra를 선택한 Codex: `$setup team` — 공식 스킬 호출 문법
- Codex가 `/setup`을 인식하지 않는 경우 `$setup team`을 사용한다. 이 설정은 Codex의 내장 슬래시 명령 파서를 변경하지 않는다.

두 진입점은 같은 실행기를 호출한다. 어느 쪽에서 먼저 실행해도 아래 6개 역할의 독립 CLI 세션을 macOS Terminal에 연다. 두 번째 호출은 실행 중인 역할을 재사용한다. 명령을 입력한 기존 세션은 실행 관리용이며 별도의 역할로 중복 배정하지 않는다.

| 역할 | 실행 도구 | 지정 모델 |
| --- | --- | --- |
| PM | Claude Code | fable |
| Frontend | Claude Code | opus |
| Backend | Claude Code | opus |
| QA | Codex | gpt-6-astra |
| Git Manager | Claude Code | sonnet |
| DevOps | Claude Code | fable |

역할·모델 매핑의 실행 원본은 `tools/team/launch.py`다. 역할의 권한과 책임은 각 역할 문서를 따른다. 사용 불가능한 모델을 다른 모델로 자동 대체하지 않는다.

## 준비 조건

- macOS, Python 3, Terminal, PATH에서 찾을 수 있는 `claude`와 `codex`
- 각 CLI 로그인과 해당 모델 사용 권한
- 명령·스킬이 보이지 않으면 프로젝트 루트에서 새 세션을 시작한다.
- Terminal 실행 시 OS 자동화 권한 또는 호스트 실행 승인이 필요할 수 있다. 실행기는 권한 검사를 우회하지 않는다.

## 동작과 상태 확인

각 세션은 진입점·자신의 역할·ACTIVE를 읽고 준비 상태를 보고한 뒤 다음 입력을 기다린다. 미정 요구사항을 채우거나 기능 구현, Git 변경, 배포를 자동으로 시작하지 않는다.

```bash
python3 tools/team/launch.py status
python3 tools/team/launch.py team --dry-run
```

명령을 제공하는 스킬이 없는 환경에서도 `python3 tools/team/launch.py team`으로 동일하게 시작할 수 있다. 특정 도구만 시작할 때는 `--provider claude` 또는 `--provider codex`를 사용한다.

- `.team-runtime/`은 로컬 프로세스 식별·중복 실행 방지 정보다. 프로젝트 설계·Issue 상태는 저장하지 않으며 Git에서 제외한다.
- RUNNING은 CLI 프로세스 생존만 뜻한다. 로그인 성공·모델 사용 가능·역할 준비 완료는 각 Terminal의 실제 응답으로 확인한다.
- STARTING은 실행 대기다. 60초 뒤에도 시작되지 않으면 Terminal 오류를 확인하고 재실행한다.
- 역할별 잠금으로 동시 호출의 중복 실행을 막는다. 종료된 역할만 다음 호출에서 새로 시작한다.
- 세션 종료는 해당 Terminal에서 CLI의 종료 명령을 사용한다. 이전 대화의 자동 복원은 하지 않으며 새 세션은 `/docs`에서 재개한다.

## 협업 범위

이 명령은 역할 세션 생성과 초기 지시 전달을 자동화한다. 서로 다른 CLI 사이의 지속적인 메시지 전달·완료 감지·자동 재할당 데몬은 포함하지 않는다. 현재는 PM이 문서에 할당·인계를 기록하고 해당 역할 세션에 후속 입력을 전달해야 작업이 시작된다. 문서 변경만으로 대기 중인 세션이 자동으로 깨어나지는 않는다.

## 참고

- [Claude 사용자 스킬](https://code.claude.com/docs/en/skills)
- [Codex 스킬 생성·호출](https://learn.chatgpt.com/docs/build-skills)

확인 기준: 로컬 Claude Code 2.1.275, Codex CLI 0.154.0-alpha.6.2
