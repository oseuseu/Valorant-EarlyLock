from collections.abc import Iterable
from typing import Protocol, Self

from earlylock.domain.models import (
    Agent,
    GameState,
    LiveMatch,
    Player,
    PlayerName,
    Team,
)


class ValorantGateway(Protocol):
    @property
    def player_name(self) -> str: ...

    @property
    def player_tag(self) -> str: ...

    def select_agent(self, match_id: str, agent: Agent) -> bool: ...

    def lock_agent(self, match_id: str, agent: Agent) -> bool: ...

    def close(self) -> None: ...


class PlayerNameGateway(Protocol):
    def get_player_names(
        self,
        puuids: Iterable[str],
    ) -> dict[str, PlayerName]: ...


class PlayerNameRepository(Protocol):
    def get_player_name_from_database(
        self,
        player_id: str,
    ) -> PlayerName | None: ...

    def upsert_player_names(self, player_names: Iterable[PlayerName]) -> int: ...


class GameStateTracker(Protocol):
    @property
    def state(self) -> GameState: ...

    @property
    def match_id(self) -> str | None: ...

    def players(self, team: Team) -> tuple[Player, ...]: ...

    def refresh(self) -> Self: ...


class GameGateway(Protocol):
    def get_pregame_id(self) -> str | None: ...

    def get_pregame_match(self, match_id: str) -> LiveMatch | None: ...

    def get_coregame_id(self) -> str | None: ...

    def get_coregame_match(self, match_id: str) -> LiveMatch | None: ...


class PlayerNameLookup(Protocol):
    def resolve_many(
        self,
        puuids: Iterable[str],
    ) -> dict[str, PlayerName]: ...


class GameEventListener(Protocol):
    def on_coregame_end(self, match_id: str) -> None: ...
