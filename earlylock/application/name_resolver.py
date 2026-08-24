from typing import Iterable

from earlylock.domain.models import PlayerName
from earlylock.infrastructure.database.name_database import PlayerNameDatabase
from earlylock.infrastructure.riot.api import ValorantApi


class PlayerNameResolver:
    def __init__(
            self,
            api: ValorantApi,
            database: PlayerNameDatabase
    ) -> None:
        self._api = api
        self._database = database

    def resolve_many(
        self,
        puuids: Iterable[str],
    ) -> dict[str, PlayerName]:
        requested = list(dict.fromkeys(puuid for puuid in puuids if puuid))

        api_results = self._api.get_player_names(requested)

        # name/tag가 모두 있어야 API 조회 성공으로 취급
        resolved = {
            puuid: player_name
            for puuid, player_name in api_results.items()
            if player_name.name and player_name.tag
        }
        
        missing_puuids = [
            puuid for puuid in requested
            if puuid not in resolved
        ]

        for puuid in missing_puuids:
            cached = self._database.get_player_name_from_database(puuid)
            if cached is not None:
                resolved[puuid] = cached
            else:
                resolved[puuid] = PlayerName(id=puuid, name=None, tag=None)

        return resolved

        