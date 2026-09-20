# 팀 세션 시작

협업 도구 폴더와 제품 코드 폴더를 구분한다.

```text
제품 프로젝트/
├── ai-workflow/   # 이 문서·모니터·스킬·설정·로그
├── app/      # 제품 프론트엔드
└── backend/       # 제품 백엔드
```

## 실행

제품 루트에서 다음 명령 하나를 실행한다.

```bash
python3 ai-workflow/workflow.py start
```

폴더 준비 → 팀 초기화 → 로컬 모니터 실행 순서다. 이미 실행 중인 역할은 재사용한다. 초기화는 기능 구현·Commit·배포 요청이 아니다. 웹에서 PM에게 요구사항을 전달한 뒤 구현을 시작한다.

- [모니터](http://127.0.0.1:8765/) → PM → PM 연결
- 다른 포트: `python3 ai-workflow/workflow.py start --port 8766`
- 모니터만: `python3 ai-workflow/workflow.py start --monitor-only`
- 상태 확인: `python3 ai-workflow/workflow.py status`
- 실행 명령 확인: `python3 ai-workflow/workflow.py team --dry-run`
- 팀만 초기화: `python3 ai-workflow/workflow.py team`
- 다른 도구 폴더 이름을 쓸 때는 첫 실행에 `--project .`를 지정한다.

스킬을 사용하는 경우에는 ai-workflow 폴더에서 Claude의 `/setup team` 또는 Codex의 `$setup team`을 실행한다. Codex가 `/setup`을 인식하지 않으면 `$setup team`을 사용한다. 역할·모델 매핑의 원본은 도구 내부 `tools/team/launch.py`다.

## 저장과 작업 경로

- 문서·스킬·런타임·설정은 ai-workflow 내부에만 저장하며 제품 루트에 복사하지 않는다.
- 팀 CLI의 작업 경로는 ai-workflow다. 제품 app·backend 경로는 초기 지시에 별도로 전달한다.
- 첫 초기화는 도구에 포함된 예제 문서를 `.team-runtime/bootstrap-backup`에 보존하고 프로젝트 템플릿을 설치한다. 이후 프로젝트 문서·PR 규칙은 덮어쓰지 않는다.
- 제품 경로는 `.workflow-project.json`, 프로세스 상태·시크릿은 `.team-runtime`에 저장한다. 모두 도구의 Git 제외 대상이다.
- 기존 버전이 제품 루트에 만든 파일은 자동 삭제·이동하지 않는다. 기존 세션은 이전 경로를 사용하므로 전환 작업 없이 중복 파일부터 지우지 않는다.
- 초기화는 제품 Git 저장소를 만들지 않는다. 제품 Git 작업 대상과 협업 도구 저장소를 구분한다.

## 팀 상태와 소통

Claude 역할은 background 세션으로 실행되며 QA는 Codex Terminal 세션이다. macOS, Python 3.9 이상, 로그인된 claude·codex CLI와 지정 모델 접근 권한이 필요하다.

- RUNNING은 세션 생존만 뜻한다. 역할 준비 여부는 실제 출력으로 확인한다.
- 역할 이름에 제품 경로 식별자를 포함한다. 서로 다른 프로젝트의 같은 역할을 구분한다.
- 사용자와 직접 대화하는 역할은 PM뿐이다. 다른 역할은 질문·결과·차단 사유를 PM에게 보고한다.
- 문서 변경만으로 세션이 깨어나지 않는다. PM이 실제 역할 세션에 할당을 전달한다.
- PM↔QA 자동 메시지 중계는 별도 기능이다. 연결 부재는 PM이 차단 사유로 관리하고 사용자에게 중계를 요구하지 않는다.
- 모니터 종료는 웹 연결만 닫으며 역할 세션을 종료하지 않는다. Claude 종료는 `claude stop <id>`, QA 종료는 해당 Terminal에서 수행한다.

## 웹 기능

- PM 대화: PM 연결 → 입력창. Enter 전송, Shift+Enter 줄바꿈, 한글 조합 중 Enter는 전송하지 않음. 실제 CLI 권한 요청은 사용자가 터미널 화면에서 선택.
- 비PM 역할은 관찰 전용. QA는 동일 협업 경로의 QA 초기화 세션을 Codex 읽기 API로 찾아 저장된 대화·명령 기록과 마지막 기록 시각을 표시. 모델 대화를 시작·재개하지 않음.
- 상단 프로젝트 문서 버튼: 도구 내부 docs Markdown과 MyIdea.md만 읽기 전용으로 제공. 경로 탈출·외부 심볼릭 링크·HTML 실행 차단.
- 오른쪽 프로젝트 관리: 제품의 Git·Figma·배포 URL, 로컬 시크릿, 협업 세션 토큰 기록. 시크릿은 기본 마스킹·표시 30초 제한·탭 전환 시 숨김. 로컬 평문 파일 권한 600, Git 제외.
- 토큰 집계는 저장된 로컬 세션 기록이며 청구 금액이나 계정 잔여 한도가 아님.
- 페이지 높이는 화면에 고정하고 대화·문서·설정 본문은 내부 스크롤.
- 서버는 127.0.0.1 전용. PM 입력과 시크릿 표시·변경은 동일 Origin 및 서버 토큰 검증. 임의 세션이나 명령을 웹 요청으로 선택하지 못함.
- xterm 5.5.0, addon-fit 0.10.0, markdown-it 14.1.0 배포본과 라이선스는 tools/team/web/vendor에 포함. npm 설치나 CDN 연결 불필요.
