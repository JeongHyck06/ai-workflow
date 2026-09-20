# Domain 확장 규칙

PM이 요구사항을 분석하여 책임 경계를 정하고 필요한 Domain만 생성한다. 현재 확정 Domain은 없다.

## 구조

이름은 의미가 명확한 영문 소문자와 필요 시 하이픈을 사용한다. 아래는 확장 예시이며 확정 기능이 아니다.

```text
domains/
├── README.md
├── auth/
│   ├── SPEC.md
│   └── TASKS.md
└── user/
    ├── SPEC.md
    └── TASKS.md
```

1. PM이 REQUIREMENTS·FEATURES에 연결하여 Domain의 포함·제외 범위를 정한다.
2. 아래 템플릿으로 SPEC.md와 TASKS.md를 만든다.
3. 공통 API·DB·UI 설계는 원본 문서를 링크한다. Domain 사이 의존성도 SPEC에 연결한다.
4. PM이 ACTIVE에 Issue를 생성하고 TASKS에서 참조한다.

## SPEC.md 템플릿

```markdown
# TODO Domain 설계

- 담당: TODO
- 갱신일: TBD
- 관련 요구사항·기능·사용자 흐름: TODO 링크
- 목적: TODO
- 포함 범위: TODO
- 제외 범위: TODO
- Domain 고유 요구사항·비즈니스 규칙: TODO
- Frontend 책임·화면 동작: TODO
- Backend 책임·처리 흐름: TODO
- API 계약: TODO 원본 링크
- 데이터 모델: TODO 원본 링크
- 예외·경계 조건: TODO
- 다른 Domain과의 의존성: TODO
- 수용 기준: TODO
- 미정 사항·결정 주체: TODO

## 결정 이력
| 날짜 | 결정과 사유 | 관련 Issue | 작성 역할 |
| --- | --- | --- | --- |
```

## TASKS.md 템플릿

```markdown
# TODO Domain 작업 목록

- 담당: PM
- 갱신일: TBD
- 설계: [SPEC](SPEC.md)

담당자와 현재 상태는 연결된 Issue에서 확인한다. 상태 값을 이 문서에 복제하지 않는다.

| 작업 | Issue 및 현재 상태 원본 | 선행 Issue |
| --- | --- | --- |

## 아직 Issue로 분해하지 않은 작업
- TODO
```

완료 작업은 TASKS에 유지하되 링크를 DONE의 해당 Issue로 바꾼다. 파일 이동 시 관련 참조도 갱신한다.
