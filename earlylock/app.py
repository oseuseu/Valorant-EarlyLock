import sys
from collections.abc import Sequence

from PySide6.QtWidgets import QApplication

from earlylock.application.auto_pick import AutoPickService
from earlylock.application.name_resolver import PlayerNameResolver
from earlylock.infrastructure.database.name_database import PlayerNameDatabase
from earlylock.infrastructure.riot.api import ValorantApi
from earlylock.infrastructure.riot.client import RiotClient
from earlylock.infrastructure.riot.event_listener import EarlyPickGameEventListener
from earlylock.infrastructure.riot.tracker import GameTracker
from earlylock.presentation.qt.main_dialog import MainDialog


def build_auto_pick_service() -> AutoPickService:
    client = RiotClient()
    gateway = ValorantApi(client)
    database = PlayerNameDatabase()
    resolver = PlayerNameResolver(gateway, database)
    listener = EarlyPickGameEventListener(gateway, database)
    tracker = GameTracker(api=gateway, resolver=resolver, listener=listener)
    return AutoPickService(gateway, tracker)


def main(argv: Sequence[str] | None = None) -> int:
    app = QApplication(list(argv) if argv is not None else sys.argv)
    window = MainDialog(build_auto_pick_service)
    window.show()
    return app.exec()
