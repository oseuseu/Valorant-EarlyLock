from dataclasses import dataclass
from typing import Self

from requests import RequestException

from earlylock.models import (
    AutoPickSettings, GameState, LiveMatch, LivePlayer, Player, PlayerName, Team,
)
from earlylock.valorant_api import ValorantApi


class GameTracker:
    def __init__(
        self,
        api: ValorantApi,
    ) -> None:
        self._api = api
        self._state = GameState.LOBBY
        self._match_id: str | None = None
        self._names: dict[str, PlayerName] = {}
        self._players: dict[Team, tuple[Player, ...]] = self._empty_teams()

    @property
    def state(self) -> GameState:
        return self._state

    @property
    def match_id(self) -> str | None:
        return self._match_id

    def players(self, team: Team) -> tuple[Player, ...]:
        return self._players[team]

    def refresh(self) -> Self:
        if self._state is GameState.LOBBY:
            self._refresh_lobby()
        elif self._state is GameState.PREGAME:
            self._refresh_pregame()
        else:
            self._refresh_coregame()
        return self

    def _refresh_lobby(self) -> None:
        match_id = self._api.get_pregame_id()
        if match_id is not None:
            self._update_match(
                GameState.PREGAME,
                self._api.get_pregame_match(match_id),
            )

    def _refresh_pregame(self) -> None:
        coregame_id = self._api.get_coregame_id()
        if coregame_id is not None:
            self._update_match(
                GameState.IN_GAME,
                self._api.get_coregame_match(coregame_id),
            )
            return

        pregame_id = self._api.get_pregame_id()
        if pregame_id is None:
            self._reset()
            return

        self._update_match(
            GameState.PREGAME,
            self._api.get_pregame_match(pregame_id),
        )

    def _refresh_coregame(self) -> None:
        match_id = self._api.get_coregame_id()
        if match_id is not None:
            self._update_match(
                GameState.IN_GAME,
                self._api.get_coregame_match(match_id),
            )
            return

        self._reset()

    def _update_match(
        self,
        state: GameState,
        match: LiveMatch | None,
    ) -> None:
        if match is None:
            return

        if match.id != self._match_id:
            self._names.clear()
        live_players = match.allies + match.enemies
        missing = list(dict.fromkeys(
            player.puuid for player in live_players
            if player.puuid and player.puuid not in self._names
        ))
        if missing:
            try:
                names = self._api.get_player_names(missing)
            except RequestException:
                # Keep tracking and retry unresolved names on the next poll.
                names = {}
            self._names.update(
                (puuid, name) for puuid, name in names.items()
                if puuid in missing and name.name and name.tag
            )
        self._state = state
        self._match_id = match.id
        self._players = {
            "Ally": self._resolve_players(match.allies, self._names, "Ally"),
            "Enemy": self._resolve_players(match.enemies, self._names, "Enemy"),
        }

    @staticmethod
    def _resolve_players(
        players: tuple[LivePlayer, ...],
        names: dict[str, PlayerName],
        team: Team,
    ) -> tuple[Player, ...]:
        resolved: list[Player] = []
        for player in players:
            player_name = names.get(player.puuid)
            resolved.append(
                Player(
                    puuid=player.puuid,
                    name=player_name.name if player_name else None,
                    tag=player_name.tag if player_name else None,
                    team=team,
                    agent=player.agent,
                    is_locked=player.is_locked,
                )
            )
        return tuple(resolved)

    def _reset(self) -> None:
        self._state = GameState.LOBBY
        self._match_id = None
        self._names.clear()
        self._players = self._empty_teams()

    @staticmethod
    def _empty_teams() -> dict[Team, tuple[Player, ...]]:
        return {"Ally": (), "Enemy": ()}


@dataclass(frozen=True, slots=True)
class GameStateObservation:
    state: GameState
    tracker: GameTracker
    pregame_started: bool = False
    pregame_ended: bool = False


@dataclass(frozen=True, slots=True)
class PickResult:
    match_found: bool
    selected: bool = False
    locked: bool | None = None


class AutoPickService:
    def __init__(
        self,
        gateway: ValorantApi,
    ) -> None:
        self._gateway = gateway
        self._tracker = GameTracker(gateway)
        self._pregame_handled = False

    @property
    def player_display_name(self) -> str:
        return f"{self._gateway.player_name}#{self._gateway.player_tag}"

    def poll_game_state(self) -> GameStateObservation:
        tracker = self._tracker.refresh()
        state = tracker.state

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
        state = tracker.state
        match_id = tracker.match_id
        if state is not GameState.PREGAME or match_id is None:
            return PickResult(match_found=False)

        selected = self._gateway.select_agent(match_id, settings.agent)
        return PickResult(match_found=True, selected=selected)

    def close(self) -> None:
        self._gateway.close()
