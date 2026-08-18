from collections.abc import Iterable
from typing import Any

from requests import HTTPError

from earlylock.domain.models import Agent, GameState, MatchSnapshot, PlayerName
from earlylock.infrastructure.riot.client import EndpointType, RiotClient
from earlylock.infrastructure.riot.match_mapper import (
    from_coregame,
    from_pregame,
    get_ally_player_ids,
    get_coregame_player_ids,
)


class ValorantApi:
    NOT_IN_GAME_STATUS_CODES = {400, 404}

    def __init__(self, client: RiotClient) -> None:
        self._client = client

    @property
    def player_name(self) -> str:
        return self._client.player_name

    @property
    def player_tag(self) -> str:
        return self._client.player_tag

    def _fetch_optional(self, endpoint: str) -> dict[str, Any] | None:
        try:
            return self._client.fetch(endpoint, EndpointType.GLZ)
        except HTTPError as error:
            status_code = (
                error.response.status_code
                if error.response is not None
                else None
            )
            if status_code in self.NOT_IN_GAME_STATUS_CODES:
                return None
            raise

    def get_pregame_player(self) -> dict[str, Any] | None:
        return self._fetch_optional(f"/pregame/v1/players/{self._client.puuid}")

    def get_pregame_id(self) -> str | None:
        player = self.get_pregame_player()
        return player.get("MatchID") if player else None

    def get_pregame_match(self, match_id: str) -> dict[str, Any] | None:
        return self._fetch_optional(f"/pregame/v1/matches/{match_id}")

    def get_player_names(self, puuids: Iterable[str]) -> dict[str, PlayerName]:
        unique_puuids = list(dict.fromkeys(puuid for puuid in puuids if puuid))
        if not unique_puuids:
            return {}

        payload = self._client.put(
            "/name-service/v2/players",
            EndpointType.PD,
            json_data=unique_puuids,
        )
        if not isinstance(payload, list):
            raise TypeError("Name Service 응답이 JSON array 형식이 아닙니다.")

        names: dict[str, PlayerName] = {}
        for player in payload:
            puuid = player.get("Subject")
            name = player.get("GameName")
            tag = player.get("TagLine")
            if not all(isinstance(value, str) for value in (puuid, name, tag)):
                continue
            names[puuid] = PlayerName(puuid=puuid, name=name, tag=tag)
        return names

    def get_pregame_snapshot(self, match_id: str) -> MatchSnapshot | None:
        payload = self.get_pregame_match(match_id)
        if payload is None:
            return None

        player_names = self.get_player_names(get_ally_player_ids(payload))
        return from_pregame(payload, player_names)

    def get_coregame_player(self) -> dict[str, Any] | None:
        return self._fetch_optional(f"/core-game/v1/players/{self._client.puuid}")

    def get_coregame_id(self) -> str | None:
        player = self.get_coregame_player()
        return player.get("MatchID") if player else None

    def get_coregame_match(self, match_id: str) -> dict[str, Any] | None:
        return self._fetch_optional(f"/core-game/v1/matches/{match_id}")

    def get_coregame_snapshot(self, match_id: str) -> MatchSnapshot | None:
        payload = self.get_coregame_match(match_id)
        if payload is None:
            return None

        player_names = self.get_player_names(get_coregame_player_ids(payload))
        return from_coregame(payload, player_names)

    def get_game_state(self) -> GameState:
        if self.get_pregame_player() is not None:
            return GameState.PREGAME
        if self.get_coregame_player() is not None:
            return GameState.IN_GAME
        return GameState.LOBBY

    def select_agent(self, match_id: str, agent: Agent) -> bool:
        try:
            self._client.post(
                f"/pregame/v1/matches/{match_id}/select/{agent.uuid}",
                EndpointType.GLZ,
            )
            return True
        except HTTPError:
            return False

    def lock_agent(self, match_id: str, agent: Agent) -> bool:
        try:
            self._client.post(
                f"/pregame/v1/matches/{match_id}/lock/{agent.uuid}",
                EndpointType.GLZ,
            )
            return True
        except HTTPError:
            return False

    def quit_pregame(self, match_id: str) -> bool:
        try:
            self._client.post(
                f"/pregame/v1/matches/{match_id}/quit",
                EndpointType.GLZ
            )
            return True
        except:
            return False

    def quit_coregame(self, match_id: str) -> bool:
        try:
            self._client.post(
                f"/core-game/v1/players/{self._client.puuid}/disassociate/{match_id}",
                EndpointType.GLZ
            )
            return True
        except:
            return False

    def close(self) -> None:
        self._client.close()
