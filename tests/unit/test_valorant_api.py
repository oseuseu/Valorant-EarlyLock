import unittest

from requests import HTTPError, Response

from earlylock.domain.models import Agent, GameState
from earlylock.infrastructure.riot.client import EndpointType
from earlylock.infrastructure.riot.api import ValorantApi


class StubRiotClient:
    player_name = "Tester"
    player_tag = "KR1"
    puuid = "player-1"

    def __init__(self, responses: dict[str, dict]) -> None:
        self.responses = responses
        self.requested: list[str] = []
        self.put_requests: list[tuple[str, object, object]] = []
        self.name_response: list[dict] = []
        self.closed = False

    def fetch(self, endpoint: str, endpoint_type: object) -> dict:
        self.requested.append(endpoint)
        if endpoint in self.responses:
            return self.responses[endpoint]

        response = Response()
        response.status_code = 404
        raise HTTPError(response=response)

    def post(
        self,
        endpoint: str,
        endpoint_type: object,
        json_data: dict | None = None,
    ) -> dict:
        return {}

    def put(
        self,
        endpoint: str,
        endpoint_type: object,
        json_data: object = None,
    ) -> list[dict]:
        self.put_requests.append((endpoint, endpoint_type, json_data))
        return self.name_response

    def close(self) -> None:
        self.closed = True


class ValorantApiTests(unittest.TestCase):
    def test_detects_pregame_without_coregame_request(self) -> None:
        pregame_endpoint = "/pregame/v1/players/player-1"
        client = StubRiotClient({pregame_endpoint: {"MatchID": "match-1"}})
        api = ValorantApi(client)  # type: ignore[arg-type]

        state = api.get_game_state()

        self.assertIs(state, GameState.PREGAME)
        self.assertEqual(client.requested, [pregame_endpoint])

    def test_returns_lobby_when_no_active_match_exists(self) -> None:
        client = StubRiotClient({})
        api = ValorantApi(client)  # type: ignore[arg-type]

        state = api.get_game_state()

        self.assertIs(state, GameState.LOBBY)
        self.assertEqual(len(client.requested), 2)

    def test_name_service_resolves_players_in_one_request(self) -> None:
        client = StubRiotClient({})
        client.name_response = [
            {
                "Subject": "player-1",
                "GameName": "Alpha",
                "TagLine": "KR1",
            },
            {
                "Subject": "player-2",
                "GameName": "Bravo",
                "TagLine": "1234",
            },
        ]
        api = ValorantApi(client)  # type: ignore[arg-type]

        names = api.get_player_names(["player-1", "player-2", "player-1"])

        self.assertEqual(names["player-1"].name, "Alpha")
        self.assertEqual(names["player-2"].tag, "1234")
        self.assertEqual(
            client.put_requests,
            [
                (
                    "/name-service/v2/players",
                    EndpointType.PD,
                    ["player-1", "player-2"],
                )
            ],
        )

    def test_builds_pregame_snapshot_with_resolved_names(self) -> None:
        match_endpoint = "/pregame/v1/matches/match-1"
        client = StubRiotClient(
            {
                match_endpoint: {
                    "ID": "match-1",
                    "AllyTeam": {
                        "TeamID": "Blue",
                        "Players": [
                            {
                                "Subject": "player-1",
                                "CharacterID": Agent.JETT.uuid,
                                "CharacterSelectionState": "locked",
                            }
                        ],
                    },
                }
            }
        )
        client.name_response = [
            {
                "Subject": "player-1",
                "GameName": "Alpha",
                "TagLine": "KR1",
            }
        ]
        api = ValorantApi(client)  # type: ignore[arg-type]

        snapshot = api.get_pregame_snapshot("match-1")

        self.assertIsNotNone(snapshot)
        assert snapshot is not None
        self.assertEqual(snapshot.players[0].name, "Alpha")
        self.assertIs(snapshot.players[0].agent, Agent.JETT)

    def test_builds_coregame_snapshot_with_all_players(self) -> None:
        match_endpoint = "/core-game/v1/matches/core-match-1"
        client = StubRiotClient(
            {
                match_endpoint: {
                    "MatchID": "core-match-1",
                    "Players": [
                        {
                            "Subject": "blue-player",
                            "TeamID": "Blue",
                            "CharacterID": Agent.SAGE.uuid,
                        },
                        {
                            "Subject": "red-player",
                            "TeamID": "Red",
                            "CharacterID": Agent.OMEN.uuid,
                        },
                    ],
                }
            }
        )
        client.name_response = [
            {
                "Subject": "blue-player",
                "GameName": "Alpha",
                "TagLine": "KR1",
            },
            {
                "Subject": "red-player",
                "GameName": "Bravo",
                "TagLine": "1234",
            },
        ]
        api = ValorantApi(client)  # type: ignore[arg-type]

        snapshot = api.get_coregame_snapshot("core-match-1")

        self.assertIsNotNone(snapshot)
        assert snapshot is not None
        self.assertEqual(len(snapshot.players), 2)
        self.assertEqual(snapshot.players[0].name, "Alpha")
        self.assertEqual(snapshot.players[1].name, "Bravo")
        self.assertEqual(
            client.put_requests[0][2],
            ["blue-player", "red-player"],
        )


if __name__ == "__main__":
    unittest.main()
