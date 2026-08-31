import time
from threading import Thread

from requests import RequestException

from earlylock.infrastructure.database.name_database import PlayerNameDatabase
from earlylock.infrastructure.riot.api import ValorantApi


class EarlyPickGameEventListener:
    MATCH_DETAIL_ATTEMPTS = 10
    RETRY_DELAY_SECONDS = 1.0

    def __init__(self, api: ValorantApi, database: PlayerNameDatabase) -> None:
        self._api = api
        self._database = database

    def on_coregame_end(self, match_id: str) -> None:
        Thread(
            target=self._save_match_players,
            args=(match_id,),
            daemon=True,
            name=f"match-name-cache-{match_id}",
        ).start()

    def _save_match_players(self, match_id: str) -> bool:
        for attempt in range(self.MATCH_DETAIL_ATTEMPTS):
            try:
                player_ids = self._api.get_match_player_ids(match_id)
                if player_ids is not None:
                    names = self._api.get_player_names(player_ids)
                    self._database.upsert_player_names(names.values())
                    return True
            except RequestException:
                pass

            if attempt + 1 < self.MATCH_DETAIL_ATTEMPTS:
                time.sleep(self.RETRY_DELAY_SECONDS)

        return False
