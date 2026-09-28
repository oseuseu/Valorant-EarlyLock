import sys
from collections.abc import Sequence

from PySide6.QtWidgets import QApplication

from earlylock.game import AutoPickService
from earlylock.name_finder import ValorantNameService
from earlylock.riot_client import RiotClient
from earlylock.ui import MainDialog
from earlylock.valorant_api import ValorantApi


def build_auto_pick_service() -> AutoPickService:
    name_service = ValorantNameService()
    return AutoPickService(ValorantApi(RiotClient(), name_service))


def main(argv: Sequence[str] | None = None) -> int:
    app = QApplication(list(argv) if argv is not None else sys.argv)
    window = MainDialog(build_auto_pick_service)
    window.show()
    return app.exec()
