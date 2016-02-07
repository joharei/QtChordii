# coding: utf-8

# Copyright (C) 2013-2016 Johan Reitan
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
import codecs
import glob
import os
import shutil
import subprocess
import sys
import tempfile

from PyQt5 import uic
from PyQt5.QtCore import Qt, QDir, QSize
from PyQt5.QtGui import QKeySequence, QIcon
from PyQt5.QtWidgets import (QApplication, QMenu, QAction, qApp, QMessageBox, QFileDialog, QListWidgetItem,
                             QMainWindow, QDesktopWidget)

from gui.warningmessagebox import WarningMessageBox
from gui.welcomedialog import WelcomeDialog
from model.songbook import Songbook
from tab2chordpro.Transpose import testTabFormat, tab2ChordPro, enNotation
from utils.ps2pdf import ps2pdf
from utils.which import which


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = uic.loadUi('gui/qtchordii/mainwindow.ui', self)

        self.app_name = "QtChordii"

        args = parse_arguments()

        self.file_name = None
        self.songbook = Songbook()
        if args.project:
            self.project_file = os.path.abspath(args.project)
        else:
            self.project_file, new_file = WelcomeDialog.get_project(self)
            if not self.project_file:
                sys.exit(0)
            if new_file:
                self.save_project()

        self.load_project(self.project_file)

        self.working_dir = os.path.dirname(self.project_file)
        self.temp_dir = tempfile.mkdtemp()

        self.setup_file_widget()
        self.setup_editor()
        self.setup_file_menu()
        self.setup_geometry()
        self.dirty = False

    def setup_file_menu(self):
        file_menu = QMenu(self.tr("&File"), self)
        self.menuBar.addMenu(file_menu)

        # new_file_act = QAction(self.tr("&New..."), self)
        new_file_act = self.ui.actionNew
        new_file_act.setShortcut(QKeySequence.New)
        new_file_act.setIcon(QIcon.fromTheme('document-new'))
        new_file_act.triggered.connect(self.new_file)
        file_menu.addAction(new_file_act)

        # open_file_act = QAction(self.tr("&Open Directory..."), self)
        open_file_act = self.ui.actionOpen
        open_file_act.setShortcut(QKeySequence.Open)
        open_file_act.setIcon(QIcon.fromTheme('folder-open'))
        open_file_act.triggered.connect(self.select_dir)
        file_menu.addAction(open_file_act)

        # save_file_act = QAction(self.tr("&Save"), self)
        save_file_act = self.ui.actionSave
        save_file_act.setShortcut(QKeySequence.Save)
        save_file_act.setIcon(QIcon.fromTheme('document-save'))
        save_file_act.triggered.connect(self.save_file)
        file_menu.addAction(save_file_act)

        save_file_as_act = QAction(self.tr("Save as..."), self)
        save_file_as_act.setShortcut(QKeySequence.SaveAs)
        save_file_as_act.triggered.connect(self.save_file_as)
        file_menu.addAction(save_file_as_act)

        file_menu.addSeparator()

        load_project_file_act = QAction(self.tr("&Load project"), self)
        load_project_file_act.triggered.connect(self.select_project)
        file_menu.addAction(load_project_file_act)

        save_project_file_act = QAction(self.tr("Save &project"), self)
        #        save_project_file_act.setShortcut(QKeySequence.Save)
        save_project_file_act.triggered.connect(self.save_project)
        file_menu.addAction(save_project_file_act)

        file_menu.addSeparator()

        # update_preview_act = QAction(self.tr("&Export songbook to PostScript..."), self)
        update_preview_act = self.ui.actionPreview
        update_preview_act.triggered.connect(self.update_preview)
        update_preview_act.setIcon(QIcon.fromTheme('system-run'))
        file_menu.addAction(update_preview_act)

        compile_songbook_act = QAction(self.tr("&Compile songbook"), self)
        compile_songbook_act.triggered.connect(self.run_chordii)
        file_menu.addAction(compile_songbook_act)

        file_menu.addSeparator()

        exit_act = QAction(QIcon.fromTheme('application-exit'), self.tr('E&xit'), self)
        exit_act.setShortcut(QKeySequence.Quit)
        exit_act.setStatusTip(self.tr('Exit application'))
        exit_act.triggered.connect(qApp.quit)
        file_menu.addAction(exit_act)

    def setup_file_widget(self):
        self.ui.fileWidget.itemSelectionChanged.connect(self.selection_changed)

    def setup_editor(self):
        self.ui.textEdit.set_main(self)
        self.ui.textEdit.textChanged.connect(self.set_dirty)

    def setup_geometry(self):
        available_geometry = QDesktopWidget().availableGeometry()

        width = available_geometry.width() * 4 / 5
        height = available_geometry.height() * 4 / 5
        splitter_size = 300
        self.ui.splitter.setSizes([splitter_size, (width - splitter_size) / 2, (width - splitter_size) / 2])
        self.resize(width, height)

        center_point = available_geometry.center()
        geometry = self.frameGeometry()
        geometry.moveCenter(center_point)
        self.move(geometry.topLeft())

    def selection_changed(self):
        if len(self.ui.fileWidget.selectedItems()) == 1:
            if self.ok_to_continue():
                self.open_file(self.ui.fileWidget.selectedItems()[0].data(Qt.UserRole))

    def closeEvent(self, event):
        """
        Ask to save, and remove temp_dir
        """
        if self.ok_to_continue():
            shutil.rmtree(self.temp_dir)
            event.accept()
        else:
            event.ignore()

    def set_dirty(self):
        """
        On change of text in textEdit window, set the flag "dirty" to True
        """
        if self.file_name:
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
        if self.file_name:
            file_base = os.path.basename(self.file_name)
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
                return self.save_file()
        return True

    def new_file(self):
        if not self.ok_to_continue():
            return
        self.file_name = QFileDialog.getSaveFileName(self, self.tr("New file"), QDir.homePath(),
                                                     self.tr("Chordii files (*.cho *.crd)"))
        if not self.file_name[1]:
            return
        self.save_file()
        if self.ui.textEdit.isReadOnly():
            self.ui.textEdit.setReadOnly(False)
        self.ui.textEdit.setText("{t:}\n{st:}")
        self.ui.textEdit.setFocus()
        self.statusBar().showMessage('New file', 5000)

    def open_file(self, path=""):
        if self.ui.textEdit.isReadOnly():
            self.ui.textEdit.setReadOnly(False)

        self.file_name = path

        if self.file_name != "":
            in_stream = codecs.open(self.file_name, "r", "ISO-8859-1")
            if in_stream:
                self.ui.textEdit.setPlainText(in_stream.read())
        self.clear_dirty()

        self.update_preview()

        self.update_status('File opened.')
        self.tab2chordpro()

    def update_preview(self):
        out_file = os.path.join(self.temp_dir, os.path.splitext(os.path.basename(self.file_name))[0])
        out_file = self.run_chordii(self.file_name, out_file, True)
        self.ui.scrollArea.load(out_file)

    def save_file(self):
        """
        Save file with current name.
        """
        if self.file_name is None:
            return self.save_file_as()
        else:
            if not self.dirty:
                return
            fname = self.file_name
            fl = codecs.open(fname, 'w', "ISO-8859-1")
            temp_text = self.ui.textEdit.toPlainText()
            if temp_text:
                fl.write(temp_text)
                fl.close()
                self.clear_dirty()
                self.update_status('Saved file')
                return True
            else:
                self.ui.statusBar.showMessage('Failed to save ...', 5000)
                return False

    def save_file_as(self):
        """
        Save file with a different name and maybe different directory.
        """
        path = self.file_name if self.file_name else self.working_dir
        fname = QFileDialog.getSaveFileName(self,
                                            self.tr("Save as..."), path, self.tr("Chordii files (*.cho *.crd)"))[0]
        if fname:
            print(fname)
            if "." not in fname:
                fname += ".cho"
            self.file_name = fname
            self.save_file()
            self.statusBar().showMessage('SaveAs file' + fname, 8000)
            self.clear_dirty()

    def select_dir(self):
        directory = QFileDialog.getExistingDirectory(self, self.tr("Choose working directory"),
                                                     self.working_dir if self.working_dir else QDir.homePath())
        self.open_dir(directory)

    def open_dir(self, directory):
        for fileType in ('cho', 'crd'):
            for filename in glob.iglob('{}/*.{}'.format(directory, fileType)):
                self.songbook.add_song(filename)
        self.open_project()

    def select_project(self):
        filename = QFileDialog.getOpenFileName(self, self.tr("Open project"), QDir.homePath(),
                                               self.tr("Chordii project files (*.chproj)"))
        if filename:
            self.load_project(filename)

    def load_project(self, filename):
        self.songbook = Songbook()
        self.songbook.load(filename)
        self.open_project()

    def open_project(self):
        self.ui.fileWidget.clear()
        missing_files = []
        for filename in self.songbook.songs:
            if not os.path.isfile(filename):
                missing_files.append(os.path.basename(filename))
                self.songbook.songs.remove(filename)
                continue
            item = QListWidgetItem(os.path.basename(filename))
            item.setData(Qt.UserRole, filename)
            item.setSizeHint(QSize(0, 30))
            self.ui.fileWidget.addItem(item)
        if missing_files:
            QMessageBox.warning(self, self.tr('Missing files'),
                                self.tr('The following project files were missing from the project directory:') +
                                '<ul>' +
                                ''.join(['<li>{}</li>'.format(filename) for filename in missing_files]) +
                                '</ul>')
        self.ui.statusBar.showMessage("Project opened.", 5000)

    def save_project(self):
        """
        Save the list of songs for later loading.
        """
        self.songbook.clear()
        for i in range(self.ui.fileWidget.count()):
            path = self.ui.fileWidget.item(i).data(Qt.UserRole)
            self.songbook.add_song(path)
        # filename = QFileDialog.getSaveFileName(self, self.tr("Save project"),
        #                                        self.project_file if self.project_file else QDir.homePath(),
        #                                        self.tr("Chordii project files (*.chproj)"))
        if self.project_file:
            self.project_file = self.project_file
            self.songbook.save(self.project_file)
        self.ui.statusBar.showMessage("Project saved.", 5000)

    def run_chordii(self, input_file=None, output_file=None, preview=False):
        """
        Run Chordii to produce output.
        :param input_file: The name of the chordpro file to compile. If None, all chordii files in the project will be
            compiled.
        :type input_file: str
        :param output_file: The filename of the resulting pdf. If None, a temp file will be created.
        :type output_file: str
        :param preview: Whether to compile a single song as a preview, or the whole project.
        :type preview: bool
        """

        chordii_command = which("chordii")
        if chordii_command is None:
            chordii_command = which("chordii430")
        if chordii_command is None:
            ret = QMessageBox.critical(self, self.tr(self.app_name + " - Chordii problem"),
                                       self.tr("Couldn't find a chordii executable in the PATH. \
                                       Please specify chordii's location to continue."),
                                       QMessageBox.Open | QMessageBox.Cancel, QMessageBox.Open)
            if ret == QMessageBox.Open:
                chordii_command = QFileDialog.getOpenFileName(self, self.tr("Specify the chordii executable"),
                                                              QDir.homePath())[0]
        command = [chordii_command, "-i", "-L", "-p", "1"] if not preview else [chordii_command]
        if not output_file:
            out_dir = os.path.join(self.working_dir, "output")
            output_file = os.path.join(out_dir, "songbook")
            if not os.path.exists(out_dir):
                os.makedirs(out_dir)
        if not input_file:
            for i in range(self.ui.fileWidget.count()):
                command.append(self.ui.fileWidget.item(i).data(Qt.UserRole))
        else:
            command.append(input_file)
        command.append("-o")
        command.append(output_file + '.ps')
        print('{}'.format(' '.join(map(str, command))))
        try:
            response = subprocess.check_output(command, stderr=subprocess.STDOUT).decode()
            if not preview:
                if response:
                    msg_box = WarningMessageBox()
                    msg_box.setWindowTitle(self.tr(self.app_name + " - Chordii warning"))
                    msg_box.setText(self.tr("Chordii exited with warnings."))
                    msg_box.setDetailedText(response)
                    msg_box.setIcon(QMessageBox.Warning)
                    msg_box.exec_()
                else:
                    QMessageBox.information(self, self.tr(self.app_name + " - Chordii was successful"),
                                            self.tr("Chordii compiled the songbook without warnings!"))
        except subprocess.CalledProcessError as e:
            if not preview:
                message = self.tr("Chordii crashed while compiling.")
                if e.stderr:
                    message += '<br' + self.tr("Chordii output:") + '<br><pre>' + e.stderr + '</pre>'
                else:
                    message += '<br>' + self.tr("Tip: This could be due to an incorrect chord definition.")
                QMessageBox.critical(self, self.tr(self.app_name + " - Chordii problem"), message)
        return ps2pdf(output_file)

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


def parse_arguments():
    parser = argparse.ArgumentParser(description='A Qt GUI for Chordii.')
    parser.add_argument('project', nargs='?', help='a project file to open')
    args = parser.parse_args()
    return args


if __name__ == "__main__":
    app = QApplication(sys.argv)

    qt_chordii = MainWindow()
    qt_chordii.show()

    app.exec_()
