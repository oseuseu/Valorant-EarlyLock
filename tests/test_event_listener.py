import unittest
from collections.abc import Iterable

from earlylock.domain.models import PlayerName
from earlylock.infrastructure.riot.event_listener import EarlyPickGameEventListener


class FakeApi:
    def __init__(self) -> None:
        self.calls = 0

    def get_match_player_ids(self, match_id: str) -> tuple[str, ...] | None:
        self.calls += 1
        return None if self.calls == 1 else ("player-id",)

    def get_player_names(
        self,
        player_ids: Iterable[str],
    ) -> dict[str, PlayerName]:
        return {"player-id": PlayerName("player-id", "Player", "KR1")}


class FakeDatabase:
    def __init__(self) -> None:
        self.saved: list[PlayerName] = []

    def upsert_player_names(self, player_names: Iterable[PlayerName]) -> int:
        names = list(player_names)
        self.saved.extend(names)
        return len(names)


class EarlyPickGameEventListenerTest(unittest.TestCase):
    def test_retries_and_stores_player_name_values(self) -> None:
        api = FakeApi()
        database = FakeDatabase()
        listener = EarlyPickGameEventListener(api, database)
        listener.MATCH_DETAIL_ATTEMPTS = 2
        listener.RETRY_DELAY_SECONDS = 0

        saved = listener._save_match_players("match-id")

        self.assertTrue(saved)
        self.assertEqual(api.calls, 2)
        self.assertEqual(
            database.saved,
            [PlayerName("player-id", "Player", "KR1")],
        )


if __name__ == "__main__":
    unittest.main()
