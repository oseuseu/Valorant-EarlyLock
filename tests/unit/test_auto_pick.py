import unittest

from earlylock.application.auto_pick import AutoPickService
from earlylock.domain.models import Agent, AutoPickSettings, GameState
from tests.fakes import FakeValorantGateway


class AutoPickServiceTests(unittest.TestCase):
    def test_pregame_is_emitted_once_until_state_changes(self) -> None:
        gateway = FakeValorantGateway(
            [
                GameState.LOBBY,
                GameState.PREGAME,
                GameState.PREGAME,
                GameState.IN_GAME,
                GameState.PREGAME,
            ]
        )
        service = AutoPickService(gateway)

        observations = [service.poll_game_state() for _ in range(5)]

        self.assertFalse(observations[0].pregame_started)
        self.assertTrue(observations[1].pregame_started)
        self.assertFalse(observations[2].pregame_started)
        self.assertTrue(observations[3].pregame_ended)
        self.assertTrue(observations[4].pregame_started)

    def test_pick_only_selects_without_locking(self) -> None:
        gateway = FakeValorantGateway()
        service = AutoPickService(gateway)
        settings = AutoPickSettings(agent=Agent.JETT, pick_only=True)

        result = service.pick_agent(settings)

        self.assertTrue(result.match_found)
        self.assertTrue(result.selected)
        self.assertIsNone(result.locked)
        self.assertEqual(gateway.selected, [("match-1", Agent.JETT)])
        self.assertEqual(gateway.locked, [])

    def test_regular_pick_selects_and_locks(self) -> None:
        gateway = FakeValorantGateway()
        service = AutoPickService(gateway)
        settings = AutoPickSettings(agent=Agent.SAGE, pick_only=False)

        result = service.pick_agent(settings)

        self.assertTrue(result.selected)
        self.assertTrue(result.locked)
        self.assertEqual(gateway.locked, [("match-1", Agent.SAGE)])

    def test_missing_match_does_not_call_pick_endpoints(self) -> None:
        gateway = FakeValorantGateway(match_id=None)
        service = AutoPickService(gateway)

        result = service.pick_agent(
            AutoPickSettings(agent=Agent.GEKKO, pick_only=False)
        )

        self.assertFalse(result.match_found)
        self.assertEqual(gateway.selected, [])
        self.assertEqual(gateway.locked, [])

    def test_close_releases_gateway(self) -> None:
        gateway = FakeValorantGateway()
        service = AutoPickService(gateway)

        service.close()

        self.assertTrue(gateway.closed)


if __name__ == "__main__":
    unittest.main()
