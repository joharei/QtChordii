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
import codecs
import glob
from PyQt4 import QtCore, QtGui, uic
from PyQt4.QtCore import QDir, Qt, QSize
from gui.warningmessagebox import WarningMessageBox
from PyQt4.QtGui import QFileSystemModel, QFileDialog, QMessageBox, QInputDialog, QListWidgetItem, QIcon
from which import which
from tab2chordpro.Transpose import testTabFormat, tab2ChordPro, enNotation


class MainForm(QtGui.QMainWindow):
    def __init__(self, parent=None):
        QtGui.QMainWindow.__init__(self, parent)
        self.ui = uic.loadUi('gui/qtchordii/mainwindow.ui', self)
        self.show()

        self.appName = "QtChordii"

        args = self.parseArguments()

#        self.highlighter = Highlighter()

        self.workingDir = args.workingdir

        if self.workingDir is None:
            self.selectDir()
        else:
            self.openDir()

        self.setupFileWidget()
        self.setupEditor()
        currentSizes = self.ui.splitter.sizes()
        self.ui.splitter.setSizes([400, currentSizes[1] + currentSizes[0], currentSizes[2] + currentSizes[1] + currentSizes[0]])
        self.setupFileMenu()
        self.setupToolBar()
        self.setGeometry(0,0,1600, 800)

    def parseArguments(self):
        parser = argparse.ArgumentParser(
            description='A Qt GUI for Chordii.')
        parser.add_argument('-d', '--workingdir',
                            help='the directory containing Chordii files')
        args = parser.parse_args()
        return args

    def setupToolBar(self):
        self.ui.actionNew.setIcon(QIcon.fromTheme('document-new'))
        self.ui.actionNew.triggered.connect(self.newFile)
        self.ui.actionOpen.setIcon(QIcon.fromTheme('folder-open'))
        self.ui.actionOpen.triggered.connect(self.selectDir)
        self.ui.actionSave.setIcon(QIcon.fromTheme('document-save'))
        self.ui.actionSave.triggered.connect(self.saveFile)
        self.ui.actionRun.setIcon(QIcon.fromTheme('system-run'))
        self.ui.actionRun.triggered.connect(self.runChordii)

    def setupFileWidget(self):
        self.ui.fileWidget.itemSelectionChanged.connect(self.selectionChanged)

    def setupEditor(self):
        self.ui.textEdit.setMain(self)
        self.ui.textEdit.textChanged.connect(self.setDirty)
        self.dirty = False

    def selectionChanged(self):
#        test = QItemSelectionRange()
#        test.top()
        if len(self.ui.fileWidget.selectedItems()) == 1:
            if self.okToContinue():
                self.openFile(self.ui.fileWidget.selectedItems()[0].data(Qt.UserRole))
            # else:
            #     self.ui.fileWidget.setSelection(oldSelection)

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
            self.setWindowTitle(str(self.appName + " - " + flbase + "[*]"))
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
                                         QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel)
            if reply == QMessageBox.Cancel:
                return False
            elif reply == QMessageBox.Yes:
                return self.saveFile()
        return True

    def newFile(self):
        if not self.okToContinue():
            return
        self.fileName = QInputDialog.getText(self, self.tr("New File..."),
                                             self.tr("Enter name for new file (without extension):"))
        if not self.fileName[1]:
            return
        self.fileName = os.path.join(self.workingDir, str(self.fileName[0]) + ".cho")
        self.saveFile()
        if self.ui.textEdit.isReadOnly():
            self.ui.textEdit.setReadOnly(False)
        self.ui.textEdit.setText("{t:}\n{st:}")
        self.ui.textEdit.setFocus()
        self.statusBar().showMessage('New file', 5000)

    def openFile(self, path=""):
        if self.ui.textEdit.isReadOnly():
            self.ui.textEdit.setReadOnly(False)

        self.fileName = path

        if self.fileName != "":
            inStream = codecs.open(self.fileName, "r", "ISO-8859-1")
            if inStream:
                self.ui.textEdit.setPlainText(inStream.read())
        self.clearDirty()

        self.temp_dir = os.path.join(self.workingDir, "temp")
        if not os.path.exists(self.temp_dir):
            os.makedirs(self.temp_dir)
        out_file = os.path.join(self.temp_dir, '{}.ps'.format(os.path.splitext(os.path.basename(self.fileName))[0]))

        self.runChordii(self.fileName, out_file, True)

        self.ui.scrollArea.load(self.ps2pdf(out_file))
        self.updateStatus('File opened.')
        self.tab2chordpro()

    def saveFile(self):
        """
        Save file with current name.
        """
        if self.fileName is None:
            return self.saveFileAs()
        else:
            if not self.dirty:
                return
            fname = self.fileName
            fl = codecs.open(fname, 'w', "ISO-8859-1")
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

    def saveFileAs(self):
        """
        Save file with a different name and maybe different directory.
        """
        path = self.fileName if self.fileName is not None else self.workingDir
        fname = QFileDialog.getSaveFileName(self,
                                            self.tr("Save as..."), path, self.tr("Chordii files (*.cho *.crd)"))[0]
        if fname:
            print(fname)
            if "." not in fname:
                fname += ".cho"
            self.fileName = fname
            self.saveFile()
            self.statusBar().showMessage('SaveAs file' + fname, 8000)
            self.clearDirty()

    def selectDir(self):
        self.workingDir = QFileDialog.getExistingDirectory(self, self.tr("Choose working directory"),
                                                           QDir.homePath() if self.workingDir is None else "")
        self.openDir()

    def openDir(self):
        print(self.workingDir)
        for fileType in ('cho', 'crd'):
            for file in glob.iglob('{}/*.{}'.format(self.workingDir, fileType)):
                item = QListWidgetItem(os.path.basename(file))
                item.setData(Qt.UserRole, file)
                item.setSizeHint(QSize(0, 30))
                self.ui.fileWidget.addItem(item)

    def setupFileMenu(self):
        fileMenu = QtGui.QMenu(self.tr("&File"), self)
        self.menuBar.addMenu(fileMenu)

        newFileAct = QtGui.QAction(self.tr("&New..."), self)
        newFileAct.setShortcut(QtGui.QKeySequence.New)
        newFileAct.triggered.connect(self.newFile)
        fileMenu.addAction(newFileAct)

        openFileAct = QtGui.QAction(self.tr("&Open Directory..."), self)
        openFileAct.setShortcut(QtGui.QKeySequence.Open)
        openFileAct.triggered.connect(self.selectDir)
        fileMenu.addAction(openFileAct)

        saveFileAct = QtGui.QAction(self.tr("&Save"), self)
        saveFileAct.setShortcut(QtGui.QKeySequence.Save)
        saveFileAct.triggered.connect(self.saveFile)
        fileMenu.addAction(saveFileAct)

        saveFileAsAct = QtGui.QAction(self.tr("Save as..."), self)
        saveFileAsAct.setShortcut(QtGui.QKeySequence.SaveAs)
        saveFileAsAct.triggered.connect(self.saveFileAs)
        fileMenu.addAction(saveFileAsAct)

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
            row = self.model.index(i, 0, parent)
            path = self.model.fileInfo(row).absoluteFilePath()
            file = open(path, "r")
            saveString += file.read()
            file.close()
        outDir = os.path.join(self.workingDir, "output")
        if not os.path.exists(outDir):
            os.makedirs(outDir)
        saveFile = open(os.path.join(outDir, "songbook.cho"), "w")
        saveFile.write(saveString)

    def runChordii(self, inputFile=None, outputFile=None, preview=False):
        """
        Run Chordii to produce output.
        """

        chordiiCommand = which("chordii")
        if chordiiCommand is None:
            chordiiCommand = which("chordii430")
        if chordiiCommand is None:
            ret = QMessageBox.critical(self, self.tr(self.appName + " - Chordii problem"),
                                       self.tr("Couldn't find a chordii executable in the PATH. \
                                       Please specify chordii's location to continue."),
                                       QMessageBox.Open | QMessageBox.Cancel, QMessageBox.Open)
            if ret == QMessageBox.Open:
                chordiiCommand = QFileDialog.getOpenFileName(self, self.tr("Specify the chordii executable"),
                                                             QDir.homePath())[0]
        command = [chordiiCommand, "-i", "-L", "-p", "1"] if not preview else [chordiiCommand]
        if not outputFile:
            outDir = os.path.join(self.workingDir, "output")
            outputFile = os.path.join(outDir, "songbook.ps")
            if not os.path.exists(outDir):
                os.makedirs(outDir)
        if not inputFile:
            for i in range(self.ui.fileWidget.count()):
                command.append(self.ui.fileWidget.item(i).data(Qt.UserRole))
        else:
            command.append(inputFile)
        command.append("-o")
        command.append(outputFile)
        print(command)
        try:
            response = subprocess.check_output(command, stderr=subprocess.STDOUT)
            if not preview:
                if response is not None and response == b'':
                    QMessageBox.information(self, self.tr(self.appName + " - Chordii was successful"),
                                            self.tr("Chordii compiled the songbook without warnings!"))
                elif response is not None:
                    msgBox = WarningMessageBox()
                    msgBox.setWindowTitle(self.tr(self.appName + " - Chordii warning"))
                    msgBox.setText(self.tr("Chordii exited with warnings."))
                    msgBox.setDetailedText(self.tr(bytearray(response).decode()))
                    msgBox.setIcon(QMessageBox.Warning)
                    msgBox.exec_()
        except subprocess.CalledProcessError as e:
            if not preview:
                QMessageBox.critical(self, self.tr(self.appName + " - Chordii problem"),
                                     self.tr("Chordii crashed while compiling. Please check your syntax.\
                                             Tip: This is probably due to an incorrect chord definition."))

    def tab2chordpro(self):
        notation = testTabFormat(self.ui.textEdit.toPlainText(), [enNotation])
        if notation is not None:
            res = QMessageBox.question(self, self.tr(self.appName),
                                       self.tr("It seems this file is in the tab format.\n" +
                                               "Do you want to convert it to the ChordPro format?"),
                                       QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
            if res == QMessageBox.No:
                return
            self.ui.textEdit.setText(tab2ChordPro(self.ui.textEdit.toPlainText()))

    def ps2pdf(self, file):
        out_file = '{}.pdf'.format(os.path.splitext(file)[0])
        print(subprocess.check_output(['ps2pdf', file, out_file], stderr=subprocess.STDOUT))
        return out_file


if __name__ == "__main__":
    app = QtGui.QApplication(sys.argv)
    myapp = MainForm()
    sys.exit(app.exec_())
