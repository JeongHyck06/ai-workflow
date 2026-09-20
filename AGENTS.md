# 프로젝트 진입점

먼저 `docs/README.md`를 읽는다. 역할·설계·Issue의 원본은 `/docs`다.
팀 시작 요청은 `.agents/skills/setup/SKILL.md`를 따른다.
`$setup team` 또는 자연어 팀 시작 요청은 세션 초기화이며 기능 구현·Commit·배포 요청이 아니다.
클라이언트가 `/setup team`을 일반 메시지로 전달한 경우에도 동일 스킬을 적용한다.
슬래시 명령 파서가 입력을 거부하면 AGENTS.md로 이를 가로챌 수 없으므로 `$setup team`을 안내한다.
