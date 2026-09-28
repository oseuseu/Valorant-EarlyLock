# Valorant EarlyLock

VALORANT 클라이언트의 로컬 API를 이용해 PREGAME 진입 시 선택한 요원을 자동으로 선택하는 PySide6 애플리케이션입니다. 자동 잠금은 비활성화되어 있습니다.

## 실행

Python 3.11 이상과 실행 중인 VALORANT 클라이언트가 필요합니다. 이름 조회에는 Riot 웹 로그인 세션의 `ssid`가 필요합니다. 프로젝트 루트의 `.env` 파일에 값을 입력하면 자동으로 읽습니다.

```dotenv
RIOT_SSID=여기에_ssid_입력
```

`.env` 파일이 없다면 `.env.example`을 복사해서 만드세요. `.env`는 Git에서 제외됩니다. 기존 터미널 환경 변수보다 `.env`의 값을 우선 사용합니다.

```powershell
python -m pip install -e .
python -m earlylock
```

기존 실행 방식도 지원합니다.

```powershell
python main.py
```

## 구조

- `earlylock/app.py`: 애플리케이션 실행 및 객체 연결
- `earlylock/models.py`: 게임 상태, 요원, 플레이어, 자동 픽 설정
- `earlylock/riot_client.py`: lockfile 읽기, 게임 클라이언트 인증 및 HTTP 요청
- `earlylock/valorant_api.py`: 경기 정보 변환, 요원 선택 및 이름 조회 연결
- `earlylock/name_finder.py`: `ssid`를 이용한 웹 인증 및 PUUID 기반 이름 조회
- `earlylock/game.py`: 게임 상태 추적과 자동 픽
- `earlylock/ui.py`: Qt 화면과 감시 Worker
- `earlylock/ui_main_dialog.py`, `earlylock/forms/main_dialog.ui`: Designer 생성 코드와 원본

이름 숨김 여부와 관계없이 모든 플레이어의 PUUID를 `ValorantNameService`에 전달합니다. 이름 DB나 경기 종료 후 수집 작업은 사용하지 않습니다. 조회한 이름은 현재 경기 동안 메모리에만 유지하며, 경기 변경·종료 시 비웁니다. 네트워크 오류로 조회하지 못한 이름은 다음 갱신에서 다시 시도하고 화면에는 `조회 실패`로 표시합니다.

## 검사

VALORANT 클라이언트나 실제 인증 정보 없이도 상태 전환, 응답 변환, 웹 인증 요청, 숨긴 이름 조회 경로와 재시도를 검사할 수 있습니다.

```powershell
python -m unittest discover -s tests -v
python -m compileall -q earlylock tests main.py
```

Qt Designer 파일을 수정한 후 생성 코드는 다음 명령으로 갱신합니다.

```powershell
pyside6-uic earlylock/forms/main_dialog.ui -o earlylock/ui_main_dialog.py
```
