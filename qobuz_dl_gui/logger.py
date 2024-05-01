import logging
from PyQt5.QtCore import QObject, pyqtSignal
from PyQt5.QtGui import QTextCursor, QColor
from PyQt5 import QtWidgets


class QPlainTextEditLogger(QObject, logging.Handler):
    appendPlainText = pyqtSignal(str)

    def __init__(self, parent):
        super().__init__(parent)
        super(logging.Handler).__init__()

        self.widget = QtWidgets.QTextEdit()
        self.widget.setReadOnly(True)
        self.appendPlainText.connect(self.log)

    def emit(self, record):
        msg = self.format(record)
        self.appendPlainText.emit(msg)

    def log(self, text):
        colors = {
            "DEBUG": self.widget.palette().highlight().color(),
            "INFO": self.widget.palette().highlight().color(),
            "WARNING": QColor(255, 255, 0),
            "ERROR": QColor(255, 0, 0)
        }

        parts = text.split(" - ")
        level, msg = parts[0], parts[1]
        default_color = self.widget.textColor()
        self.widget.moveCursor(QTextCursor.End)
        if level in colors:
            self.widget.setTextColor(colors[level])
        self.widget.insertPlainText(msg + "\n")
        self.widget.setTextColor(default_color)
