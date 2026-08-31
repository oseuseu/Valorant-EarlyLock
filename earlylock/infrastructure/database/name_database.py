import json
import shutil
import sys
from collections.abc import Iterable
from datetime import datetime
from pathlib import Path
from threading import RLock
from typing import Any

from earlylock.domain.models import PlayerName


def get_application_directory() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent / "data"
    return Path(__file__).resolve().parents[2] / "data"


DEFAULT_DATABASE_PATH = get_application_directory() / "player_name_database.json"


class PlayerNameDatabase:
    def __init__(self, path: Path = DEFAULT_DATABASE_PATH) -> None:
        self.path = Path(path)
        self._database: dict[str, dict[str, Any]] = {}
        self._lock = RLock()
        self.load_player_name_database()

    def load_player_name_database(self) -> dict[str, dict[str, Any]]:
        with self._lock:
            if not self.path.exists():
                self._database = {}
                self.save_player_name_database()
                return self._database

            try:
                raw_text = self.path.read_text(encoding="utf-8").strip()
                loaded = json.loads(raw_text) if raw_text else {}
                self._database = loaded if isinstance(loaded, dict) else {}
                if not raw_text or not isinstance(loaded, dict):
                    self.save_player_name_database()
            except (OSError, json.JSONDecodeError):
                self.backup_corrupted_database_file()
                self._database = {}
                self.save_player_name_database()

            return self._database

    def save_player_name_database(self) -> None:
        with self._lock:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            temp_path = self.path.with_suffix(f"{self.path.suffix}.tmp")
            temp_path.write_text(
                json.dumps(
                    self._database,
                    ensure_ascii=False,
                    indent=2,
                    sort_keys=True,
                ),
                encoding="utf-8",
            )
            temp_path.replace(self.path)

    def get_player_name_from_database(self, player_id: str) -> PlayerName | None:
        with self._lock:
            entry = self._database.get(player_id)
            if not isinstance(entry, dict):
                return None

            return PlayerName(
                id=player_id,
                name=entry.get("gameName"),
                tag=entry.get("tagLine"),
            )

    def upsert_player_name(self, player_name: PlayerName) -> bool:
        return bool(self.upsert_player_names((player_name,)))

    def upsert_player_names(self, player_names: Iterable[PlayerName]) -> int:
        changed_count = 0
        with self._lock:
            for player_name in player_names:
                if not player_name.name or not player_name.tag:
                    continue

                current = self._database.get(player_name.id, {})
                if not isinstance(current, dict):
                    current = {}
                updated = {
                    **current,
                    "gameName": player_name.name,
                    "tagLine": player_name.tag,
                }
                if updated == current:
                    continue

                self._database[player_name.id] = updated
                changed_count += 1

            if changed_count:
                self.save_player_name_database()

        return changed_count

    def backup_corrupted_database_file(self) -> Path | None:
        with self._lock:
            if not self.path.exists():
                return None

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = self.path.with_name(
                f"{self.path.stem}.corrupted.{timestamp}.bak"
            )
            try:
                shutil.copy2(self.path, backup_path)
                return backup_path
            except OSError:
                return None
