import unittest
from typing import Any
from unittest.mock import Mock

from earlylock.models import Agent
from earlylock.game import GameTracker
from earlylock.name_finder import ValorantNameService
from earlylock.valorant_api import ValorantApi
from earlylock.riot_client import EndpointType


class FakeRiotClient:
    puuid = "current-player"
    player_name = "Player"
    player_tag = "KR1"

    def __init__(self, responses: dict[str, dict[str, Any]]) -> None:
        self.responses = responses

    def fetch(self, endpoint: str, endpoint_type: EndpointType) -> dict[str, Any]:
        return self.responses[endpoint]


class ValorantApiTest(unittest.TestCase):
    def setUp(self) -> None:
        self.name_service = Mock(spec=ValorantNameService)

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

        match = ValorantApi(client, self.name_service).get_pregame_match("pregame-id")

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

        match = ValorantApi(client, self.name_service).get_coregame_match("coregame-id")

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

    def test_resolves_hidden_players_by_puuid_through_name_finder(self) -> None:
        client = FakeRiotClient({
            "/pregame/v1/players/current-player": {"MatchID": "pregame-id"},
            "/pregame/v1/matches/pregame-id": {
                "ID": "pregame-id",
                "AllyTeam": {"Players": [
                    {"Subject": "hidden", "PlayerIdentity": {"Incognito": True}},
                    {"Subject": "visible", "PlayerIdentity": {"Incognito": False}},
                ]},
            },
        })
        self.name_service.get_player_names.return_value = {
            "hidden": ("HiddenPlayer", "KR1"),
            "visible": ("VisiblePlayer", "KR2"),
        }

        tracker = GameTracker(ValorantApi(client, self.name_service)).refresh()

        self.name_service.get_player_names.assert_called_once_with(["hidden", "visible"])
        self.assertEqual(
            [(player.name, player.tag) for player in tracker.players("Ally")],
            [("HiddenPlayer", "KR1"), ("VisiblePlayer", "KR2")],
        )


if __name__ == "__main__":
    unittest.main()
