# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'main_dialog.ui'
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
    QHBoxLayout, QPushButton, QSizePolicy, QTextBrowser,
    QVBoxLayout, QWidget)

class Ui_Dialog(object):
    def setupUi(self, Dialog):
        if not Dialog.objectName():
            Dialog.setObjectName(u"Dialog")
        Dialog.resize(400, 600)
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(Dialog.sizePolicy().hasHeightForWidth())
        Dialog.setSizePolicy(sizePolicy)
        self.verticalLayout = QVBoxLayout(Dialog)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setSpacing(10)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalLayout.setContentsMargins(0, -1, -1, -1)
        self.selectedAgent = QComboBox(Dialog)
        self.selectedAgent.setObjectName(u"selectedAgent")

        self.horizontalLayout.addWidget(self.selectedAgent)

        self.startToggleButton = QPushButton(Dialog)
        self.startToggleButton.setObjectName(u"startToggleButton")

        self.horizontalLayout.addWidget(self.startToggleButton)

        self.quitButton = QPushButton(Dialog)
        self.quitButton.setObjectName(u"quitButton")

        self.horizontalLayout.addWidget(self.quitButton)


        self.verticalLayout.addLayout(self.horizontalLayout)

        self.pickOnlyCheckBox = QCheckBox(Dialog)
        self.pickOnlyCheckBox.setObjectName(u"pickOnlyCheckBox")
        font = QFont()
        font.setPointSize(9)
        self.pickOnlyCheckBox.setFont(font)

        self.verticalLayout.addWidget(self.pickOnlyCheckBox)

        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setSpacing(12)
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.teamTextBox = QTextBrowser(Dialog)
        self.teamTextBox.setObjectName(u"teamTextBox")
        font1 = QFont()
        font1.setPointSize(10)
        font1.setBold(True)
        self.teamTextBox.setFont(font1)

        self.horizontalLayout_2.addWidget(self.teamTextBox)

        self.enemyTextBox = QTextBrowser(Dialog)
        self.enemyTextBox.setObjectName(u"enemyTextBox")
        self.enemyTextBox.setFont(font1)

        self.horizontalLayout_2.addWidget(self.enemyTextBox)


        self.verticalLayout.addLayout(self.horizontalLayout_2)

        self.logTextBrowser = QTextBrowser(Dialog)
        self.logTextBrowser.setObjectName(u"logTextBrowser")

        self.verticalLayout.addWidget(self.logTextBrowser)

        self.verticalLayout.setStretch(2, 1)
        self.verticalLayout.setStretch(3, 1)

        self.retranslateUi(Dialog)

        QMetaObject.connectSlotsByName(Dialog)
    # setupUi

    def retranslateUi(self, Dialog):
        Dialog.setWindowTitle(QCoreApplication.translate("Dialog", u"EarlyPick", None))
        self.startToggleButton.setText(QCoreApplication.translate("Dialog", u"\uc2dc\uc791/\uc885\ub8cc", None))
        self.quitButton.setText(QCoreApplication.translate("Dialog", u"\uac8c\uc784 \ub098\uac00\uae30", None))
        self.pickOnlyCheckBox.setText(QCoreApplication.translate("Dialog", u"pick only", None))
    # retranslateUi

