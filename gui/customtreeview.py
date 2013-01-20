from PySide import QtCore
from PySide.QtGui import QTreeView

class CustomTreeView(QTreeView):
    def __init__(self, parent):
        super(CustomTreeView, self).__init__(parent)

    def supportedDropAction(self, event):
        return QtCore.Qt.MoveAction