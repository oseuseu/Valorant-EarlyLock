import threading
import sys

from main_ui import MainUi
from PySide6.QtWidgets import QApplication

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainUi()
    window.show()
    app.exec()