from collections.abc import Iterable

from earlylock.application.ports import PlayerNameGateway, PlayerNameRepository
from earlylock.domain.models import PlayerName


class PlayerNameResolver:
    def __init__(
        self,
        api: PlayerNameGateway,
        database: PlayerNameRepository,
    ) -> None:
        self._api = api
        self._database = database

    def resolve_many(self, puuids: Iterable[str]) -> dict[str, PlayerName]:
        requested = list(dict.fromkeys(puuid for puuid in puuids if puuid))
        if not requested:
            return {}

        api_results = self._api.get_player_names(requested)
        resolved = {
            puuid: player_name
            for puuid, player_name in api_results.items()
            if player_name.name and player_name.tag
        }
        self._database.upsert_player_names(resolved.values())

        for puuid in requested:
            if puuid in resolved:
                continue
            resolved[puuid] = (
                self._database.get_player_name_from_database(puuid)
                or PlayerName(id=puuid, name=None, tag=None)
            )

        return resolved
