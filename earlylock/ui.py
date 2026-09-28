from collections.abc import Callable
from datetime import datetime
from pathlib import Path
from threading import Event, Lock

from PySide6.QtCore import QObject, QThread, Signal
from PySide6.QtGui import QCloseEvent, QFont, QFontDatabase
from PySide6.QtWidgets import QDialog, QTextBrowser, QWidget

from earlylock.game import AutoPickService, GameTracker, PickResult
from earlylock.models import Agent, AutoPickSettings, Player
from earlylock.ui_main_dialog import Ui_Dialog

ServiceFactory = Callable[[], AutoPickService]


class AutoPickWorker(QThread):
    log_message = Signal(str)
    game_tracker_updated = Signal(object)
    settings_requested = Signal()

    POLL_INTERVAL_SECONDS = 1.5

    def __init__(
        self,
        service_factory: ServiceFactory,
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self._service_factory = service_factory
        self._stop_event = Event()
        self._settings_event = Event()
        self._settings_lock = Lock()
        self._current_settings: AutoPickSettings | None = None

    def stop(self) -> None:
        self._stop_event.set()
        self._settings_event.set()

    def provide_settings(self, settings: AutoPickSettings) -> None:
        with self._settings_lock:
            self._current_settings = settings
        self._settings_event.set()

    def _request_current_settings(self) -> AutoPickSettings | None:
        with self._settings_lock:
            self._current_settings = None
        self._settings_event.clear()
        self.settings_requested.emit()

        while not self._stop_event.is_set():
            if self._settings_event.wait(0.1):
                with self._settings_lock:
                    return self._current_settings
        return None

    def run(self) -> None:
        try:
            service = self._service_factory()
        except Exception as error:
            self.log_message.emit(f"VALORANT 클라이언트 연결에 실패했습니다: {error}")
            return

        self.log_message.emit(f"{service.player_display_name}로 연결했습니다.")
        try:
            self._monitor(service)
        except Exception as error:
            self.log_message.emit(f"자동 픽 감시 중 오류가 발생했습니다: {error}")
        finally:
            try:
                service.close()
            except Exception as error:
                self.log_message.emit(f"VALORANT 연결 종료 중 오류가 발생했습니다: {error}")

    def _monitor(self, service: AutoPickService) -> None:
        while not self._stop_event.is_set():
            observation = service.poll_game_state()
            self.game_tracker_updated.emit(observation.tracker)

            if observation.pregame_started:
                settings = self._request_current_settings()
                if settings is None:
                    break

                self.log_message.emit(
                    "PREGAME을 감지했습니다. "
                    f"{settings.pick_delay_seconds:g}초 후 자동 픽을 시도합니다."
                )
                if self._stop_event.wait(settings.pick_delay_seconds):
                    break

                result = service.pick_agent(settings)
                self._emit_pick_result(settings, result)
            elif observation.pregame_ended:
                self.log_message.emit(
                    f"{observation.state.value} 상태를 감지했습니다. "
                    "다음 PREGAME 감지를 대기합니다."
                )

            if self._stop_event.wait(self.POLL_INTERVAL_SECONDS):
                break

    def _emit_pick_result(
        self,
        settings: AutoPickSettings,
        result: PickResult,
    ) -> None:
        if not result.match_found:
            self.log_message.emit(
                "PREGAME 정보를 확인할 수 없어 자동 픽을 시도하지 못했습니다."
            )
            return

        selected_message = "성공" if result.selected else "실패"
        self.log_message.emit(
            f"{settings.agent.display_name} 선택에 {selected_message}했습니다."
        )

        if result.locked is None:
            self.log_message.emit("자동 잠금 기능이 비활성화되어 있습니다.")
            return

        locked_message = "성공" if result.locked else "실패"
        self.log_message.emit(
            f"{settings.agent.display_name} 잠금에 {locked_message}했습니다."
        )


class MainDialog(QDialog):
    FONT_PATH = (
        Path(__file__).resolve().parent
        / "assets"
        / "fonts"
        / "SarasaMonoK-Regular.ttf"
    )

    def __init__(
        self,
        service_factory: ServiceFactory,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._service_factory = service_factory

        self.ui = Ui_Dialog()
        self.ui.setupUi(self)

        font_id = QFontDatabase.addApplicationFont(str(self.FONT_PATH))
        if font_id == -1:
            raise RuntimeError("폰트 로드 실패")

        font_family = QFontDatabase.applicationFontFamilies(font_id)[0]
        font = QFont(font_family, 10)
        self.ui.teamTextBox.setFont(font)
        self.ui.enemyTextBox.setFont(font)

        for agent in Agent:
            self.ui.selectedAgent.addItem(agent.display_name, agent)

        self._worker: AutoPickWorker | None = None
        self._close_requested = False

        self.ui.startToggleButton.setCheckable(True)
        self.ui.startToggleButton.setText("시작")
        self.ui.startToggleButton.toggled.connect(self.on_start_toggled)

    def on_start_toggled(self, is_running: bool) -> None:
        if is_running:
            self.ui.startToggleButton.setText("종료")
            self.append_log("자동 픽 감시를 시작합니다.")

            self._worker = AutoPickWorker(self._service_factory, self)
            self._worker.log_message.connect(self.append_log)
            self._worker.game_tracker_updated.connect(self.update_player_text_boxes)
            self._worker.settings_requested.connect(self.provide_current_settings)
            self._worker.finished.connect(self.on_worker_finished)
            self._worker.start()
            return

        self.ui.startToggleButton.setText("시작")
        self.append_log("자동 픽 감시를 종료합니다.")

        if self._worker is not None:
            self.ui.startToggleButton.setEnabled(False)
            self._worker.stop()

    def provide_current_settings(self) -> None:
        if self._worker is None:
            return

        self._worker.provide_settings(
            AutoPickSettings(
                agent=self.ui.selectedAgent.currentData(),
                pick_only=self.ui.pickOnlyCheckBox.isChecked(),
            )
        )

    def on_worker_finished(self) -> None:
        worker_stopped_unexpectedly = self.ui.startToggleButton.isChecked()
        worker = self._worker
        self._worker = None
        if worker is not None:
            worker.deleteLater()
        self.ui.startToggleButton.setEnabled(True)

        if worker_stopped_unexpectedly:
            self.ui.startToggleButton.blockSignals(True)
            self.ui.startToggleButton.setChecked(False)
            self.ui.startToggleButton.blockSignals(False)
            self.ui.startToggleButton.setText("시작")
            self.append_log("자동 픽 감시가 중지되었습니다.")

        if self._close_requested:
            self._close_requested = False
            self.close()

    def closeEvent(self, event: QCloseEvent) -> None:
        if self._worker is not None and self._worker.isRunning():
            self._close_requested = True
            self._worker.stop()
            event.ignore()
            return
        super().closeEvent(event)

    def append_log(self, message: str) -> None:
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.ui.logTextBrowser.append(f"[{timestamp}] {message}")

    def update_player_text_boxes(self, tracker: GameTracker) -> None:
        allies, enemies = player_display_texts(tracker)
        _replace_text(self.ui.teamTextBox, allies)
        _replace_text(self.ui.enemyTextBox, enemies)


def player_display_texts(tracker: GameTracker) -> tuple[str, str]:
    allies = "\n".join(
        _format_player(player) for player in tracker.players("Ally")
    )
    enemies = "\n".join(
        _format_player(player) for player in tracker.players("Enemy")
    )
    return allies, enemies


def _format_player(player: Player) -> str:
    if player.agent is None:
        agent = "미선택"
    elif player.is_locked:
        agent = player.agent.display_name
    else:
        agent = f"-{player.agent.display_name}"

    if player.name is None:
        identity = "조회 실패"
    elif player.tag is None:
        identity = player.name
    else:
        identity = f"{player.name}#{player.tag}"

    return f"{agent:<5}: {identity}"


def _replace_text(widget: QTextBrowser, text: str) -> None:
    if widget.toPlainText() == text:
        return

    widget.setPlainText(text)
