# Copyright (C) 2013, 2014 Johan Reitan
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
        self.is_blanked = True
        self.current_page = 0
        self.pdf_images = []
        self.scroll_layout = None

    def load(self, filename):
        self.doc = popplerqt4.Poppler.Document.load(filename)
        self.doc.setRenderHint(
            popplerqt4.Poppler.Document.Antialiasing and popplerqt4.Poppler.Document.TextAntialiasing)
        self.current_page = 0
        self.pdf_images = [None for i in range(self.doc.numPages())]
        self.cache_image(self.current_page)
        self.un_blank()
        self.paintEvent(None)

    def cache_image(self, idx):
        if idx >= self.doc.numPages():
            return
        if self.pdf_images[idx] is not None:
            return
        page = self.doc.page(idx)
        scroll_width = self.verticalScrollBar().sizeHint().width()
        ratio = 1.0 * (self.frameSize().width() - 1.7 * scroll_width) / page.pageSize().width()
        self.pdf_images[idx] = page.renderToImage(72 * ratio, 72 * ratio)

    def get_image(self, idx):
        self.cache_image(idx)
        return self.pdf_images[idx]

    def blank(self):
        self.is_blanked = True
        self.update()

    def un_blank(self):
        self.is_blanked = False
        self.update()

    def paintEvent(self, event):
        if self.is_blanked:
            return
        img = self.get_image(0)
        if img is None:
            return

        scroll_contents = QtGui.QWidget()
        self.setWidget(scroll_contents)
        self.scroll_layout = QtGui.QVBoxLayout()
        scroll_contents.setLayout(self.scroll_layout)

        for i in range(self.doc.numPages()):
            img = self.get_image(i)
            label = QtGui.QLabel()
            label.setPixmap(QtGui.QPixmap(img))

            self.scroll_layout.addWidget(label)