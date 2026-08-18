from collections import deque
from collections.abc import Iterable

from earlylock.domain.models import Agent, GameState


class FakeValorantGateway:
    player_name = "Tester"
    player_tag = "KR1"

    def __init__(
        self,
        states: Iterable[GameState] = (),
        *,
        match_id: str | None = "match-1",
        select_succeeds: bool = True,
        lock_succeeds: bool = True,
    ) -> None:
        self._states = deque(states)
        self.match_id = match_id
        self.select_succeeds = select_succeeds
        self.lock_succeeds = lock_succeeds
        self.selected: list[tuple[str, Agent]] = []
        self.locked: list[tuple[str, Agent]] = []
        self.closed = False

    def get_game_state(self) -> GameState:
        return self._states.popleft() if self._states else GameState.LOBBY

    def get_pregame_id(self) -> str | None:
        return self.match_id

    def select_agent(self, match_id: str, agent: Agent) -> bool:
        self.selected.append((match_id, agent))
        return self.select_succeeds

    def lock_agent(self, match_id: str, agent: Agent) -> bool:
        self.locked.append((match_id, agent))
        return self.lock_succeeds

    def close(self) -> None:
        self.closed = True
