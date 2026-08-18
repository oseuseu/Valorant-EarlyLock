import sys
from collections.abc import Sequence

from PySide6.QtWidgets import QApplication

from earlylock.application.auto_pick import AutoPickService
from earlylock.infrastructure.riot.api import ValorantApi
from earlylock.infrastructure.riot.client import RiotClient
from earlylock.presentation.qt.main_dialog import MainDialog


def build_auto_pick_service() -> AutoPickService:
    client = RiotClient()
    gateway = ValorantApi(client)
    return AutoPickService(gateway)


def main(argv: Sequence[str] | None = None) -> int:
    app = QApplication(list(argv) if argv is not None else sys.argv)
    window = MainDialog(build_auto_pick_service)
    window.show()
    return app.exec()
