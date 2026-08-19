from typing import Protocol

from earlylock.domain.models import Agent


class ValorantGateway(Protocol):
    @property
    def player_name(self) -> str: ...

    @property
    def player_tag(self) -> str: ...

    def select_agent(self, match_id: str, agent: Agent) -> bool: ...

    def lock_agent(self, match_id: str, agent: Agent) -> bool: ...

    def close(self) -> None: ...
