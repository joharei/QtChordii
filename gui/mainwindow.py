# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'qtchordii/mainwindow.ui'
#
# Created: Sun Aug  4 20:15:47 2013
#      by: pyside-uic 0.2.14 running on PySide 1.2.0
#
# WARNING! All changes made in this file will be lost!

from PySide import QtCore, QtGui

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(1018, 568)
        self.centralWidget = QtGui.QWidget(MainWindow)
        self.centralWidget.setObjectName("centralWidget")
        self.gridLayout = QtGui.QGridLayout(self.centralWidget)
        self.gridLayout.setObjectName("gridLayout")
        self.splitter = QtGui.QSplitter(self.centralWidget)
        self.splitter.setOrientation(QtCore.Qt.Horizontal)
        self.splitter.setObjectName("splitter")
        self.fileWidget = QtGui.QListWidget(self.splitter)
        self.fileWidget.setAcceptDrops(True)
        self.fileWidget.setDragEnabled(True)
        self.fileWidget.setDragDropMode(QtGui.QAbstractItemView.InternalMove)
        self.fileWidget.setDefaultDropAction(QtCore.Qt.MoveAction)
        self.fileWidget.setSelectionMode(QtGui.QAbstractItemView.ContiguousSelection)
        self.fileWidget.setObjectName("fileWidget")
        self.textEdit = CustomTextEdit(self.splitter)
        self.textEdit.setStyleSheet("font: 9pt \"DejaVu Sans Mono\";")
        self.textEdit.setObjectName("textEdit")
        self.gridLayout.addWidget(self.splitter, 0, 0, 1, 1)
        MainWindow.setCentralWidget(self.centralWidget)
        self.menuBar = QtGui.QMenuBar(MainWindow)
        self.menuBar.setGeometry(QtCore.QRect(0, 0, 1018, 20))
        self.menuBar.setObjectName("menuBar")
        MainWindow.setMenuBar(self.menuBar)
        self.mainToolBar = QtGui.QToolBar(MainWindow)
        self.mainToolBar.setObjectName("mainToolBar")
        MainWindow.addToolBar(QtCore.Qt.TopToolBarArea, self.mainToolBar)
        self.statusBar = QtGui.QStatusBar(MainWindow)
        self.statusBar.setObjectName("statusBar")
        MainWindow.setStatusBar(self.statusBar)

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QtGui.QApplication.translate("MainWindow", "QtChordii", None, QtGui.QApplication.UnicodeUTF8))

from gui.customtextedit import CustomTextEdit
