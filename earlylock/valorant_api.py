from collections.abc import Iterable
from typing import Any

from requests import HTTPError

from earlylock.models import Agent, LiveMatch, LivePlayer, PlayerName
from earlylock.name_finder import ValorantNameService
from earlylock.riot_client import EndpointType, RiotClient

JsonObject = dict[str, Any]


class ValorantApi:
    NOT_IN_GAME_STATUS_CODES = {400, 404}

    def __init__(self, client: RiotClient, name_service: ValorantNameService) -> None:
        self._client = client
        self._name_service = name_service

    @property
    def player_name(self) -> str:
        return self._client.player_name

    @property
    def player_tag(self) -> str:
        return self._client.player_tag

    @property
    def player_puuid(self) -> str:
        return self._client.puuid

    def _fetch_optional(
        self,
        endpoint: str,
        endpoint_type: EndpointType = EndpointType.GLZ,
    ) -> JsonObject | None:
        try:
            return self._client.fetch(endpoint, endpoint_type)
        except HTTPError as error:
            status_code = (
                error.response.status_code
                if error.response is not None
                else None
            )
            if status_code in self.NOT_IN_GAME_STATUS_CODES:
                return None
            raise

    def get_pregame_id(self) -> str | None:
        return self._get_current_match_id("pregame")

    def get_pregame_match(self, match_id: str) -> LiveMatch | None:
        payload = self._fetch_optional(f"/pregame/v1/matches/{match_id}")
        if payload is None:
            return None

        return LiveMatch(
            id=_match_id(payload, match_id),
            allies=_parse_live_players(_team_players(payload.get("AllyTeam"))),
        )

    def get_coregame_id(self) -> str | None:
        return self._get_current_match_id("core-game")

    def get_coregame_match(self, match_id: str) -> LiveMatch | None:
        payload = self._fetch_optional(f"/core-game/v1/matches/{match_id}")
        if payload is None:
            return None

        allies, enemies = _coregame_teams(payload, self.player_puuid)
        return LiveMatch(
            id=_match_id(payload, match_id),
            allies=_parse_live_players(allies, locked_by_default=True),
            enemies=_parse_live_players(enemies, locked_by_default=True),
        )

    def _get_current_match_id(self, game_phase: str) -> str | None:
        player = self._fetch_optional(
            f"/{game_phase}/v1/players/{self.player_puuid}"
        )
        match_id = player.get("MatchID") if player else None
        return match_id if isinstance(match_id, str) and match_id else None

    def get_player_names(self, puuids: Iterable[str]) -> dict[str, PlayerName]:
        unique_puuids = list(dict.fromkeys(puuid for puuid in puuids if puuid))
        if not unique_puuids:
            return {}

        return {
            puuid: PlayerName(puuid, name, tag)
            for puuid, (name, tag) in self._name_service.get_player_names(
                unique_puuids
            ).items()
        }

    def select_agent(self, match_id: str, agent: Agent) -> bool:
        return self._post_successfully(
            f"/pregame/v1/matches/{match_id}/select/{agent.uuid}"
        )

    def lock_agent(self, match_id: str, agent: Agent) -> bool:
        return self._post_successfully(
            f"/pregame/v1/matches/{match_id}/lock/{agent.uuid}"
        )

    def quit_pregame(self, match_id: str) -> bool:
        return self._post_successfully(f"/pregame/v1/matches/{match_id}/quit")

    def quit_coregame(self, match_id: str) -> bool:
        return self._post_successfully(
            f"/core-game/v1/players/{self.player_puuid}/disassociate/{match_id}"
        )

    def _post_successfully(self, endpoint: str) -> bool:
        try:
            self._client.post(endpoint, EndpointType.GLZ)
            return True
        except HTTPError:
            return False

    def close(self) -> None:
        self._client.close()


def _match_id(payload: JsonObject, fallback: str) -> str:
    match_id = payload.get("ID") or payload.get("MatchID")
    return match_id if isinstance(match_id, str) and match_id else fallback


def _team_players(team: object) -> list[JsonObject]:
    if isinstance(team, dict):
        team = team.get("Players", [])
    if not isinstance(team, list):
        return []
    return [player for player in team if isinstance(player, dict)]


def _coregame_teams(
    payload: JsonObject,
    current_player_id: str,
) -> tuple[list[JsonObject], list[JsonObject]]:
    allies = _team_players(payload.get("AllyTeam"))
    enemies = _team_players(payload.get("EnemyTeam"))
    if allies or enemies:
        return allies, enemies

    players = _team_players(payload.get("Players"))
    current_player = next(
        (player for player in players if player.get("Subject") == current_player_id),
        None,
    )
    ally_team_id = current_player.get("TeamID") if current_player else None
    if ally_team_id is None:
        return players, []

    return (
        [player for player in players if player.get("TeamID") == ally_team_id],
        [player for player in players if player.get("TeamID") != ally_team_id],
    )


def _parse_live_players(
    players: Iterable[JsonObject],
    *,
    locked_by_default: bool = False,
) -> tuple[LivePlayer, ...]:
    parsed: list[LivePlayer] = []
    for player in players:
        puuid = player.get("Subject")
        if not isinstance(puuid, str) or not puuid:
            continue

        selection_state = player.get("CharacterSelectionState")
        is_locked = locked_by_default or (
            isinstance(selection_state, str)
            and selection_state.casefold() == "locked"
        )
        parsed.append(
            LivePlayer(
                puuid=puuid,
                agent=Agent.from_uuid(player.get("CharacterID")),
                is_locked=is_locked,
            )
        )
    return tuple(parsed)
