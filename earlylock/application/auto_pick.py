from dataclasses import dataclass

from earlylock.application.ports import ValorantGateway
from earlylock.domain.models import AutoPickSettings, GameState
from earlylock.infrastructure.riot.tracker import GameTracker


@dataclass(frozen=True)
class GameStateObservation:
    state: GameState
    tracker: GameTracker
    pregame_started: bool = False
    pregame_ended: bool = False


@dataclass(frozen=True)
class PickResult:
    match_found: bool
    selected: bool = False
    locked: bool | None = None


class AutoPickService:
    def __init__(
        self,
        gateway: ValorantGateway,
        tracker: GameTracker,
    ) -> None:
        self._gateway = gateway
        self._tracker = tracker
        self._pregame_handled = False

    @property
    def player_display_name(self) -> str:
        return f"{self._gateway.player_name}#{self._gateway.player_tag}"

    def poll_game_state(self) -> GameStateObservation:
        tracker = self._tracker.refresh()
        state = tracker.get_game_state()

        if state is GameState.PREGAME and not self._pregame_handled:
            self._pregame_handled = True
            return GameStateObservation(
                state=state,
                tracker=tracker,
                pregame_started=True,
            )

        if state is not GameState.PREGAME and self._pregame_handled:
            self._pregame_handled = False
            return GameStateObservation(
                state=state,
                tracker=tracker,
                pregame_ended=True,
            )

        return GameStateObservation(state=state, tracker=tracker)

    def pick_agent(self, settings: AutoPickSettings) -> PickResult:
        tracker = self._tracker.refresh()
        state = tracker.get_game_state()
        match_id = tracker.get_match_id()
        if state is not GameState.PREGAME or match_id is None:
            return PickResult(match_found=False)

        selected = self._gateway.select_agent(match_id, settings.agent)
        if settings.pick_only:
            return PickResult(match_found=True, selected=selected)

        locked = self._gateway.lock_agent(match_id, settings.agent)
        return PickResult(
            match_found=True,
            selected=selected,
            locked=locked,
        )

    def close(self) -> None:
        self._gateway.close()
