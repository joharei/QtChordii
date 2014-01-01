# Copyright 2013 Johan Reitan
#
# This file is part of QtChordii.
#
# QtChordii is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# QtChordii is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with QtChordii.  If not, see <http://www.gnu.org/licenses/>.

from PyQt4 import QtGui
from PyQt4.QtGui import QScrollArea
import popplerqt4


class PDFViewer(QScrollArea):
    def __init__(self, parent):
        super().__init__(parent)
        self.setWidgetResizable(True)
        self.doc = None
        self.isBlanked = True

    def load(self, filename):
        self.doc = popplerqt4.Poppler.Document.load(filename)
        self.doc.setRenderHint(
            popplerqt4.Poppler.Document.Antialiasing and popplerqt4.Poppler.Document.TextAntialiasing)
        self.currentPage = 0
        self.pdfImages = [None for i in range(self.doc.numPages())]
        self.cacheImage(self.currentPage)
        self.unBlank()
        self.paintEvent(None)

    def cacheImage(self, idx):
        if idx >= self.doc.numPages():
            return
        if self.pdfImages[idx] is not None:
            return
        page = self.doc.page(idx)
        scroll_width = self.verticalScrollBar().sizeHint().width()
        ratio = 1.0 * (self.frameSize().width() - 1.7 * scroll_width) / page.pageSize().width()
        self.pdfImages[idx] = page.renderToImage(72 * ratio, 72 * ratio)

    def getImage(self, idx):
        self.cacheImage(idx)
        return self.pdfImages[idx]

    def blank(self):
        self.isBlanked = True
        self.update()

    def unBlank(self):
        self.isBlanked = False
        self.update()

    def paintEvent(self, event):
        if self.isBlanked:
            return
        img = self.getImage(0)
        if img is None:
            return

        scrollContents = QtGui.QWidget()
        self.setWidget(scrollContents)
        self.scroll_layout = QtGui.QVBoxLayout()
        scrollContents.setLayout(self.scroll_layout)

        for i in range(self.doc.numPages()):
            img = self.getImage(i)
            label = QtGui.QLabel()
            label.setPixmap(QtGui.QPixmap(img))

            self.scroll_layout.addWidget(label)