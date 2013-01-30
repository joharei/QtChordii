from PySide.QtGui import *

class WarningMessageBox(QMessageBox):

    def __init__(self, *args, **kwargs):
        super(WarningMessageBox, self).__init__(*args, **kwargs)
        self.detail_box_size = None

    def resizeEvent(self, event):

        result = super(WarningMessageBox, self).resizeEvent(event)

        details_box = self.findChild(QTextEdit)
        if self.detail_box_size is None:
            self.detail_box_size = details_box.viewport().size()
        if details_box is not None:
            details_box.setFixedSize(self.detail_box_size)

        return result