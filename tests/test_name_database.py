import json
import tempfile
import unittest
from pathlib import Path

from earlylock.domain.models import PlayerName
from earlylock.infrastructure.database.name_database import PlayerNameDatabase


class PlayerNameDatabaseTest(unittest.TestCase):
    def test_upserts_many_with_one_file_write_and_reloads(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "players.json"
            database = PlayerNameDatabase(path)

            changed = database.upsert_player_names(
                (
                    PlayerName("one", "First", "KR1"),
                    PlayerName("two", "Second", "KR2"),
                    PlayerName("invalid", None, None),
                )
            )

            self.assertEqual(changed, 2)
            self.assertEqual(
                PlayerNameDatabase(path).get_player_name_from_database("two"),
                PlayerName("two", "Second", "KR2"),
            )
            saved = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(set(saved), {"one", "two"})


if __name__ == "__main__":
    unittest.main()
