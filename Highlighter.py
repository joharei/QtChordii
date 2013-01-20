import re
from PySide import QtCore, QtGui

class Highlighter(QtCore.QObject):
    def __init__(self, parent=None):
        QtCore.QObject.__init__(self, parent)

        self.mappings = {}

    def addToDocument(self, doc):
        self.connect(doc, QtCore.SIGNAL("contentsChange(int, int, int)"), self.highlight)

    def addMapping(self, pattern, format):
        self.mappings[pattern] = format

    def highlight(self, position, removed, added):
        doc = self.sender()

        block = doc.findBlock(position)
        if not block.isValid():
            return

        if added > removed:
            endBlock = doc.findBlock(position + added)
        else:
            endBlock = block

        while block.isValid() and not (endBlock < block):
            self.highlightBlock(block)
            block = block.next()

    def highlightBlock(self, block):
        layout = block.layout()
        text = block.text()

        overrides = []

        for pattern in self.mappings:
            for m in re.finditer(pattern,text):
                range = QtGui.QTextLayout.FormatRange()
                s,e = m.span()
                range.start = s
                range.length = e-s
                range.format = self.mappings[pattern]
                overrides.append(range)

        print(overrides)
        layout.setAdditionalFormats(overrides)
        block.document().markContentsDirty(block.position(), block.length())