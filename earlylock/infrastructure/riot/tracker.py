from typing import Self

from earlylock.application.ports import (
    GameEventListener,
    GameGateway,
    PlayerNameLookup,
)
from earlylock.domain.models import (
    GameState,
    LiveMatch,
    LivePlayer,
    Player,
    PlayerName,
    Team,
)


class GameTracker:
    def __init__(
        self,
        api: GameGateway,
        resolver: PlayerNameLookup,
        listener: GameEventListener,
    ) -> None:
        self._api = api
        self._resolver = resolver
        self._listener = listener
        self._state = GameState.LOBBY
        self._match_id: str | None = None
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

        ended_match_id = self._match_id
        self._reset()
        if ended_match_id is not None:
            self._listener.on_coregame_end(ended_match_id)

    def _update_match(
        self,
        state: GameState,
        match: LiveMatch | None,
    ) -> None:
        if match is None:
            return

        live_players = match.allies + match.enemies
        names = self._resolver.resolve_many(
            player.puuid for player in live_players
        )
        self._state = state
        self._match_id = match.id
        self._players = {
            "Ally": self._resolve_players(match.allies, names, "Ally"),
            "Enemy": self._resolve_players(match.enemies, names, "Enemy"),
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
        self._players = self._empty_teams()

    @staticmethod
    def _empty_teams() -> dict[Team, tuple[Player, ...]]:
        return {"Ally": (), "Enemy": ()}
