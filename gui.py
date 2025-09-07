import sys
from PyQt5 import QtWidgets, QtCore, QtGui
from task_scheduler import ScreenshotScheduler
from screenshoter import take_screenshots_mss
import os

def __init__(self):
    super().__intit__()
    self.scheduler = ScreenshotScheduler("screenshots.db")
    self.setup_ui()
    self.setup_tray()
    self.setup_signals()

def setup_gui(self):
    self.setWindowTitle('скриншотер')
    self.setGeometry(100, 100, 500, 400)

    central_widget = QtWidgets.QWidget()
    self.setCentralWidget(central_widget)
    layout = QtWidgets.QVBoxLayout(central_widget)


def setup_tray(self):
    if not QSystemTrayIcon.isSystemTrayAvailable():
        return

    self.tray_icon = QSystemTrayIcon(self)

    icon_path = os.path.join('media', 'icons', 'icon-16x16')

    if os.path.exists(icon_path):
        self.tray_icon.setIcon(QtGui.QIcon(icon_path))
    else:
        self.tray_icon.setIcon(self.style().standardIcon(QtWidgets.QStyle.SP_ComputerIcon))

    tray_menu = QMenu()


