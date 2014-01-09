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
from PyQt4.QtGui import QFileDialog, QMessageBox, QInputDialog, QListWidgetItem, QIcon
from which import which
from tab2chordpro.Transpose import testTabFormat, tab2ChordPro, enNotation


class MainForm(QtGui.QMainWindow):
    def __init__(self, parent=None):
        QtGui.QMainWindow.__init__(self, parent)
        self.ui = uic.loadUi('gui/qtchordii/mainwindow.ui', self)
        self.show()

        self.app_name = "QtChordii"

        args = parse_arguments()

        #        self.highlighter = Highlighter()

        self.working_dir = args.workingdir

        if self.working_dir is None:
            self.selectDir()
        else:
            self.openDir()

        self.setup_file_widget()
        self.setup_editor()
        current_sizes = self.ui.splitter.sizes()
        self.ui.splitter.setSizes(
            [400, current_sizes[1] + current_sizes[0], current_sizes[2] + current_sizes[1] + current_sizes[0]])
        self.setup_file_menu()
        self.setGeometry(0, 0, 1600, 800)
        self.dirty = False

    def setup_file_menu(self):
        file_menu = QtGui.QMenu(self.tr("&File"), self)
        self.menuBar.addMenu(file_menu)

        # new_file_act = QtGui.QAction(self.tr("&New..."), self)
        new_file_act = self.ui.actionNew
        new_file_act.setShortcut(QtGui.QKeySequence.New)
        new_file_act.setIcon(QIcon.fromTheme('document-new'))
        new_file_act.triggered.connect(self.newFile)
        file_menu.addAction(new_file_act)

        # open_file_act = QtGui.QAction(self.tr("&Open Directory..."), self)
        open_file_act = self.ui.actionOpen
        open_file_act.setShortcut(QtGui.QKeySequence.Open)
        open_file_act.setIcon(QIcon.fromTheme('folder-open'))
        open_file_act.triggered.connect(self.selectDir)
        file_menu.addAction(open_file_act)

        # save_file_act = QtGui.QAction(self.tr("&Save"), self)
        save_file_act = self.ui.actionSave
        save_file_act.setShortcut(QtGui.QKeySequence.Save)
        save_file_act.setIcon(QIcon.fromTheme('document-save'))
        save_file_act.triggered.connect(self.saveFile)
        file_menu.addAction(save_file_act)

        save_file_as_act = QtGui.QAction(self.tr("Save as..."), self)
        save_file_as_act.setShortcut(QtGui.QKeySequence.SaveAs)
        save_file_as_act.triggered.connect(self.saveFileAs)
        file_menu.addAction(save_file_as_act)

        file_menu.addSeparator()

        save_project_file_act = QtGui.QAction(self.tr("Save &project"), self)
        #        save_project_file_act.setShortcut(QtGui.QKeySequence.Save)
        save_project_file_act.triggered.connect(self.saveProject)
        file_menu.addAction(save_project_file_act)

        # export_file_act = QtGui.QAction(self.tr("&Export songbook to PostScript..."), self)
        export_file_act = self.ui.actionRun
        export_file_act.triggered.connect(self.runChordii)
        export_file_act.setIcon(QIcon.fromTheme('system-run'))
        file_menu.addAction(export_file_act)

        file_menu.addSeparator()

        file_menu.addAction(self.tr("E&xit"), QtGui.qApp, QtCore.SLOT("quit()"),
                            QtGui.QKeySequence.Quit)

    def setup_file_widget(self):
        self.ui.fileWidget.itemSelectionChanged.connect(self.selection_changed)

    def setup_editor(self):
        self.ui.textEdit.setMain(self)
        self.ui.textEdit.textChanged.connect(self.set_dirty)

    def selection_changed(self):
        if len(self.ui.fileWidget.selectedItems()) == 1:
            if self.ok_to_continue():
                self.openFile(self.ui.fileWidget.selectedItems()[0].data(Qt.UserRole))

    def set_dirty(self):
        """
        On change of text in textEdit window, set the flag "dirty" to True
        """
        if hasattr(self, "fileName"):
            if self.dirty:
                return True
            self.dirty = True
            self.update_status('self.dirty set to True')

    def clear_dirty(self):
        """Clear the dirty."""
        self.dirty = False

    def update_status(self, message):
        """
        Keep status current.
        """
        if hasattr(self, "fileName") and self.fileName is not None:
            file_base = os.path.basename(self.fileName)
            self.setWindowTitle(str(self.app_name + " - " + file_base + "[*]"))
            self.ui.statusBar.showMessage(message, 5000)
            self.setWindowModified(self.dirty)

    def ok_to_continue(self):
        """
        Boolean result invocation method.
        """
        if self.dirty:
            reply = QMessageBox.question(self,
                                         self.app_name + " - Unsaved Changes",
                                         "Save unsaved changes?",
                                         QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel)
            if reply == QMessageBox.Cancel:
                return False
            elif reply == QMessageBox.Yes:
                return self.saveFile()
        return True

    def newFile(self):
        if not self.ok_to_continue():
            return
        self.fileName = QInputDialog.getText(self, self.tr("New File..."),
                                             self.tr("Enter name for new file (without extension):"))
        if not self.fileName[1]:
            return
        self.fileName = os.path.join(self.working_dir, str(self.fileName[0]) + ".cho")
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
        self.clear_dirty()

        self.temp_dir = os.path.join(self.working_dir, "temp")
        if not os.path.exists(self.temp_dir):
            os.makedirs(self.temp_dir)
        out_file = os.path.join(self.temp_dir, '{}.ps'.format(os.path.splitext(os.path.basename(self.fileName))[0]))

        self.runChordii(self.fileName, out_file, True)

        self.ui.scrollArea.load(self.ps2pdf(out_file))
        self.update_status('File opened.')
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
                self.clear_dirty()
                self.update_status('Saved file')
                return True
            else:
                self.ui.statusBar.showMessage('Failed to save ...', 5000)
                return False

    def saveFileAs(self):
        """
        Save file with a different name and maybe different directory.
        """
        path = self.fileName if self.fileName is not None else self.working_dir
        fname = QFileDialog.getSaveFileName(self,
                                            self.tr("Save as..."), path, self.tr("Chordii files (*.cho *.crd)"))[0]
        if fname:
            print(fname)
            if "." not in fname:
                fname += ".cho"
            self.fileName = fname
            self.saveFile()
            self.statusBar().showMessage('SaveAs file' + fname, 8000)
            self.clear_dirty()

    def selectDir(self):
        self.working_dir = QFileDialog.getExistingDirectory(self, self.tr("Choose working directory"),
                                                            QDir.homePath() if self.working_dir is None else "")
        self.openDir()

    def openDir(self):
        print(self.working_dir)
        for fileType in ('cho', 'crd'):
            for file in glob.iglob('{}/*.{}'.format(self.working_dir, fileType)):
                item = QListWidgetItem(os.path.basename(file))
                item.setData(Qt.UserRole, file)
                item.setSizeHint(QSize(0, 30))
                self.ui.fileWidget.addItem(item)

    def saveProject(self):
        """
        Save all the song files as one continuous file for passing to Chordii.
        """
        saveString = ""
        parent = self.model.index(self.working_dir)
        for i in range(self.model.rowCount(parent)):
            if i > 0:
                saveString += str("\n{ns}\n\n")
            row = self.model.index(i, 0, parent)
            path = self.model.fileInfo(row).absoluteFilePath()
            file = open(path, "r")
            saveString += file.read()
            file.close()
        outDir = os.path.join(self.working_dir, "output")
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
            ret = QMessageBox.critical(self, self.tr(self.app_name + " - Chordii problem"),
                                       self.tr("Couldn't find a chordii executable in the PATH. \
                                       Please specify chordii's location to continue."),
                                       QMessageBox.Open | QMessageBox.Cancel, QMessageBox.Open)
            if ret == QMessageBox.Open:
                chordiiCommand = QFileDialog.getOpenFileName(self, self.tr("Specify the chordii executable"),
                                                             QDir.homePath())[0]
        command = [chordiiCommand, "-i", "-L", "-p", "1"] if not preview else [chordiiCommand]
        if not outputFile:
            outDir = os.path.join(self.working_dir, "output")
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
                    QMessageBox.information(self, self.tr(self.app_name + " - Chordii was successful"),
                                            self.tr("Chordii compiled the songbook without warnings!"))
                elif response is not None:
                    msgBox = WarningMessageBox()
                    msgBox.setWindowTitle(self.tr(self.app_name + " - Chordii warning"))
                    msgBox.setText(self.tr("Chordii exited with warnings."))
                    msgBox.setDetailedText(self.tr(bytearray(response).decode()))
                    msgBox.setIcon(QMessageBox.Warning)
                    msgBox.exec_()
        except subprocess.CalledProcessError as e:
            if not preview:
                QMessageBox.critical(self, self.tr(self.app_name + " - Chordii problem"),
                                     self.tr("Chordii crashed while compiling. Please check your syntax.\
                                             Tip: This is probably due to an incorrect chord definition."))

    def tab2chordpro(self):
        notation = testTabFormat(self.ui.textEdit.toPlainText(), [enNotation])
        if notation is not None:
            res = QMessageBox.question(self, self.tr(self.app_name),
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


def parse_arguments():
    parser = argparse.ArgumentParser(
        description='A Qt GUI for Chordii.')
    parser.add_argument('-d', '--workingdir',
                        help='the directory containing Chordii files')
    args = parser.parse_args()
    return args


if __name__ == "__main__":
    app = QtGui.QApplication(sys.argv)
    myapp = MainForm()
    sys.exit(app.exec_())
