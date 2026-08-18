from collections.abc import Callable
from datetime import datetime

from PySide6.QtGui import QCloseEvent
from PySide6.QtWidgets import QDialog, QWidget

from earlylock.application.auto_pick import AutoPickService
from earlylock.domain.models import Agent, AutoPickSettings
from earlylock.presentation.qt.generated.ui_main_dialog import Ui_Dialog
from earlylock.presentation.qt.workers import AutoPickWorker


class MainDialog(QDialog):
    def __init__(
        self,
        service_factory: Callable[[], AutoPickService],
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._service_factory = service_factory

        self.ui = Ui_Dialog()
        self.ui.setupUi(self)

        for agent in Agent:
            self.ui.selectedAgent.addItem(agent.display_name, agent)

        self.worker: AutoPickWorker | None = None
        self.close_requested = False

        self.ui.startToggleButton.setCheckable(True)
        self.ui.startToggleButton.setText("시작")
        self.ui.startToggleButton.toggled.connect(self.on_start_toggled)

    def on_start_toggled(self, is_running: bool) -> None:
        if is_running:
            self.ui.startToggleButton.setText("종료")
            self.append_log("자동 픽 감시를 시작합니다.")

            self.worker = AutoPickWorker(self._service_factory, self)
            self.worker.log_message.connect(self.append_log)
            self.worker.settings_requested.connect(self.provide_current_settings)
            self.worker.finished.connect(self.on_worker_finished)
            self.worker.start()
            return

        self.ui.startToggleButton.setText("시작")
        self.append_log("자동 픽 감시를 종료합니다.")

        if self.worker is not None:
            self.ui.startToggleButton.setEnabled(False)
            self.worker.stop()

    def provide_current_settings(self) -> None:
        if self.worker is None:
            return

        self.worker.provide_settings(
            AutoPickSettings(
                agent=self.ui.selectedAgent.currentData(),
                pick_only=self.ui.pickOnlyCheckBox.isChecked(),
            )
        )

    def on_worker_finished(self) -> None:
        worker_stopped_unexpectedly = self.ui.startToggleButton.isChecked()
        self.worker = None
        self.ui.startToggleButton.setEnabled(True)

        if worker_stopped_unexpectedly:
            self.ui.startToggleButton.blockSignals(True)
            self.ui.startToggleButton.setChecked(False)
            self.ui.startToggleButton.blockSignals(False)
            self.ui.startToggleButton.setText("시작")
            self.append_log("자동 픽 감시가 중지되었습니다.")

        if self.close_requested:
            self.close_requested = False
            self.close()

    def closeEvent(self, event: QCloseEvent) -> None:
        if self.worker is not None and self.worker.isRunning():
            self.close_requested = True
            self.worker.stop()
            event.ignore()
            return
        super().closeEvent(event)

    def append_log(self, message: str) -> None:
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.ui.logTextBrowser.append(f"[{timestamp}] {message}")
