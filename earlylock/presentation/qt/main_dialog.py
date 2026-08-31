from datetime import datetime
from pathlib import Path

from PySide6.QtGui import QCloseEvent, QFont, QFontDatabase
from PySide6.QtWidgets import QDialog, QTextBrowser, QWidget

from earlylock.application.ports import GameStateTracker
from earlylock.domain.models import Agent, AutoPickSettings, Player
from earlylock.presentation.qt.generated.ui_main_dialog import Ui_Dialog
from earlylock.presentation.qt.workers import AutoPickWorker, ServiceFactory


class MainDialog(QDialog):
    FONT_PATH = (
        Path(__file__).resolve().parents[2]
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

    def update_player_text_boxes(self, tracker: GameStateTracker) -> None:
        allies, enemies = player_display_texts(tracker)
        _replace_text(self.ui.teamTextBox, allies)
        _replace_text(self.ui.enemyTextBox, enemies)


def player_display_texts(tracker: GameStateTracker) -> tuple[str, str]:
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
        identity = "가림"
    elif player.tag is None:
        identity = player.name
    else:
        identity = f"{player.name}#{player.tag}"

    return f"{agent:<5}: {identity}"


def _replace_text(widget: QTextBrowser, text: str) -> None:
    if widget.toPlainText() == text:
        return

    widget.setPlainText(text)
