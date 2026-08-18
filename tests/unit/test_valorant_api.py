import unittest

from requests import HTTPError, Response

from earlylock.domain.models import GameState
from earlylock.infrastructure.riot.api import ValorantApi


class StubRiotClient:
    player_name = "Tester"
    player_tag = "KR1"
    puuid = "player-1"

    def __init__(self, responses: dict[str, dict]) -> None:
        self.responses = responses
        self.requested: list[str] = []
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


if __name__ == "__main__":
    unittest.main()
