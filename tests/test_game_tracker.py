import unittest
from collections.abc import Iterable

from requests import ConnectionError

from earlylock.models import (
    Agent, AutoPickSettings, GameState, LiveMatch, LivePlayer, PlayerName,
)
from earlylock.game import AutoPickService, GameTracker


class FakeApi:
    player_name = "Player"
    player_tag = "KR1"

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
        self.name_requests: list[list[str]] = []
        self.name_error = False
        self.missing_names: set[str] = set()
        self.selected: list[tuple[str, Agent]] = []

    def get_pregame_id(self) -> str | None:
        return self.pregame_id

    def get_coregame_id(self) -> str | None:
        return self.coregame_id

    def get_pregame_match(self, match_id: str) -> LiveMatch:
        return self.pregame

    def get_coregame_match(self, match_id: str) -> LiveMatch:
        return self.coregame

    def get_player_names(self, player_ids: Iterable[str]) -> dict[str, PlayerName]:
        player_ids = list(player_ids)
        self.name_requests.append(player_ids)
        if self.name_error:
            raise ConnectionError("Name lookup unavailable")
        return {
            player_id: PlayerName(player_id, player_id.title(), "KR1")
            for player_id in player_ids
            if player_id not in self.missing_names
        }

    def select_agent(self, match_id: str, agent: Agent) -> bool:
        self.selected.append((match_id, agent))
        return True

    def lock_agent(self, match_id: str, agent: Agent) -> bool:
        raise AssertionError("Automatic locking must remain disabled")


class GameTrackerTest(unittest.TestCase):
    def test_tracks_pregame_coregame_and_match_end(self) -> None:
        api = FakeApi()
        tracker = GameTracker(api)

        tracker.refresh()
        self.assertEqual(tracker.state, GameState.PREGAME)
        self.assertEqual(tracker.match_id, "pregame-id")
        self.assertEqual(tracker.players("Ally")[0].name, "Ally")

        api.coregame_id = "coregame-id"
        api.pregame_id = None
        tracker.refresh()
        self.assertEqual(tracker.state, GameState.IN_GAME)
        self.assertEqual(tracker.players("Enemy")[0].agent, Agent.SAGE)
        self.assertEqual(tracker.players("Enemy")[0].name, "Enemy")

        api.coregame_id = None
        tracker.refresh()
        self.assertEqual(tracker.state, GameState.LOBBY)
        self.assertEqual(tracker.players("Ally"), ())
        self.assertEqual(tracker.players("Enemy"), ())
        self.assertEqual(len(api.name_requests), 2)

    def test_reuses_names_but_refreshes_agent_selection(self) -> None:
        api = FakeApi()
        tracker = GameTracker(api).refresh()
        api.pregame = LiveMatch("pregame-id", (LivePlayer("ally", Agent.SAGE),))

        tracker.refresh()

        self.assertEqual(api.name_requests, [["ally"]])
        self.assertEqual(tracker.players("Ally")[0].agent, Agent.SAGE)
        self.assertFalse(tracker.players("Ally")[0].is_locked)

    def test_retries_only_missing_names(self) -> None:
        api = FakeApi()
        api.pregame = LiveMatch("pregame-id", (
            LivePlayer("ally", None), LivePlayer("hidden", None),
        ))
        api.missing_names = {"hidden"}
        tracker = GameTracker(api).refresh()
        self.assertIsNone(tracker.players("Ally")[1].name)

        api.missing_names.clear()
        tracker.refresh()

        self.assertEqual(api.name_requests, [["ally", "hidden"], ["hidden"]])
        self.assertEqual(tracker.players("Ally")[1].name, "Hidden")

    def test_lookup_failure_does_not_block_selection_and_is_retried(self) -> None:
        api = FakeApi()
        api.name_error = True
        service = AutoPickService(api)

        observation = service.poll_game_state()
        self.assertTrue(observation.pregame_started)
        self.assertIsNone(observation.tracker.players("Ally")[0].name)
        result = service.pick_agent(AutoPickSettings(Agent.JETT, pick_only=False))
        self.assertTrue(result.selected)
        self.assertIsNone(result.locked)
        self.assertEqual(api.selected, [("pregame-id", Agent.JETT)])

        api.name_error = False
        observation = service.poll_game_state()
        self.assertFalse(observation.pregame_started)
        self.assertEqual(observation.tracker.players("Ally")[0].name, "Ally")

    def test_clears_names_when_match_ends_or_changes(self) -> None:
        api = FakeApi()
        tracker = GameTracker(api).refresh()
        api.pregame_id = None
        tracker.refresh()
        self.assertEqual(tracker.state, GameState.LOBBY)

        api.pregame_id = "pregame-id"
        tracker.refresh()
        api.pregame_id = "next-match"
        api.pregame = LiveMatch("next-match", (LivePlayer("ally", None),))
        tracker.refresh()
        self.assertEqual(api.name_requests, [["ally"], ["ally"], ["ally"]])

    def test_does_not_select_outside_pregame(self) -> None:
        api = FakeApi()
        api.pregame_id = None
        result = AutoPickService(api).pick_agent(
            AutoPickSettings(Agent.JETT, pick_only=True)
        )
        self.assertFalse(result.match_found)
        self.assertEqual(api.selected, [])


if __name__ == "__main__":
    unittest.main()
