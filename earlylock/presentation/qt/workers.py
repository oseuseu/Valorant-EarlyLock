from collections.abc import Callable
from threading import Event, Lock

from PySide6.QtCore import QObject, QThread, Signal

from earlylock.application.auto_pick import AutoPickService, PickResult
from earlylock.domain.models import AutoPickSettings

ServiceFactory = Callable[[], AutoPickService]


class AutoPickWorker(QThread):
    log_message = Signal(str)
    settings_requested = Signal()

    POLL_INTERVAL_SECONDS = 1.0

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
            self.log_message.emit("pick only 설정에 따라 요원을 잠그지 않습니다.")
            return

        locked_message = "성공" if result.locked else "실패"
        self.log_message.emit(
            f"{settings.agent.display_name} 잠금에 {locked_message}했습니다."
        )
