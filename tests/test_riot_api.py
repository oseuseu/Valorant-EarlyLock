import unittest
from typing import Any

from earlylock.domain.models import Agent
from earlylock.infrastructure.riot.api import ValorantApi
from earlylock.infrastructure.riot.client import EndpointType


class FakeRiotClient:
    puuid = "current-player"
    player_name = "Player"
    player_tag = "KR1"

    def __init__(self, responses: dict[str, dict[str, Any]]) -> None:
        self.responses = responses

    def fetch(self, endpoint: str, endpoint_type: EndpointType) -> dict[str, Any]:
        return self.responses[endpoint]


class ValorantApiTest(unittest.TestCase):
    def test_parses_pregame_team_and_selection_state(self) -> None:
        client = FakeRiotClient(
            {
                "/pregame/v1/matches/pregame-id": {
                    "ID": "pregame-id",
                    "AllyTeam": {
                        "Players": [
                            {
                                "Subject": "ally-1",
                                "CharacterID": Agent.JETT.uuid.upper(),
                                "CharacterSelectionState": "locked",
                            },
                            {
                                "Subject": "ally-2",
                                "CharacterID": "unknown-agent",
                                "CharacterSelectionState": "selected",
                            },
                        ]
                    },
                }
            }
        )

        match = ValorantApi(client).get_pregame_match("pregame-id")

        self.assertIsNotNone(match)
        assert match is not None
        self.assertEqual(match.id, "pregame-id")
        self.assertEqual(match.allies[0].agent, Agent.JETT)
        self.assertTrue(match.allies[0].is_locked)
        self.assertIsNone(match.allies[1].agent)
        self.assertFalse(match.allies[1].is_locked)

    def test_splits_flat_coregame_players_using_current_team(self) -> None:
        client = FakeRiotClient(
            {
                "/core-game/v1/matches/coregame-id": {
                    "MatchID": "coregame-id",
                    "Players": [
                        {
                            "Subject": "current-player",
                            "TeamID": "Blue",
                            "CharacterID": Agent.SAGE.uuid,
                        },
                        {
                            "Subject": "ally-2",
                            "TeamID": "Blue",
                            "CharacterID": Agent.OMEN.uuid,
                        },
                        {
                            "Subject": "enemy-1",
                            "TeamID": "Red",
                            "CharacterID": Agent.RAZE.uuid,
                        },
                    ],
                }
            }
        )

        match = ValorantApi(client).get_coregame_match("coregame-id")

        self.assertIsNotNone(match)
        assert match is not None
        self.assertEqual(
            tuple(player.puuid for player in match.allies),
            ("current-player", "ally-2"),
        )
        self.assertEqual(
            tuple(player.puuid for player in match.enemies),
            ("enemy-1",),
        )
        self.assertTrue(all(player.is_locked for player in match.allies))
        self.assertTrue(all(player.is_locked for player in match.enemies))


if __name__ == "__main__":
    unittest.main()
