import unittest

from earlylock.domain.models import Agent, GameState, PlayerName
from earlylock.infrastructure.riot.match_mapper import (
    from_coregame,
    from_pregame,
    get_ally_player_ids,
    get_coregame_player_ids,
)


class PregameMatchMapperTests(unittest.TestCase):
    def setUp(self) -> None:
        self.payload = {
            "ID": "match-1",
            "Teams": [
                {
                    "TeamID": "Red",
                    "Players": [{"Subject": "enemy-player"}],
                }
            ],
            "AllyTeam": {
                "TeamID": "Blue",
                "Players": [
                    {
                        "Subject": "player-1",
                        "CharacterID": Agent.PHOENIX.uuid,
                        "CharacterSelectionState": "locked",
                    },
                    {
                        "Subject": "player-2",
                        "CharacterID": "",
                        "CharacterSelectionState": "",
                    },
                ],
            },
            "EnemyTeam": None,
        }

    def test_maps_only_ally_team_players(self) -> None:
        names = {
            "player-1": PlayerName("player-1", "Alpha", "KR1"),
            "player-2": PlayerName("player-2", "Bravo", "1234"),
        }

        snapshot = from_pregame(self.payload, names)

        self.assertIs(snapshot.state, GameState.PREGAME)
        self.assertEqual(snapshot.match_id, "match-1")
        self.assertEqual(len(snapshot.players), 2)
        self.assertEqual(snapshot.players[0].name, "Alpha")
        self.assertEqual(snapshot.players[0].tag, "KR1")
        self.assertEqual(snapshot.players[0].team, "Blue")
        self.assertIs(snapshot.players[0].agent, Agent.PHOENIX)
        self.assertTrue(snapshot.players[0].is_lock)
        self.assertIsNone(snapshot.players[1].agent)
        self.assertFalse(snapshot.players[1].is_lock)

    def test_missing_name_is_kept_as_none(self) -> None:
        snapshot = from_pregame(self.payload)

        self.assertIsNone(snapshot.players[0].name)
        self.assertIsNone(snapshot.players[0].tag)

    def test_extracts_only_ally_player_ids(self) -> None:
        self.assertEqual(
            get_ally_player_ids(self.payload),
            ("player-1", "player-2"),
        )


class CoregameMatchMapperTests(unittest.TestCase):
    def setUp(self) -> None:
        self.payload = {
            "MatchID": "core-match-1",
            "Players": [
                {
                    "Subject": "blue-player",
                    "TeamID": "Blue",
                    "CharacterID": Agent.REYNA.uuid,
                },
                {
                    "Subject": "red-player",
                    "TeamID": "Red",
                    "CharacterID": Agent.SKYE.uuid,
                },
            ],
        }

    def test_maps_players_from_both_teams(self) -> None:
        names = {
            "blue-player": PlayerName("blue-player", "Alpha", "KR1"),
            "red-player": PlayerName("red-player", "Bravo", "1234"),
        }

        snapshot = from_coregame(self.payload, names)

        self.assertIs(snapshot.state, GameState.IN_GAME)
        self.assertEqual(snapshot.match_id, "core-match-1")
        self.assertEqual(len(snapshot.players), 2)
        self.assertEqual(snapshot.players[0].team, "Blue")
        self.assertIs(snapshot.players[0].agent, Agent.REYNA)
        self.assertEqual(snapshot.players[0].name, "Alpha")
        self.assertTrue(snapshot.players[0].is_lock)
        self.assertEqual(snapshot.players[1].team, "Red")
        self.assertIs(snapshot.players[1].agent, Agent.SKYE)
        self.assertEqual(snapshot.players[1].tag, "1234")
        self.assertTrue(snapshot.players[1].is_lock)

    def test_extracts_all_coregame_player_ids(self) -> None:
        self.assertEqual(
            get_coregame_player_ids(self.payload),
            ("blue-player", "red-player"),
        )


if __name__ == "__main__":
    unittest.main()
