# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'testui.ui'
##
## Created by: Qt User Interface Compiler version 6.11.1
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
    QFont, QFontDatabase, QGradient, QIcon,
    QImage, QKeySequence, QLinearGradient, QPainter,
    QPalette, QPixmap, QRadialGradient, QTransform)
from PySide6.QtWidgets import (QApplication, QCheckBox, QComboBox, QDialog,
    QHBoxLayout, QListWidget, QListWidgetItem, QPushButton,
    QSizePolicy, QTextBrowser, QWidget)

class Ui_Dialog(object):
    def setupUi(self, Dialog):
        if not Dialog.objectName():
            Dialog.setObjectName(u"Dialog")
        Dialog.resize(400, 600)
        self.horizontalLayoutWidget = QWidget(Dialog)
        self.horizontalLayoutWidget.setObjectName(u"horizontalLayoutWidget")
        self.horizontalLayoutWidget.setGeometry(QRect(20, 10, 361, 41))
        self.horizontalLayout = QHBoxLayout(self.horizontalLayoutWidget)
        self.horizontalLayout.setSpacing(10)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalLayout.setContentsMargins(0, 0, 0, 0)
        self.selectedAgent = QComboBox(self.horizontalLayoutWidget)
        self.selectedAgent.setObjectName(u"selectedAgent")

        self.horizontalLayout.addWidget(self.selectedAgent)

        self.startToggleButton = QPushButton(self.horizontalLayoutWidget)
        self.startToggleButton.setObjectName(u"startToggleButton")

        self.horizontalLayout.addWidget(self.startToggleButton)

        self.quitButton = QPushButton(self.horizontalLayoutWidget)
        self.quitButton.setObjectName(u"quitButton")

        self.horizontalLayout.addWidget(self.quitButton)

        self.horizontalLayoutWidget_2 = QWidget(Dialog)
        self.horizontalLayoutWidget_2.setObjectName(u"horizontalLayoutWidget_2")
        self.horizontalLayoutWidget_2.setGeometry(QRect(20, 110, 361, 141))
        self.horizontalLayout_2 = QHBoxLayout(self.horizontalLayoutWidget_2)
        self.horizontalLayout_2.setSpacing(12)
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.horizontalLayout_2.setContentsMargins(0, 0, 0, 0)
        self.teamList = QListWidget(self.horizontalLayoutWidget_2)
        __qlistwidgetitem = QListWidgetItem(self.teamList)
        __qlistwidgetitem.setTextAlignment(Qt.AlignLeading|Qt.AlignVCenter)
        QListWidgetItem(self.teamList)
        QListWidgetItem(self.teamList)
        QListWidgetItem(self.teamList)
        QListWidgetItem(self.teamList)
        self.teamList.setObjectName(u"teamList")
        font = QFont()
        font.setPointSize(10)
        font.setBold(True)
        self.teamList.setFont(font)

        self.horizontalLayout_2.addWidget(self.teamList)

        self.enemyList = QListWidget(self.horizontalLayoutWidget_2)
        __qlistwidgetitem1 = QListWidgetItem(self.enemyList)
        __qlistwidgetitem1.setTextAlignment(Qt.AlignLeading|Qt.AlignVCenter)
        QListWidgetItem(self.enemyList)
        QListWidgetItem(self.enemyList)
        QListWidgetItem(self.enemyList)
        QListWidgetItem(self.enemyList)
        self.enemyList.setObjectName(u"enemyList")
        self.enemyList.setFont(font)

        self.horizontalLayout_2.addWidget(self.enemyList)

        self.pickOnlyCheckBox = QCheckBox(Dialog)
        self.pickOnlyCheckBox.setObjectName(u"pickOnlyCheckBox")
        self.pickOnlyCheckBox.setGeometry(QRect(20, 60, 81, 16))
        font1 = QFont()
        font1.setPointSize(9)
        self.pickOnlyCheckBox.setFont(font1)
        self.logTextBrowser = QTextBrowser(Dialog)
        self.logTextBrowser.setObjectName(u"logTextBrowser")
        self.logTextBrowser.setGeometry(QRect(20, 280, 361, 301))

        self.retranslateUi(Dialog)

        QMetaObject.connectSlotsByName(Dialog)
    # setupUi

    def retranslateUi(self, Dialog):
        Dialog.setWindowTitle(QCoreApplication.translate("Dialog", "Early Pick", None))
        self.startToggleButton.setText(QCoreApplication.translate("Dialog", "시작/종료", None))
        self.quitButton.setText(QCoreApplication.translate("Dialog", "게임 나가기", None))

        self.pickOnlyCheckBox.setText(QCoreApplication.translate("Dialog", "pick only", None))
    # retranslateUi

