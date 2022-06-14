import importlib.resources
import logging
import sys

import qdarktheme

from PySide6 import QtCore, QtGui
from PySide6.QtWidgets import QApplication

import pyqtgraph as pg

from acconeer.exptool.app import resources  # type: ignore[attr-defined]

from .app_model import AppModel
from .backend import Backend
from .plugin_loader import load_default_plugins
from .ui import MainWindow


def main():
    logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)

    backend = Backend()
    backend.start()

    model = AppModel(backend, load_default_plugins())
    model.start()

    pg.setConfigOption("background", "w")
    pg.setConfigOption("foreground", "k")
    pg.setConfigOption("leftButtonPan", False)
    pg.setConfigOptions(antialias=True)

    QApplication.setHighDpiScaleFactorRoundingPolicy(
        QtCore.Qt.HighDpiScaleFactorRoundingPolicy.PassThrough,
    )
    QtCore.QCoreApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling, True)

    app = QApplication(sys.argv)

    app.setStyleSheet(qdarktheme.load_stylesheet("light"))
    app.setAttribute(QtCore.Qt.ApplicationAttribute.AA_UseHighDpiPixmaps)

    with importlib.resources.path(resources, "icon.png") as path:
        app.setWindowIcon(_pixmap_to_icon(QtGui.QPixmap(str(path))))

    mw = MainWindow(model)
    mw.show()

    model.broadcast()

    app.exec()

    model.stop()
    backend.stop()


def _pixmap_to_icon(pixmap: QtGui.QPixmap) -> QtGui.QIcon:
    size = max(pixmap.size().height(), pixmap.size().width())

    square_pixmap = QtGui.QPixmap(size, size)
    square_pixmap.fill(QtGui.Qt.transparent)

    painter = QtGui.QPainter(square_pixmap)
    painter.drawPixmap(
        (square_pixmap.size().width() - pixmap.size().width()) // 2,
        (square_pixmap.size().height() - pixmap.size().height()) // 2,
        pixmap,
    )
    painter.end()

    scaled_pixmap = square_pixmap.scaled(
        256,
        256,
        aspectMode=QtGui.Qt.KeepAspectRatio,
        mode=QtGui.Qt.SmoothTransformation,
    )

    return QtGui.QIcon(scaled_pixmap)
