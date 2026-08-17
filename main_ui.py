from datetime import datetime
from threading import Event, Lock

from PySide6.QtCore import QThread, Signal
from PySide6.QtWidgets import QDialog

from client import Client
from constants import Agent, GameState
from ui_dialog import Ui_Dialog
from valorant_api import ValorantAPI


class AutoPickWorker(QThread):
    log_message = Signal(str)
    settings_requested = Signal()

    POLL_INTERVAL_SECONDS = 1.0
    PICK_DELAY_SECONDS = 5.0

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.stop_event = Event()
        self.settings_event = Event()
        self.settings_lock = Lock()
        self.current_settings: tuple[Agent, bool] | None = None

    def stop(self) -> None:
        self.stop_event.set()
        self.settings_event.set()

    def provide_settings(self, agent: Agent, pick_only: bool) -> None:
        with self.settings_lock:
            self.current_settings = agent, pick_only
        self.settings_event.set()

    def request_current_settings(self) -> tuple[Agent, bool] | None:
        with self.settings_lock:
            self.current_settings = None
        self.settings_event.clear()
        self.settings_requested.emit()

        while not self.stop_event.is_set():
            if self.settings_event.wait(0.1):
                with self.settings_lock:
                    return self.current_settings
        return None

    def run(self) -> None:
        try:
            client = Client()
            valorant_api = ValorantAPI(client)
        except Exception as error:
            self.log_message.emit(f"VALORANT 클라이언트 연결에 실패했습니다: {error}")
            return

        self.log_message.emit(
            f"{client.player_name}#{client.player_tag}로 연결했습니다."
        )
        pregame_handled = False

        try:
            while not self.stop_event.is_set():
                game_state = valorant_api.get_game_state()

                if game_state == GameState.PREGAME and not pregame_handled:
                    pregame_handled = True
                    self.log_message.emit(
                        "PREGAME을 감지했습니다. 3초 후 자동 픽을 시도합니다."
                    )
                    if self.stop_event.wait(self.PICK_DELAY_SECONDS):
                        break
                    self.pick_agent(valorant_api)
                elif game_state != GameState.PREGAME and pregame_handled:
                    pregame_handled = False
                    self.log_message.emit(
                        f"{game_state.value} 상태를 감지했습니다. 다음 PREGAME 감지를 대기합니다."
                    )

                if self.stop_event.wait(self.POLL_INTERVAL_SECONDS):
                    break
        except Exception as error:
            self.log_message.emit(f"자동 픽 감시 중 오류가 발생했습니다: {error}")

    def pick_agent(self, valorant_api: ValorantAPI) -> None:
        settings = self.request_current_settings()
        if settings is None:
            return

        agent, pick_only = settings
        match_id = valorant_api.get_pregame_id()

        if match_id is None:
            self.log_message.emit(
                "PREGAME 정보를 확인할 수 없어 자동 픽을 시도하지 못했습니다."
            )
            return

        if valorant_api.select_agent(match_id, agent):
            self.log_message.emit(f"{agent.display_name} 선택에 성공했습니다.")
        else:
            self.log_message.emit(f"{agent.display_name} 선택에 실패했습니다.")

        if pick_only:
            self.log_message.emit("pick only 설정에 따라 요원을 잠그지 않습니다.")
            return

        if valorant_api.lock_agent(match_id, agent):
            self.log_message.emit(f"{agent.display_name} 잠금에 성공했습니다.")
        else:
            self.log_message.emit(f"{agent.display_name} 잠금에 실패했습니다.")


class MainUi(QDialog):
    def __init__(self):
        super().__init__()

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

            self.worker = AutoPickWorker(self)
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
            self.ui.selectedAgent.currentData(),
            self.ui.pickOnlyCheckBox.isChecked(),
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

    def closeEvent(self, event) -> None:
        if self.worker is not None and self.worker.isRunning():
            self.close_requested = True
            self.worker.stop()
            event.ignore()
            return
        super().closeEvent(event)

    def append_log(self, message: str) -> None:
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.ui.logTextBrowser.append(f"[{timestamp}] {message}")
