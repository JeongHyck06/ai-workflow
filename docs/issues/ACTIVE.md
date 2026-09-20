# 진행 Issue

- 담당: PM이 할당·상태 관리, 각 Agent가 자신의 수행 기록 작성
- 갱신일: 2026-09-21
- 현재 등록된 Issue: ISSUE-0001
- 상태 정의와 전이 조건: [협업 규칙](../README.md#issue-workflow)

## 관리 규칙

- PM이 `ISSUE-0001`부터 ID를 순차 부여한다. ACTIVE·DONE 전체에서 중복·재사용하지 않는다.
- 아래 템플릿을 복사하고 제목을 Issue ID로 작성한다. 링크 예: `ACTIVE.md#issue-0001`
- Frontend·Backend를 함께 포함하면 각 담당자의 범위·완료 증거를 구분한다. 모든 필수 작업이 조건을 만족해야 전체 상태가 전진한다.
- 독립 작업은 별도 Issue로 분리하고 관련·선행 Issue를 연결한다.
- 담당자는 역할·모델과 필요 시 세션 식별자를 적는다. 두 Opus 또는 두 Fable의 역할을 구별한다.
- 할당·계약·의존성이 미정이면 READY로 전환하지 않는다.
- QA 발견 문제는 PM이 결함 Issue를 생성하거나 기존 결함 Issue에 연결한다. 원본 구현 Issue에도 링크를 남긴다.

## Issue 템플릿

```markdown
## ISSUE-NNNN

- Domain: TODO — SPEC 링크 또는 공통 작업임을 명시
- 제목: TODO
- 설명: TODO — 목적, 범위, 제외 범위
- 담당 Agent: TODO
- 관련 요구사항·기능·설계: TODO 링크
- 관련 Frontend 작업: TODO — 담당자·범위 또는 해당 없음과 사유
- 관련 Backend 작업: TODO — 담당자·범위 또는 해당 없음과 사유
- 기타 역할 작업: TODO — QA·Git·DevOps 등
- 수정 가능한 파일·문서 범위: TODO
- 선행 의존성: TODO
- 관련 Issue: TODO
- 현재 상태: PLANNED
- 최종 갱신일·작성 역할: TBD

### 완료 조건
- [ ] TODO — 관찰 가능한 결과로 작성

### 테스트 조건
- 대상 환경·실행 방법: TODO
- 정상 흐름: TODO
- 오류·경계 조건: TODO
- 필수 테스트·성공 기준: TODO

### 수행 및 검증 기록
| 날짜 | 역할 | 변경·검증 내용 | 대상 변경본·환경 | 결과·증거 |
| --- | --- | --- | --- | --- |

### 발견된 문제
| 문제 | 심각도·영향 | 재현 정보 또는 QA 링크 | 결함 Issue | 해결 여부 |
| --- | --- | --- | --- | --- |

### 상태 이력
| 날짜 | 이전 상태 | 새 상태 | 근거·증거 | 기록자 |
| --- | --- | --- | --- | --- |

### 세션 인계
- 마지막 완료 작업: TODO
- 진행 중인 작업·수정 파일: TODO
- 남은 작업: TODO
- 장애 요인·필요한 결정: TODO
- 다음 행동·담당 Agent: TODO

### Git·배포 기록
- QA 보고서 및 검증 변경본: TODO
- 작업 경로·Branch·기준 Commit: TBD — Git Manager 기록
- Commit·PR·Merge 참조: TODO
- 배포 대상 여부·비대상 사유: TBD
- 배포 버전·환경·서비스 점검 결과: TODO
- 배포 실패·복구 결과: 해당 시 기록
```

Commit 이전 QA 대상은 기준 Commit(있는 경우), 변경 파일 목록, diff 식별값이나 보관 위치, 검증 시각으로 식별한다. Git Manager는 제출 변경본과의 일치를 확인한다.

## ISSUE-0001

- 제목: 로컬 팀 세션 웹 모니터
- Domain: 공통 개발 도구
- 요청 근거: 사용자의 웹 UI 구현 및 지정 Figma 파일 디자인 작성 요청
- 담당: Codex (사용자 직접 할당)
- 범위: workflow.py, tools/team/, templates/project/, README.md, 관련 문서
- 설계: 기존 실행기와 분리된 Python HTTP 서버. GET /api/state는 프로젝트별 Claude 세션과 최근 로그, QA 상태, ACTIVE 문서를 반환. 고정 정적 경로, 4초 조회 캐시와 잠금 사용.
- 디자인: [Team Monitor](https://www.figma.com/design/wSs0xJpVRe6B8TNEy0kL2G/Test?node-id=3-130)
- 완료 조건: 역할별 상태/최근 출력/Issue 조회, 자동·수동 갱신, 실패·빈 상태 구분, Figma 디자인 기록
- 제외: 웹에서 역할 시작·종료, 비PM 사용자 메시지 전송, PM↔QA 자동 중계, 외부 배포
- 현재 상태: CODE_REVIEW
- 검증: `python3 -m unittest discover -s tools/team -p test_dashboard.py` 4개 통과. `node --check tools/team/web/app.js`, `git diff --check` 통과.
- 실제 HTTP 검증: HTML/JS/CSS 200, /api/state 7개 역할 및 실제 Issue 포함, 템플릿 제외, 외부 Host 403, 임의 경로 404 확인.
- 디자인 검증: Figma 프레임 생성 후 스크린샷으로 레이아웃 확인.
- 인계: 구현·자체 검증 완료. 별도 Git 리뷰와 실제 브라우저 상호작용 QA 미실행, QA_PASSED 아님.
- 실행: `python3 tools/team/dashboard.py` → http://127.0.0.1:8765
- 제한: PM만 웹 대화 가능. QA는 저장된 로그 조회. 토큰 수치는 로컬 기록 기준이며 계정 잔여 한도가 아님. 커밋·배포 미실행.
- 최종 갱신일·작성 역할: 2026-09-21 · Codex

### ISSUE-0001 후속 변경 — PM 단일 소통 창구 (2026-09-21)

- 사용자 요청에 따라 PM만 직접 소통하도록 공통·역할 문서와 신규 세션 초기 지시를 변경.
- 웹 UI에서 비PM 접속 명령과 복사 버튼을 제거하고 관찰 전용 안내 적용.
- QA 사용자 수동 중계 지침 제거. QA 통신 연결은 미구현이며 PM이 차단 사유로 관리.
- 이미 실행 중인 세션에 지침을 강제로 주입하거나 재시작하지 않음. 새 초기 지시는 이후 시작한 세션부터 적용.

### ISSUE-0001 후속 변경 — PM 웹 대화와 스크롤 (2026-09-21)

- 사용자 요청으로 기존 메시지 전송 제외 범위를 변경: PM에만 웹 입력과 실시간 출력 제공. 비PM 관찰 전용 유지.
- tools/team/pm_terminal.py, web/terminal.js, 고정 버전 xterm vendor 추가. 기존 PM 세션 attach 연결을 사용하며 새 PM을 만들지 않음.
- API: GET /api/session, GET /api/pm/output, POST /api/pm/connect·input·resize·disconnect. 입력은 동일 Origin + 토큰 검사.
- 웹 높이 고정 및 대화·로그·Issue 내부 스크롤. IME Enter 처리 및 재연결 시 자동 재전송 금지.
- 테스트: test_dashboard.py 7개, test_pm_http.py 4개 통과. JS 구문 및 Python 구문 검사 통과.
- 실제 브라우저: PM 연결·실제 대화 출력 표시, 입력창 활성, 콘솔 오류 없음 확인. viewport 1196px과 문서 높이 1196px 일치, 대화 영역 574px. 사용자 입력 테스트 메시지에 대한 PM 응답이 웹에 표시되는 것을 확인.
- Figma 새 프레임: [7:5](https://www.figma.com/design/wSs0xJpVRe6B8TNEy0kL2G/Test?node-id=7-5). 기존 프레임 보존.
- 별도 QA 역할의 승인·Git 리뷰·커밋·외부 배포는 수행하지 않음.

### ISSUE-0001 후속 변경 — 프로젝트 문서 창 (2026-09-21)

- 기획·Issue·커밋 규칙·디자인 시스템 등을 확인할 창구 추가 요청 반영.
- documents.py와 web/documents.js: GET /api/docs 목록, GET /api/doc?path=... 본문. docs의 Markdown과 MyIdea만 허용.
- 분류·검색·수정 시각·새로고침·Markdown 표/코드·내부 링크·Escape 닫기·포커스 복귀 지원. 문서 목록/본문 독립 스크롤.
- test_documents.py 4개 통과: 분류, 최신 파일 반영, 경로 탈출·절대 경로·외부 심볼릭 링크 차단.
- 브라우저 확인: 23개 문서, 검색 결과, 디자인 시스템 표·본문 정상 표시. 페이지 1196px 유지, 문서 창 1075px, 본문 내부 스크롤, 콘솔 오류 없음.
- 웹 서버 재시작 중 발견한 PTY 종료 지연 수정: nonblocking read/write 및 대기 시간 제한. PM 원본 프로세스는 종료하지 않음.

- 최종 관련 테스트: 16개 통과(실제 로컬 PTY 입출력·종료 포함). Figma [문서 창 프레임](https://www.figma.com/design/wSs0xJpVRe6B8TNEy0kL2G/Test?node-id=8-8) 추가.


### ISSUE-0001 후속 변경 — QA 기록 연결 (2026-09-21)

- 고정된 QA 미연결 안내를 제거하고 Codex App Server의 읽기 API로 같은 프로젝트의 최신 QA 초기화 세션을 식별.
- 모델을 시작·재개하지 않고 저장된 요청, QA 응답, 명령 실행 기록을 표시. 최근 기록 시각과 실행기 기반 생존 상태를 구분.
- 실제 QA 세션 01a0c002-0941-7de0-97b1-12e8190db82e의 초기화 응답 및 5,995자 기록을 브라우저에서 확인. 현재 역할 상태는 종료.

### ISSUE-0001 후속 변경 — 프로젝트 재사용과 관리 모달 (2026-09-21)

- 사용자 요청: todo/workflow에 도구를 클론하고 상위 todo의 app·backend·docs를 프로젝트별로 관리. 기존 PR 규칙 유지.
- workflow.py init/start/team/status 진입점과 project.py 경로 설정 추가. 초기화는 전용 templates/project를 사용하고 기존 문서·코드·규칙·스킬을 덮어쓰지 않음. 실행 시 역할 세션을 자동 시작하지 않음.
- 프로젝트별 .team-runtime과 .workflow-project.json 사용. CLI 프로세스와 QA Terminal에도 같은 프로젝트 경로를 전달. 새 프로젝트의 역할 이름에는 경로 해시를 포함해 이름 충돌을 방지하며 기존 실행 세션은 유지. Claude 작업 트리의 세션은 해당 프로젝트로 분류.
- 중복된 오른쪽 문서 바로가기를 URL·시크릿·토큰 모달 버튼으로 교체. 문서 브라우저는 상단 버튼에 유지.
- 사용자 선택에 따라 시크릿은 이 PC의 .team-runtime/resources.json에 평문 저장(폴더 700·파일 600·Git 제외). 기본 GET은 이름과 고정 마스킹만 제공. 명시적 표시·수정·삭제는 동일 Origin+토큰 필요. 30초 또는 탭 전환·닫기 시 화면의 값을 제거.
- Git/Figma/배포 URL 편집·열기. 현재 프로젝트 Figma 링크를 로컬 설정에 등록. 다른 프로젝트로 복제하지 않음.
- Claude 반복 메시지 사용량 중복 제거, Codex 세션별 마지막 누적값 집계. 입력·출력·캐시 구분 및 조회 실패·빈 기록 구분. 금액·계정 잔여 한도는 추정하지 않음.
- 검증: 전체 32개 테스트 통과. 새 임시 todo/workflow 복제에서 프로젝트 격리·첫 서버 실행·app/backend 생성·빈 설정·PR 규칙 보존 확인. 시크릿 보호 HTTP 검사, QA 세션 오인 방지, 토큰 중복 집계 방지 포함.
- 브라우저: URL 저장, 테스트 키 저장·마스킹·표시·탭 전환 시 숨김·삭제, 실제 토큰 집계 및 QA 로그 확인. 테스트 키는 삭제. 페이지 높이 1196px 유지, 모달 내부 스크롤 확인.
- Figma: [프로젝트 URL](https://www.figma.com/design/wSs0xJpVRe6B8TNEy0kL2G/Test?node-id=11-58), [시크릿](https://www.figma.com/design/wSs0xJpVRe6B8TNEy0kL2G/Test?node-id=14-55), [토큰](https://www.figma.com/design/wSs0xJpVRe6B8TNEy0kL2G/Test?node-id=14-94). 기존 PM 화면의 관리 카드도 갱신.
- 자체 검증 완료, 별도 Git 리뷰·QA 역할 승인·Commit·Push·PR·배포는 미실행. 원격 저장소에는 아직 반영되지 않음.


### ISSUE-0001 로컬 커밋 요청 (2026-09-21)

- 사용자의 명시적 커밋 요청에 따라 이번 구현 범위의 로컬 커밋 진행. 일반 PR 규칙은 유지하며 별도 QA 역할 승인이나 READY_FOR_PR을 허위 기록하지 않음. 현재 CODE_REVIEW 유지.
- 커밋 전 검토에서 팀 시작 완료 안내의 삭제된 SENDABLE 참조를 수정하고 기존 팀 재사용 회귀 테스트 추가. 전체 33개 테스트 통과.
- MyIdea.md의 별도 수정, .claude/worktrees, .team-runtime의 설정·시크릿은 커밋에서 제외. Push·PR·Merge·배포는 요청 범위에 포함되지 않음.


### ISSUE-0001 수정 — 제품 루트 중복 파일 생성 방지

- 사용자 지적: 제품 루트에 협업 파일을 다시 복사하는 동작이 요구한 세 폴더 구조와 다름.
- 원본 ai-workflow 저장소만 수정. TestTodo 사본과 그 안의 기존 파일·실행 세션은 변경하지 않음.
- 협업 작업 경로를 도구 폴더로 고정하고 제품 경로는 별도로 유지. 문서·역할 세션·런타임은 도구 내부를 사용하고 Git URL·화면의 프로젝트 이름은 제품 경로 기준.
- 초기화는 제품 루트에 frontend·backend만 생성. 도구 예제 문서는 첫 초기화 때 내부 백업 후 템플릿으로 교체하고 이후 프로젝트 문서는 보존. PR 규칙 유지.
- start는 팀 시작 후 모니터 실행, --monitor-only는 조회 전용 실행. 실제 테스트 모델 세션을 생성하지 않고 모의 실행과 임시 프로젝트 HTTP로 검증.
- 검증 결과: 전체 35개 테스트 통과. 제품 루트 항목 정확히 3개, 반복 초기화 문서 보존, 기존 문서 백업, 역할의 제품/협업 경로 분리, start 호출 순서 확인. 커밋·푸시는 아직 수행하지 않음.
