#coding: utf-8

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

import argparse
import os
import subprocess
import sys
from PySide import QtCore, QtGui
from PySide.QtCore import QDir, QModelIndex
from gui.warningmessagebox import WarningMessageBox
from syntax import ChordProHighlighter
from gui.mainwindow import Ui_MainWindow
from PySide.QtGui import QFileSystemModel, QFileDialog, QMessageBox, QItemSelectionRange
from which import which

class MainForm(QtGui.QMainWindow):
    def __init__(self, parent=None):
        QtGui.QMainWindow.__init__(self, parent)
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.show()

        self.appName = "QtChordii"

        args = self.parseArguments()

#        self.highlighter = Highlighter()

        self.workingDir = args.workingdir

        if self.workingDir is None:
            self.workingDir = self.openDir()

        self.setupFileTree()
        self.setupEditor()
        currentSizes = self.ui.splitter.sizes()
        self.ui.splitter.setSizes([300, currentSizes[1]+currentSizes[0]-300])
        self.setupFileMenu()

    def parseArguments(self):
        parser = argparse.ArgumentParser(
            description='A Qt GUI for Chordii.')
        parser.add_argument('-d', '--workingdir',
            help='the directory containing Chordii files')
        args = parser.parse_args()
        return args


    def setupFileTree(self):
        self.model = QFileSystemModel()
        self.model.setRootPath(self.workingDir)
        self.model.setNameFilters(self.tr("Chordii files (*.cho *.crd)"))
        self.model.setFilter(QDir.Files)
        self.ui.fileView.setModel(self.model)
        self.ui.fileView.setRootIndex(self.model.index(self.workingDir))
        self.ui.fileView.setColumnHidden(2, True)
        self.ui.fileView.setColumnWidth(0,150)
        self.ui.fileView.resizeColumnToContents(1)
        self.connect(self.ui.fileView.selectionModel(),QtCore.SIGNAL("selectionChanged(QItemSelection, QItemSelection)"),self.selectionChanged)

    def setupEditor(self):
        variableFormat = QtGui.QTextCharFormat()
        variableFormat.setFontWeight(QtGui.QFont.Bold)
        variableFormat.setForeground(QtCore.Qt.blue)
#        self.highlighter.addMapping("\\b[A-Z_]+\\b", variableFormat)

        singleLineCommentFormat = QtGui.QTextCharFormat()
        singleLineCommentFormat.setBackground(QtGui.QColor("#77ff77"))
#        self.highlighter.addMapping("#[^\n]*", singleLineCommentFormat)

        quotationFormat = QtGui.QTextCharFormat()
        quotationFormat.setBackground(QtCore.Qt.cyan)
        quotationFormat.setForeground(QtCore.Qt.blue)
#        self.highlighter.addMapping("\".*\"", quotationFormat)

        functionFormat = QtGui.QTextCharFormat()
        functionFormat.setFontItalic(True)
        functionFormat.setForeground(QtCore.Qt.blue)
#        self.highlighter.addMapping("\\b[a-z0-9_]+\\(.*\\)", functionFormat)



        font = QtGui.QFont()
        font.setFamily("Courier")
        font.setFixedPitch(True)
        font.setPointSize(10)

        self.ui.textEdit.setFont(font)
        self.highlighter = ChordProHighlighter(self.ui.textEdit.document())

        self.ui.textEdit.textChanged.connect(self.setDirty)
        self.dirty = False

    def selectionChanged(self, newSelection, oldSelection):
#        test = QItemSelectionRange()
#        test.top()
        if self.okToContinue():
            self.openFile(self.model.filePath(newSelection.indexes()[0]))
        else:
            self.model.index = oldSelection

    def setDirty(self):
        """
        On change of text in textEdit window, set the flag "dirty" to True
        """
        if hasattr(self, "fileName"):
            if self.dirty:
                return True
            self.dirty = True
            self.updateStatus('self.dirty set to True')

    def clearDirty(self):
        """Clear the dirty."""
        self.dirty = False

    def updateStatus(self, message):
        """
        Keep status current.
        """
        if hasattr(self, "fileName") and self.fileName is not None:
            flbase = os.path.basename(self.fileName)
            self.setWindowTitle(str(self.appName + " - " + flbase + "[*]") )
            self.ui.statusBar.showMessage(message, 5000)
            self.setWindowModified(self.dirty)

    def okToContinue(self):
        """
        Boolean result invocation method.
        """
        if self.dirty:
            reply = QMessageBox.question(self,
                self.appName + " - Unsaved Changes",
                "Save unsaved changes?",
                QMessageBox.Yes|QMessageBox.No|QMessageBox.Cancel)
            if reply == QMessageBox.Cancel:
                return False
            elif reply == QMessageBox.Yes:
                return self.saveFile()
        return True

    def openFile(self, path=""):
        self.fileName = path

        if self.fileName!="":
            inFile = QtCore.QFile(self.fileName)
            if inFile.open(QtCore.QFile.ReadWrite | QtCore.QFile.Text):
                inStream = QtCore.QTextStream(inFile)
                self.ui.textEdit.setPlainText(inStream.readAll())
        self.clearDirty()
        self.updateStatus('File opened.')

    def saveFile(self):
        """Save file with current name."""
        if self.fileName is None:
            return self.fileSaveAs()
        else:
            if not self.dirty:
                return
            fname = self.fileName
            fl = open(fname, 'w')
            tempText = self.ui.textEdit.toPlainText()
            if tempText:
                fl.write(tempText)
                fl.close()
                self.clearDirty()
                self.updateStatus('Saved file')
                return True
            else:
                self.ui.statusBar.showMessage('Failed to save ...', 5000)
                return False

    def openDir(self):
        print(self.workingDir)
        return QFileDialog.getExistingDirectory(self,self.tr("Choose working directory"),QDir.homePath() if self.workingDir is None else "")

    def setupFileMenu(self):
        fileMenu = QtGui.QMenu(self.tr("&File"), self)
        self.menuBar().addMenu(fileMenu)

#        newFileAct = QtGui.QAction(self.tr("&New..."), self)
#        newFileAct.setShortcut(QtGui.QKeySequence(self.tr("Ctrl+N", "File|New")))
#        self.connect(newFileAct, QtCore.SIGNAL("triggered()"), self.newFile)
#        fileMenu.addAction(newFileAct)

        openFileAct = QtGui.QAction(self.tr("&Open Directory..."), self)
        openFileAct.setShortcut(QtGui.QKeySequence.Open)
        openFileAct.triggered.connect(self.openDir)
        fileMenu.addAction(openFileAct)

        saveFileAct = QtGui.QAction(self.tr("&Save"), self)
        saveFileAct.setShortcut(QtGui.QKeySequence.Save)
        saveFileAct.triggered.connect(self.saveFile)
        fileMenu.addAction(saveFileAct)

        fileMenu.addSeparator()

        saveProjectFileAct = QtGui.QAction(self.tr("Save &project"), self)
#        saveProjectFileAct.setShortcut(QtGui.QKeySequence.Save)
        saveProjectFileAct.triggered.connect(self.saveProject)
        fileMenu.addAction(saveProjectFileAct)

        exportFileAct = QtGui.QAction(self.tr("&Export songbook to PostScript..."), self)
        exportFileAct.triggered.connect(self.runChordii)
        fileMenu.addAction(exportFileAct)

        fileMenu.addSeparator()

        fileMenu.addAction(self.tr("E&xit"), QtGui.qApp, QtCore.SLOT("quit()"),
            QtGui.QKeySequence.Quit)

    def saveProject(self):
        """
        Save all the song files as one continuous file for passing to Chordii.
        """
        saveString = ""
        parent = self.model.index(self.workingDir)
        for i in range(self.model.rowCount(parent)):
            if i > 0:
                saveString += str("\n{ns}\n\n")
            row = self.model.index(i,0,parent)
            path = self.model.fileInfo(row).absoluteFilePath()
            file = open(path, "r")
            saveString += file.read()
            file.close()
        outDir = self.workingDir + "output/"
        if not os.path.exists(outDir):
            os.makedirs(outDir)
        saveFile = open(outDir + "songbook.cho", "w")
        saveFile.write(saveString)

    def runChordii(self, inputFile = None, outputFile = None):
        """
        Run Chordii to produce output.
        """

        chordiiCommand = which("chordii")
        if chordiiCommand is None:
            chordiiCommand = which("chordii430")
        if chordiiCommand is None:
            ret = QMessageBox.critical(self, self.tr(self.appName + " - Chordii problem"),
                self.tr("Couldn't find a chordii executable in the PATH. \
                Please specify chordii's location to continue."), QMessageBox.Open | QMessageBox.Cancel,
                QMessageBox.Open)
            if ret == QMessageBox.Open:
                chordiiCommand = QFileDialog.getOpenFileName(self, self.tr("Specify the chordii executable"),
                    QDir.homePath())

        command = [chordiiCommand, "-i", "-L"]
        if not any((inputFile, outputFile)):
            outputFile = self.workingDir + "output/songbook.ps"
            outDir = self.workingDir + "output/"
            if not os.path.exists(outDir):
                os.makedirs(outDir)
            parent = self.model.index(self.workingDir)
            for i in range(self.model.rowCount(parent)):
                row = self.model.index(i,0,parent)
                path = self.model.fileInfo(row).absoluteFilePath()
                command.append(path)
        command.append("-o")
        command.append(outputFile)
        try:
            response = subprocess.check_output(command,
                stderr=subprocess.STDOUT)
            if response is not None:
                msgBox = WarningMessageBox()
                msgBox.setWindowTitle(self.tr(self.appName + " - Chordii warning"))
                msgBox.setText(self.tr("Chordii exited with warnings."))
                msgBox.setDetailedText(self.tr(bytearray(response).decode()))
                msgBox.setIcon(QMessageBox.Warning)
                msgBox.exec_()
        except subprocess.CalledProcessError as e:
            QMessageBox.critical(self, self.tr(self.appName + " - Chordii problem"), self.tr(e.output))

if __name__ == "__main__":
    app = QtGui.QApplication(sys.argv)
    myapp = MainForm()
#    myapp.show()
    sys.exit(app.exec_())