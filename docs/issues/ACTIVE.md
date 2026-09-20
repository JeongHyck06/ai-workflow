# 진행 Issue

- 담당: PM이 할당·상태 관리, 각 Agent가 자신의 수행 기록 작성
- 갱신일: TBD
- 현재 등록된 Issue: 없음
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
