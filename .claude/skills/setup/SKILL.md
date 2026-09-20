---
name: setup
description: 팀 세션 시작. `/setup team`(Claude Code) 또는 `$setup team`(Codex/Astra) 입력 시 6개 역할 CLI 세션을 macOS Terminal에 연다. 세션 초기화 전용이며 기능 구현·Commit·배포는 포함하지 않는다.
---

# 팀 세션 시작

프로젝트 루트에서 아래를 실행하고 출력을 그대로 보고한다. 기본값은 Claude와 Codex 역할을 한 번에 시작한다.

```bash
python3 tools/team/launch.py team
```

| 상황 | 명령 |
| --- | --- |
| 실행 없이 각 역할 명령 확인 | `python3 tools/team/launch.py team --dry-run` |
| 한쪽 도구만 시작 | `python3 tools/team/launch.py team --provider claude` 또는 `--provider codex` |
| 역할별 상태 확인 | `python3 tools/team/launch.py status` |

- 역할·모델 매핑의 원본은 `tools/team/launch.py`다. 이 문서에 복제하지 않는다.
- 실행 중인 역할은 재사용되므로 재호출하지 않는다. 실패한 역할만 다시 실행한다.
- RUNNING은 CLI 프로세스 생존만 뜻한다. 로그인·모델 권한·역할 준비는 각 Terminal 응답으로 확인한다.
- 이 명령은 세션 생성과 초기 지시 전달까지다. 요구사항·Issue를 만들거나 기능 구현, Git 변경, 배포를 시작하지 않는다.

준비 조건과 문제 해결은 [TEAM_SETUP](../../../docs/agents/TEAM_SETUP.md)를 따른다.
