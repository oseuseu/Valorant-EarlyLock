import unittest
from collections.abc import Iterable

from earlylock.domain.models import Agent, GameState, LiveMatch, LivePlayer, PlayerName
from earlylock.infrastructure.riot.tracker import GameTracker


class FakeApi:
    def __init__(self) -> None:
        self.pregame_id: str | None = "pregame-id"
        self.coregame_id: str | None = None
        self.pregame = LiveMatch(
            id="pregame-id",
            allies=(LivePlayer("ally", Agent.JETT, True),),
        )
        self.coregame = LiveMatch(
            id="coregame-id",
            allies=(LivePlayer("ally", Agent.JETT, True),),
            enemies=(LivePlayer("enemy", Agent.SAGE, True),),
        )

    def get_pregame_id(self) -> str | None:
        return self.pregame_id

    def get_coregame_id(self) -> str | None:
        return self.coregame_id

    def get_pregame_match(self, match_id: str) -> LiveMatch:
        return self.pregame

    def get_coregame_match(self, match_id: str) -> LiveMatch:
        return self.coregame


class FakeResolver:
    def resolve_many(self, player_ids: Iterable[str]) -> dict[str, PlayerName]:
        return {
            player_id: PlayerName(player_id, player_id.title(), "KR1")
            for player_id in player_ids
        }


class FakeListener:
    def __init__(self) -> None:
        self.ended_matches: list[str] = []

    def on_coregame_end(self, match_id: str) -> None:
        self.ended_matches.append(match_id)


class GameTrackerTest(unittest.TestCase):
    def test_tracks_pregame_coregame_and_match_end(self) -> None:
        api = FakeApi()
        listener = FakeListener()
        tracker = GameTracker(api, FakeResolver(), listener)

        tracker.refresh()
        self.assertEqual(tracker.state, GameState.PREGAME)
        self.assertEqual(tracker.match_id, "pregame-id")
        self.assertEqual(tracker.players("Ally")[0].name, "Ally")

        api.coregame_id = "coregame-id"
        api.pregame_id = None
        tracker.refresh()
        self.assertEqual(tracker.state, GameState.IN_GAME)
        self.assertEqual(tracker.players("Enemy")[0].agent, Agent.SAGE)

        api.coregame_id = None
        tracker.refresh()
        self.assertEqual(tracker.state, GameState.LOBBY)
        self.assertEqual(tracker.players("Ally"), ())
        self.assertEqual(listener.ended_matches, ["coregame-id"])


if __name__ == "__main__":
    unittest.main()
