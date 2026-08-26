import threading
import time

from typing import Protocol

from earlylock.infrastructure.riot.api import ValorantApi
from earlylock.infrastructure.database.name_database import PlayerNameDatabase

class GameEventListener(Protocol):
    def on_lobby_enter(self) -> None:
        ...

    def on_pregame_start(self) -> None:
        ...

    def on_pregame_cancel(self) -> None:
        ...

    def on_coregame_start(self) -> None:
        ...

    def on_coregame_end(self, match_id: str) -> None:
        ...


class EarlyPickGameEventListener:
    def __init__(self, api: ValorantApi, database: PlayerNameDatabase):
        self._api = api
        self._database = database

    def on_lobby_enter(self) -> None:
        ...

    def on_pregame_start(self) -> None:
        ...

    def on_pregame_cancel(self) -> None:
        ...

    def on_coregame_start(self) -> None:
        ...

    def on_coregame_end(self, match_id: str) -> None:
        return None # todo: disabled

        threading.Thread(
            target=self._save_match_players, 
            args=(match_id,)
        ).start()

    def _save_match_players(self, match_id: str) -> None:
        save = False
        for i in range(10):
            match_detail = self._api.get_match_details(match_id)
            players = match_detail.get("players", [])
            for player in players:
                pass # todo
            if match_detail:
                save = True
                break
            time.sleep(1.0)
        if not save:
            print("시간초과")

        
