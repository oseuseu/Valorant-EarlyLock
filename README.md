# Valorant EarlyLock

VALORANT 클라이언트의 로컬 API를 이용해 PREGAME 진입 시 선택한 요원을 자동으로 선택하거나 잠그는 PySide6 애플리케이션입니다.

## 실행

Python 3.11 이상과 실행 중인 VALORANT 클라이언트가 필요합니다.

```powershell
python -m pip install -e .
python -m earlylock
```

기존 실행 방식도 지원합니다.

```powershell
python main.py
```

## 구조

- `earlylock/domain`: 게임 상태, 요원, 자동 픽 설정
- `earlylock/application`: 자동 픽 유스케이스와 외부 API 규격
- `earlylock/infrastructure/riot`: lockfile, 인증, VALORANT API 및 게임 추적
- `earlylock/presentation/qt`: Qt 화면과 Worker

Qt Designer 파일을 수정한 후 생성 코드는 다음 명령으로 갱신합니다.

```powershell
pyside6-uic earlylock/presentation/qt/forms/main_dialog.ui -o earlylock/presentation/qt/generated/ui_main_dialog.py
```
