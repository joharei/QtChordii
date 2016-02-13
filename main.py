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
import os
import re
import shutil
import subprocess
import sys
import tempfile

from PyQt5 import uic
from PyQt5.QtCore import Qt, QDir, QSize, QT_TRANSLATE_NOOP
from PyQt5.QtGui import QKeySequence
from PyQt5.QtWidgets import QApplication, qApp, QMessageBox, QFileDialog, QMainWindow, QDesktopWidget, QTableWidgetItem

from gui.warningmessagebox import WarningMessageBox
from gui.welcomedialog import WelcomeDialog
from model.songbook import Songbook
from settings import settings
from tab2chordpro.Transpose import testTabFormat, tab2ChordPro, enNotation
from utils.ps2pdf import ps2pdf
from utils.which import which

CHORDPRO_FILTER = QT_TRANSLATE_NOOP('MainWindow', 'ChordPro files (*.cho *.crd)')


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = uic.loadUi('gui/qtchordii/mainwindow.ui', self)

        settings.set_up_settings()
        self.app_name = settings.APPLICATION_NAME

        args = parse_arguments()

        self.file_name = None
        self.songbook = Songbook()
        if args.project:
            self.project_file = os.path.abspath(args.project)
        else:
            self.project_file = settings.load_project_file()
            if not self.project_file:
                self.project_file, new_file = WelcomeDialog.get_project(self)
                if not self.project_file:
                    sys.exit(0)
                if new_file:
                    self.save_project()

        self.load_project(self.project_file)

        self.temp_dir = tempfile.mkdtemp()

        self.setup_file_widget()
        self.setup_editor()
        self.setup_file_menu()
        self.setup_geometry()
        self.dirty = False

    def setup_file_menu(self):
        new_file_act = self.ui.actionNew
        new_file_act.setShortcut(QKeySequence.New)
        new_file_act.triggered.connect(self.new_file)

        import_files_act = self.ui.actionImport
        import_files_act.setShortcut(QKeySequence.Open)
        import_files_act.triggered.connect(self.import_chordpro_files)

        save_file_act = self.ui.actionSave
        save_file_act.setShortcut(QKeySequence.Save)
        save_file_act.triggered.connect(self.save_file)

        save_file_as_act = self.ui.actionSave_As
        save_file_as_act.setShortcut(QKeySequence.SaveAs)
        save_file_as_act.triggered.connect(self.save_file_as)

        load_project_file_act = self.ui.actionLoad_Project
        load_project_file_act.triggered.connect(self.select_project)

        save_project_file_act = self.ui.actionSave_Project
        save_project_file_act.triggered.connect(self.save_project)

        update_preview_act = self.ui.actionPreview
        update_preview_act.triggered.connect(self.update_preview)

        compile_songbook_act = self.ui.actionCompile_Songbook
        compile_songbook_act.triggered.connect(self.run_chordii)

        exit_act = self.ui.actionExit
        exit_act.setShortcut(QKeySequence.Quit)
        exit_act.triggered.connect(qApp.quit)

    def setup_file_widget(self):
        # TODO: Fix this
        # self.ui.fileWidget.resizeColumnsToContents()
        self.ui.fileWidget.itemSelectionChanged.connect(self.selection_changed)

    def setup_editor(self):
        self.ui.textEdit.set_main(self)
        self.ui.textEdit.textChanged.connect(self.set_dirty)

    def setup_geometry(self):
        geometries = settings.load_window_geometry()
        size = geometries[settings.key_size]
        if not size:
            size = QDesktopWidget().availableGeometry().size() * 4 / 5
        self.resize(size)

        is_full_screen = geometries[settings.key_is_full_screen]
        if is_full_screen:
            self.showFullScreen()

        splitter_sizes = geometries[settings.key_splitter_sizes]
        if not splitter_sizes:
            width = size.width()
            splitter_size = width * .2
            splitter_sizes = [splitter_size, (width - splitter_size) / 2, (width - splitter_size) / 2]
        self.ui.splitter.setSizes(splitter_sizes)

        pos = geometries[settings.key_pos]
        if not pos:
            center_point = QDesktopWidget().availableGeometry().center()
            geometry = self.frameGeometry()
            geometry.moveCenter(center_point)
            pos = geometry.topLeft()
        self.move(pos)

    def selection_changed(self):
        if len(self.ui.fileWidget.selectedItems()) == 2:
            if self.ok_to_continue():
                self.open_file(self.ui.fileWidget.selectedItems()[0].data(Qt.UserRole))

    def closeEvent(self, event):
        """
        Ask to save ChordPro file, save window geometry, and remove temp_dir
        """
        if self.ok_to_continue():
            settings.save_window_geometry(self.size(), self.pos(), self.isFullScreen(), self.ui.splitter.sizes())
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
            self.update_status('')

    def clear_dirty(self):
        """Clear the dirty."""
        self.dirty = False
        self.update_status('')

    def update_status(self, message):
        """
        Keep status current.
        """
        if self.file_name:
            file_base = os.path.basename(self.file_name)
            self.setWindowTitle(file_base + ' [*]' + ' — ' + self.app_name)
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
                                                     self.tr(CHORDPRO_FILTER))
        if not self.file_name[1]:
            return
        self.save_file()
        if self.ui.textEdit.isReadOnly():
            self.ui.textEdit.setReadOnly(False)
        self.ui.textEdit.setText("{t:}\n{st:}")
        self.ui.textEdit.setFocus()
        self.statusBar().showMessage('New file', 5000)

    def open_file(self, path=None):
        if self.ui.textEdit.isReadOnly():
            self.ui.textEdit.setReadOnly(False)

        self.file_name = path

        if self.file_name:
            in_stream = codecs.open(self.file_name, "r", "ISO-8859-1")
            if in_stream:
                self.ui.textEdit.setPlainText(in_stream.read())
        self.clear_dirty()

        self.update_preview()

        self.update_status('File opened.')
        self.tab2chordpro()

    def update_preview(self):
        if self.file_name:
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
        path = self.file_name if self.file_name else os.path.dirname(self.project_file)
        fname = QFileDialog.getSaveFileName(self, self.tr("Save as..."), path, self.tr(CHORDPRO_FILTER))[0]
        if fname:
            print(fname)
            if "." not in fname:
                fname += ".cho"
            self.file_name = fname
            self.save_file()
            self.clear_dirty()

    def import_chordpro_files(self):
        working_dir = os.path.dirname(self.project_file)
        file_paths = QFileDialog.getOpenFileNames(self, self.tr("Choose files to import"),
                                                  working_dir if working_dir else QDir.homePath(),
                                                  self.tr(CHORDPRO_FILTER))[0]
        if not file_paths:
            return
        title_regex = re.compile(r'\{(?:t|title):(.+)\}')
        artist_regex = re.compile(r'\{(?:st|subtitle):(.+)\}')
        for file_path in file_paths:
            unknown = self.tr('Unknown')
            title = artist = unknown
            for line in open(file_path, 'r', encoding='ISO-8859-1'):
                match = title_regex.match(line)
                if match:
                    title = match.group(1).strip()
                match = artist_regex.match(line)
                if match:
                    artist = match.group(1).strip()
                if unknown not in (title, artist):
                    break
            self.songbook.add_song(title, artist, file_path)
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
        settings.save_project_file(filename)

    def open_project(self):
        self.ui.fileWidget.clearContents()
        missing_songs = []
        for song in self.songbook.songs:
            if not os.path.isfile(song.file_path):
                missing_songs.append(song)
                self.songbook.songs.remove(song)
                continue
            self.add_song(song.title, song.artist, song.file_path)
        if missing_songs:
            QMessageBox.warning(self, self.tr('Missing files'),
                                self.tr('The following project files were missing:') +
                                '<ul>' +
                                ''.join(['<li>{} - {} ({})</li>'.format(song.artist, song.title, song.file_path)
                                         for song in missing_songs]) + '</ul>')
        self.ui.statusBar.showMessage("Project opened.", 5000)

    def add_song(self, song_title, song_artist, song_path):
        title = QTableWidgetItem(song_title)
        title.setData(Qt.UserRole, song_path)
        title.setSizeHint(QSize(0, 30))
        artist = QTableWidgetItem(song_artist)
        row = self.ui.fileWidget.rowCount()
        self.ui.fileWidget.insertRow(row)
        self.ui.fileWidget.setItem(row, 0, title)
        self.ui.fileWidget.setItem(row, 1, artist)

    def save_project(self):
        """
        Save the list of songs for later loading.
        """
        if self.project_file:
            self.songbook.save(self.project_file)
        self.ui.statusBar.showMessage("Project saved.", 5000)

    def run_chordii(self, input_file=None, output_file=None, preview=False):
        """
        Run Chordii to produce output.
        :param input_file: The name of the ChordPro file to compile. If None, all chordii files in the project will be
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
            out_dir = os.path.join(os.path.dirname(self.project_file), "output")
            output_file = os.path.join(out_dir, self.songbook.name)
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
