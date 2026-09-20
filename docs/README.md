# AI 협업 문서 진입점

## 목적과 현재 상황

`/docs`는 모든 Agent가 공유하는 프로젝트 정보의 Single Source of Truth다. 새 세션은 이 파일에서 시작하고, 역할과 할당 Issue에 필요한 문서만 읽는다.

- 현재: 문서 체계 준비 완료. 프로젝트 요구사항, 기능, 기술 스택, 실행·배포 환경은 TBD
- 예정 코드 영역: `/app` 프론트엔드, `/backend` 백엔드
- 실제 개발 Issue: 없음. 템플릿은 할당이나 구현 승인을 의미하지 않는다.
- Agent 이름과 모델명은 역할 배정 기준이며, 이 문서가 Agent 실행이나 모델 설정을 자동 구성하지는 않는다.

## 문서 지도와 정보 소유권

아래 구조의 경로는 `docs/` 기준이다. 정보는 담당 문서에 한 번만 기록하고 다른 문서에서는 링크로 참조한다.

```text
docs/
├── README.md
├── product/
│   ├── REQUIREMENTS.md
│   ├── FEATURES.md
│   ├── USER_FLOW.md
│   └── DESIGN_SYSTEM.md
├── architecture/
│   ├── OVERVIEW.md
│   ├── FRONTEND.md
│   ├── BACKEND.md
│   ├── DATABASE.md
│   └── API.md
├── domains/
│   └── README.md
├── issues/
│   ├── ACTIVE.md
│   └── DONE.md
├── qa/
│   └── QA_REPORT.md
└── agents/
    ├── PM.md
    ├── FRONTEND.md
    ├── BACKEND.md
    ├── QA.md
    ├── GIT.md
    └── DEVOPS.md
```

| 문서 | 기록하는 정보 |
| --- | --- |
| [REQUIREMENTS](product/REQUIREMENTS.md) | 제품 목표, 요구사항, 범위, 제약 |
| [FEATURES](product/FEATURES.md) | 기능 목록 및 요구사항·Domain 연결 |
| [USER_FLOW](product/USER_FLOW.md) | 사용자 흐름과 예외 경로 |
| [DESIGN_SYSTEM](product/DESIGN_SYSTEM.md) | 공통 UI·접근성 기준 |
| [OVERVIEW](architecture/OVERVIEW.md) | 시스템 경계, 기술 결정, 운영·배포 설계 |
| [FRONTEND](architecture/FRONTEND.md) | 프론트엔드 구조와 구현 규약 |
| [BACKEND](architecture/BACKEND.md) | 백엔드 구조와 구현 규약 |
| [DATABASE](architecture/DATABASE.md) | 데이터 모델과 마이그레이션 설계 |
| [API](architecture/API.md) | Frontend와 Backend 사이의 API 계약 |
| [domains/README](domains/README.md) | Domain 생성 및 SPEC·TASKS 작성 규칙 |
| [ACTIVE](issues/ACTIVE.md) | 진행 Issue의 담당자, 상태, 인계 및 실행 증거 |
| [DONE](issues/DONE.md) | 완료 Issue의 최종 기록 |
| [QA_REPORT](qa/QA_REPORT.md) | 실제 환경 QA 실행 결과와 재검증 이력 |
| [agents](agents/PM.md) | 역할별 책임과 권한. 각 역할 파일을 읽는다. |

## 세션 시작과 선택적 읽기

1. 이 문서 → 자신의 역할 문서 → `issues/ACTIVE.md` 순서로 읽는다.
2. 할당 Issue의 설명, 상태, 인계, 관련 문서 링크를 확인한다. 할당이 없거나 선행 결정이 빠졌으면 PM에게 알린다.
3. 아래 문서 중 작업에 관련된 항목만 읽고, 관련 Domain의 `SPEC.md`와 `TASKS.md`를 확인한다.
4. 담당 파일과 병렬 작업자의 범위를 확인한 뒤 작업한다. 세션 종료 전 진행 내용, 검증 결과, 막힌 점, 다음 행동을 Issue에 기록한다.

| Agent | 역할 문서 | 작업별 추가 읽기 |
| --- | --- | --- |
| PM — Fable | [PM](agents/PM.md) | REQUIREMENTS, FEATURES, USER_FLOW, OVERVIEW, Domain 규칙, 관련 QA 결과 |
| Frontend — Opus | [FRONTEND](agents/FRONTEND.md) | FRONTEND 설계, API, DESIGN_SYSTEM, 관련 USER_FLOW |
| Backend — Opus | [BACKEND](agents/BACKEND.md) | BACKEND 설계, DATABASE, API, 관련 REQUIREMENTS |
| QA — Astra | [QA](agents/QA.md) | 관련 요구사항·흐름·UI 기준, QA_REPORT, 실행 환경 설계 |
| Git — Sonnet | [GIT](agents/GIT.md) | 해당 Issue의 변경 범위, 리뷰 기록, QA 결과 |
| DevOps — Fable | [DEVOPS](agents/DEVOPS.md) | OVERVIEW의 배포 설계, 관련 서비스 설계, Merge 기록 |

`DONE.md` 및 다른 Domain은 관련 Issue나 과거 결정 확인이 필요할 때만 읽는다. 동일 모델이 여러 역할을 맡더라도 권한은 현재 역할을 따른다.

## Issue Workflow

모든 개발 작업은 Issue 단위로 진행한다. PM이 상태를 관리하며, 각 Agent는 자신이 수행한 작업과 증거를 Issue에 기록한다. 상태 변경은 아래 조건을 만족한 경우에만 한다.

| 상태 | 진입 조건 및 다음 행동 |
| --- | --- |
| PLANNED | PM이 요구사항·Domain에 연결된 Issue 생성 |
| READY | 범위, 담당자, 완료·테스트 조건, 의존성 및 필요한 설계 확정 |
| IN_PROGRESS | 할당 개발자가 착수 |
| CODE_REVIEW | 구현과 자체 테스트 완료. 변경 범위·검증 증거를 기록하고 Git Manager가 diff 검토 |
| READY_FOR_QA | 리뷰 지적 해소, 실행 방법·환경·대상 변경본 식별 가능 |
| QA_TESTING | QA가 해당 변경본을 실제 Emulator 또는 Browser에서 검증 시작 |
| FIX_REQUIRED | 리뷰 또는 QA에서 수정 필요. PM이 문제를 확인하고 담당 개발자에게 재할당 |
| QA_PASSED | QA가 완료·테스트 조건 충족을 확인하고 보고서 연결 |
| READY_FOR_PR | PM이 QA 대상과 제출 대상의 일치, 문서·의존성·남은 문제 확인 |
| PR_OPEN | Git Manager가 Commit·Push·PR 생성 후 링크 기록 |
| MERGED | Git Manager가 저장소의 필수 검사·리뷰 조건 충족 후 Merge하고 결과 기록 |
| DEPLOYED | DevOps가 Merge된 버전을 배포하고 서비스 실행 확인 증거 기록 |

기본 경로:

`설계 → PM 기능 분석 → Domain 분리 → PLANNED → READY → IN_PROGRESS → CODE_REVIEW → READY_FOR_QA → QA_TESTING → QA_PASSED → READY_FOR_PR → PR_OPEN → MERGED → DEPLOYED`

- 수정 경로: `CODE_REVIEW 또는 QA_TESTING → FIX_REQUIRED → PM 재할당 → IN_PROGRESS → CODE_REVIEW → READY_FOR_QA → QA_TESTING`
- QA 이후 기능 변경이 생기면 PM이 영향 범위에 따라 수정·재검증 경로로 되돌린다. 기존 QA 통과를 새 변경본에 자동 적용하지 않는다.
- 실행 환경 부재, 의존성 대기, 배포 실패는 현재 상태를 유지하고 장애 요인·담당자·다음 행동을 기록한다. 검증하지 않은 단계를 통과 처리하지 않는다.
- Branch 준비와 읽기 전용 diff 검토는 QA 이전에도 Git Manager가 수행할 수 있다. Commit·Push·PR·Merge는 QA_PASSED와 PM의 READY_FOR_PR 확인 이후 수행한다.
- 배포 대상 Issue는 DEPLOYED 후 DONE으로 이동한다. 배포가 없는 문서 등 Issue는 PM이 배포 비대상 사유를 명시하고 MERGED에서 종료할 수 있다. 허위 DEPLOYED 기록은 금지한다.

## 문서 업데이트와 병렬 작업

- 요구사항·기능·사용자 흐름의 최종 정리는 PM, UI 규약은 Frontend, 각 계층 설계는 담당 개발자, QA 결과는 QA, Git 실행 기록은 Git Manager, 운영·배포 설계는 DevOps가 맡는다.
- API 계약은 Frontend·Backend가 함께 검토한다. 범위·요구사항 변경과 역할 간 충돌은 PM이 조정한 뒤 기록한다.
- 코드 변경에 영향을 주는 설계는 구현 전에 갱신한다. 작업 후에는 실제 결과, 테스트 증거, 인계 내용을 갱신한다.
- Issue 상태·담당자의 원본은 ACTIVE 또는 완료 후 DONE이다. Domain TASKS에는 상태를 복제하지 않고 해당 Issue 링크를 둔다.
- 한 파일의 같은 영역은 동시에 수정하지 않는다. PM이 Issue에 문서·코드 수정 범위를 배정하고 충돌 시 순서를 정한다. 다른 Agent의 미완료 변경을 덮어쓰거나 되돌리지 않는다.
- 미정 사항은 TODO 또는 TBD로 표시하고 결정 주체·필요한 입력을 남긴다. 결정에는 날짜, 사유, 관련 Issue를 기록한다.
- 상태와 설계 변경 시 해당 문서의 갱신일·작성 역할을 갱신한다. 증거는 명령·환경·결과 또는 링크로 남기며 실행하지 않은 테스트는 미실행으로 적는다.
- 비밀키·비밀번호·API Key 및 실제 환경 변수 값은 문서나 Git에 기록하지 않는다. 로그·화면 증거도 민감값을 제거한다.
