from PySide6.QtWidgets import QDialog

from constants import Agent
from ui_dialog import Ui_Dialog


class MainUi(QDialog):
    def __init__(self):
        super().__init__()

        self.ui = Ui_Dialog()
        self.ui.setupUi(self)

        for agent in Agent:
            self.ui.selectedAgent.addItem(agent.display_name, agent)
