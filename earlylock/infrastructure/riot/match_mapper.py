from collections.abc import Mapping
from typing import Any

from earlylock.domain.models import (
    Agent,
    GameState,
    MatchSnapshot,
    PlayerName,
    PlayerSnapshot,
)


def get_ally_player_ids(payload: Mapping[str, Any]) -> tuple[str, ...]:
    ally_team = payload.get("AllyTeam") or {}
    players = ally_team.get("Players") or []
    return tuple(
        player["Subject"]
        for player in players
        if isinstance(player, dict) and player.get("Subject")
    )


def get_coregame_player_ids(payload: Mapping[str, Any]) -> tuple[str, ...]:
    return tuple(
        player["Subject"]
        for player in payload.get("Players") or []
        if isinstance(player, dict) and player.get("Subject")
    )


def from_pregame(
    payload: Mapping[str, Any],
    player_names: Mapping[str, PlayerName] | None = None,
) -> MatchSnapshot:
    ally_team = payload.get("AllyTeam") or {}
    team_id = ally_team.get("TeamID")
    names_by_puuid = player_names or {}

    players = tuple(
        _map_pregame_player(player, team_id, names_by_puuid)
        for player in ally_team.get("Players") or []
        if isinstance(player, dict) and player.get("Subject")
    )

    return MatchSnapshot(
        state=GameState.PREGAME,
        match_id=payload.get("ID"),
        players=players,
    )


def _map_pregame_player(
    payload: Mapping[str, Any],
    team_id: str | None,
    player_names: Mapping[str, PlayerName],
) -> PlayerSnapshot:
    puuid = str(payload["Subject"])
    player_name = player_names.get(puuid)

    return PlayerSnapshot(
        puuid=puuid,
        name=player_name.name if player_name else None,
        tag=player_name.tag if player_name else None,
        team=team_id,
        agent=_find_agent(payload.get("CharacterID")),
        is_lock=payload.get("CharacterSelectionState") == "locked",
    )


def _find_agent(agent_uuid: object) -> Agent | None:
    if not isinstance(agent_uuid, str) or not agent_uuid:
        return None

    normalized_uuid = agent_uuid.casefold()
    return next(
        (agent for agent in Agent if agent.uuid.casefold() == normalized_uuid),
        None,
    )


def from_coregame(
    payload: Mapping[str, Any],
    player_names: Mapping[str, PlayerName] | None = None,
) -> MatchSnapshot:
    names_by_puuid = player_names or {}
    players = tuple(
        _map_coregame_player(player, names_by_puuid)
        for player in payload.get("Players") or []
        if isinstance(player, dict) and player.get("Subject")
    )

    return MatchSnapshot(
        state=GameState.IN_GAME,
        match_id=payload.get("MatchID"),
        players=players,
    )


def _map_coregame_player(
    payload: Mapping[str, Any],
    player_names: Mapping[str, PlayerName],
) -> PlayerSnapshot:
    puuid = str(payload["Subject"])
    player_name = player_names.get(puuid)
    agent = _find_agent(payload.get("CharacterID"))

    return PlayerSnapshot(
        puuid=puuid,
        name=player_name.name if player_name else None,
        tag=player_name.tag if player_name else None,
        team=payload.get("TeamID"),
        agent=agent,
        is_lock=agent is not None,
    )
