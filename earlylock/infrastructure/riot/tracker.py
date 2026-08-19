from dataclasses import dataclass
from typing import Any, Literal, Self

from earlylock.domain.models import Agent, GameState, PlayerName
from earlylock.infrastructure.riot.api import ValorantApi

Team = Literal["Ally", "Enemy"]


@dataclass
class Player:
    puuid: str
    name: str | None
    tag: str | None

    team: Team | None
    agent: Agent | None
    is_lock: bool = False


class GameTracker:
    def __init__(self, api: ValorantApi) -> None:
        self._api = api
        self._game_state = GameState.LOBBY
        self._match_id: str | None = None
        self._players: dict[Team, list[Player]] = {
            "Ally": [],
            "Enemy": [],
        }

    def get_game_state(self) -> GameState:
        return self._game_state

    def get_match_id(self) -> str | None:
        return self._match_id

    def get_players(self, team: Team) -> tuple[Player, ...]:
        return tuple(self._players[team])

    def lobby(self) -> Self:
        self._game_state = GameState.LOBBY
        self._match_id = None
        self._players = {
            "Ally": [],
            "Enemy": [],
        }
        return self

    def refresh(self) -> Self:
        match self._game_state:
            case GameState.LOBBY:
                pregame_id = self._api.get_pregame_id()
                if pregame_id is not None:
                    pregame = self._api.get_pregame_match(pregame_id)
                    if pregame is not None:
                        self.update_from_pregame(pregame, pregame_id)
                    return self

                coregame_id = self._api.get_coregame_id()
                if coregame_id is not None:
                    coregame = self._api.get_coregame_match(coregame_id)
                    if coregame is not None:
                        self.update_from_coregame(coregame, coregame_id)
                return self

            case GameState.PREGAME:
                coregame_id = self._api.get_coregame_id()
                if coregame_id is not None:
                    coregame = self._api.get_coregame_match(coregame_id)
                    if coregame is not None:
                        self.update_from_coregame(coregame, coregame_id)
                    return self

                pregame_id = self._api.get_pregame_id()
                if pregame_id is None:
                    return self.lobby()

                pregame = self._api.get_pregame_match(pregame_id)
                if pregame is not None:
                    self.update_from_pregame(pregame, pregame_id)
                return self

            case GameState.IN_GAME:
                coregame_id = self._api.get_coregame_id()
                if coregame_id is None:
                    return self.lobby()

                coregame = self._api.get_coregame_match(coregame_id)
                if coregame is not None:
                    self.update_from_coregame(coregame, coregame_id)

        return self

    def update_from_pregame(
        self,
        payload: dict[str, Any],
        match_id: str | None = None,
    ) -> None:
        ally_team = payload.get("AllyTeam") or {}
        players = ally_team.get("Players") or []

        puuids = (
            player.get("Subject")
            for player in players
            if isinstance(player, dict)
        )
        names = self._api.get_player_names(puuids)

        ally_players = self._get_players(ally_team, names, "Ally")

        self._game_state = GameState.PREGAME
        self._match_id = payload.get("ID") or match_id
        self._players = {
            "Ally": ally_players,
            "Enemy": [],
        }

    def update_from_coregame(
        self,
        payload: dict[str, Any],
        match_id: str | None = None,
    ) -> None:
        ally_team, enemy_team = self._get_coregame_teams(payload)

        players = (
            (ally_team.get("Players") or [])
            + (enemy_team.get("Players") or [])
        )
        puuids = (
            player.get("Subject")
            for player in players
            if isinstance(player, dict)
        )
        names = self._api.get_player_names(puuids)

        ally_players = self._get_players(ally_team, names, "Ally")
        enemy_players = self._get_players(enemy_team, names, "Enemy")

        self._game_state = GameState.IN_GAME
        self._match_id = payload.get("MatchID") or match_id
        self._players = {
            "Ally": ally_players,
            "Enemy": enemy_players,
        }

    def _get_coregame_teams(
        self,
        payload: dict[str, Any],
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        ally_team = payload.get("AllyTeam") or {}
        enemy_team = payload.get("EnemyTeam") or {}
        if ally_team or enemy_team:
            return ally_team, enemy_team

        players = payload.get("Players") or []
        current_player = next(
            (
                player
                for player in players
                if isinstance(player, dict)
                and player.get("Subject") == self._api.player_puuid
            ),
            None,
        )
        ally_team_id = current_player.get("TeamID") if current_player else None
        if ally_team_id is None:
            return {"Players": players}, {"Players": []}

        return (
            {
                "Players": [
                    player
                    for player in players
                    if isinstance(player, dict)
                    and player.get("TeamID") == ally_team_id
                ]
            },
            {
                "Players": [
                    player
                    for player in players
                    if isinstance(player, dict)
                    and player.get("TeamID") != ally_team_id
                ]
            },
        )

    def _get_players(
        self,
        payload: dict[str, Any],
        names: dict[str, PlayerName],
        team: Team,
    ) -> list[Player]:
        players = payload.get("Players") or []
        result: list[Player] = []

        for player in players:
            if not isinstance(player, dict):
                continue
            puuid = player.get("Subject")
            if not isinstance(puuid, str) or not puuid:
                continue

            player_name = names.get(puuid)

            agent = self._get_agent(player.get("CharacterID"))
            selection_state = player.get("CharacterSelectionState")
            is_lock = (
                selection_state == "locked"
                if selection_state is not None
                else agent is not None
            )

            result.append(
                Player(
                    puuid=puuid,
                    name=player_name.name if player_name else None,
                    tag=player_name.tag if player_name else None,
                    team=team,
                    agent=agent,
                    is_lock=is_lock,
                )
            )

        return result

    def _get_agent(self, uuid: str | None) -> Agent | None:
        if not isinstance(uuid, str) or not uuid:
            return None

        for agent in Agent:
            if agent.uuid.casefold() == uuid.casefold():
                return agent
        return None
