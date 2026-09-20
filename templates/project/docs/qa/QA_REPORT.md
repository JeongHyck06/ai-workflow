# QA 실행 보고서

- 담당: QA
- 갱신일: TBD
- 현재 실행 보고서: 없음
- Issue 상태 원본: [ACTIVE](../issues/ACTIVE.md)

## 기록 규칙

- 실행마다 `QA-0001` 형태의 고유 ID를 부여하고 원본 Issue에 연결한다.
- 앱은 Emulator, 웹은 Browser에서 검증한다. 플랫폼이 미정이면 PM에게 확인하며 실행 전에 통과로 표시하지 않는다.
- PASS·FAIL·BLOCKED·NOT_RUN은 실행 결과이며 Issue 상태와 별개다.
- 실패 시 재현 정보와 증거를 기록하여 PM에게 전달하고 PM이 등록·연결한 결함 Issue를 추가한다.
- 재검증은 새 보고서로 추가하고 이전 QA·수정 Issue를 연결한다. 기존 실패 결과를 삭제하지 않는다.

## 실행 템플릿

```markdown
## QA-NNNN

- 관련 Issue: TODO 링크
- 검증자·실행 시각: TODO
- 대상 플랫폼: TBD
- 실행 환경: TODO — Emulator 기종·OS 또는 Browser·버전·화면 크기
- 실행 명령·접속 경로·준비 조건: TODO
- 검증 변경본: TODO — Commit 또는 Issue의 변경본 식별 정보
- 테스트 데이터 조건: TODO — 민감값 제외
- 관련 완료·테스트 조건: TODO 원본 링크

| 케이스 | 재현 단계 | 기대 결과 | 실제 결과 | 판정 | 증거 |
| --- | --- | --- | --- | --- | --- |

- 확인 범위: 기능 정상 작동, 실제 사용자 흐름, UI 깨짐, UX 어색함, Edge Case
- 전체 결과: NOT_RUN
- 미실행·차단 항목과 사유: TODO

### 발견 문제
- 문제·심각도·사용자 영향: TODO
- 재현 단계·기대 결과·실제 결과: TODO
- 화면·로그 증거: TODO — 민감값 제거
- 결함 Issue: TODO — PM 등록 후 연결
- PM 전달 내용: TODO

### 재검증 연결
- 이전 QA 보고서·수정 Issue: 해당 시 링크
- 수정 확인 및 영향 범위 회귀 검증: TODO
```
