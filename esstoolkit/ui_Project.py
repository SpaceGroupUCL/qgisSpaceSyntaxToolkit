# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file '/Users/jorge/github/qgisSpaceSyntaxToolkit/esstoolkit/ui_Project.ui'
#
# Created: Fri Jul  3 20:13:55 2015
#      by: PyQt4 UI code generator 4.10.3
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s

try:
    _encoding = QtGui.QApplication.UnicodeUTF8
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig, _encoding)
except AttributeError:
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig)

class Ui_ProjectDialog(object):
    def setupUi(self, ProjectDialog):
        ProjectDialog.setObjectName(_fromUtf8("ProjectDialog"))
        ProjectDialog.setWindowModality(QtCore.Qt.ApplicationModal)
        ProjectDialog.resize(350, 220)
        ProjectDialog.setMinimumSize(QtCore.QSize(320, 220))
        self.verticalLayout = QtGui.QVBoxLayout(ProjectDialog)
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.datastoreBox = QtGui.QGroupBox(ProjectDialog)
        font = QtGui.QFont()
        font.setPointSize(13)
        self.datastoreBox.setFont(font)
        self.datastoreBox.setObjectName(_fromUtf8("datastoreBox"))
        self.gridLayout = QtGui.QGridLayout(self.datastoreBox)
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
        self.dataTypeCombo = QtGui.QComboBox(self.datastoreBox)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.MinimumExpanding, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.dataTypeCombo.sizePolicy().hasHeightForWidth())
        self.dataTypeCombo.setSizePolicy(sizePolicy)
        self.dataTypeCombo.setObjectName(_fromUtf8("dataTypeCombo"))
        self.dataTypeCombo.addItem(_fromUtf8(""))
        self.dataTypeCombo.addItem(_fromUtf8(""))
        self.gridLayout.addWidget(self.dataTypeCombo, 0, 1, 1, 2)
        self.dataNewButton = QtGui.QPushButton(self.datastoreBox)
        self.dataNewButton.setObjectName(_fromUtf8("dataNewButton"))
        self.gridLayout.addWidget(self.dataNewButton, 5, 1, 1, 1)
        self.dataOpenButton = QtGui.QPushButton(self.datastoreBox)
        self.dataOpenButton.setObjectName(_fromUtf8("dataOpenButton"))
        self.gridLayout.addWidget(self.dataOpenButton, 5, 2, 1, 1)
        self.dataTypeLabel = QtGui.QLabel(self.datastoreBox)
        self.dataTypeLabel.setObjectName(_fromUtf8("dataTypeLabel"))
        self.gridLayout.addWidget(self.dataTypeLabel, 0, 0, 1, 1)
        self.dataSelectLabel = QtGui.QLabel(self.datastoreBox)
        self.dataSelectLabel.setObjectName(_fromUtf8("dataSelectLabel"))
        self.gridLayout.addWidget(self.dataSelectLabel, 1, 0, 1, 1)
        self.dataSelectCombo = QtGui.QComboBox(self.datastoreBox)
        self.dataSelectCombo.setObjectName(_fromUtf8("dataSelectCombo"))
        self.gridLayout.addWidget(self.dataSelectCombo, 1, 1, 1, 2)
        self.schemaLabel = QtGui.QLabel(self.datastoreBox)
        self.schemaLabel.setObjectName(_fromUtf8("schemaLabel"))
        self.gridLayout.addWidget(self.schemaLabel, 3, 0, 1, 1)
        self.schemaCombo = QtGui.QComboBox(self.datastoreBox)
        self.schemaCombo.setObjectName(_fromUtf8("schemaCombo"))
        self.gridLayout.addWidget(self.schemaCombo, 3, 1, 1, 2)
        self.gridLayout.setColumnStretch(1, 3)
        self.gridLayout.setColumnStretch(2, 3)
        self.verticalLayout.addWidget(self.datastoreBox)
        self.closeButtonBox = QtGui.QDialogButtonBox(ProjectDialog)
        self.closeButtonBox.setOrientation(QtCore.Qt.Horizontal)
        self.closeButtonBox.setStandardButtons(QtGui.QDialogButtonBox.Cancel|QtGui.QDialogButtonBox.Ok)
        self.closeButtonBox.setObjectName(_fromUtf8("closeButtonBox"))
        self.verticalLayout.addWidget(self.closeButtonBox)

        self.retranslateUi(ProjectDialog)
        QtCore.QObject.connect(self.closeButtonBox, QtCore.SIGNAL(_fromUtf8("accepted()")), ProjectDialog.accept)
        QtCore.QObject.connect(self.closeButtonBox, QtCore.SIGNAL(_fromUtf8("rejected()")), ProjectDialog.reject)
        QtCore.QMetaObject.connectSlotsByName(ProjectDialog)

    def retranslateUi(self, ProjectDialog):
        ProjectDialog.setWindowTitle(_translate("ProjectDialog", "Project Settings", None))
        self.datastoreBox.setTitle(_translate("ProjectDialog", "Project data store", None))
        self.dataTypeCombo.setItemText(0, _translate("ProjectDialog", "Personal geodatabase", None))
        self.dataTypeCombo.setItemText(1, _translate("ProjectDialog", "Shape files folder", None))
        self.dataNewButton.setText(_translate("ProjectDialog", "New...", None))
        self.dataOpenButton.setText(_translate("ProjectDialog", "Open...", None))
        self.dataTypeLabel.setText(_translate("ProjectDialog", "Type", None))
        self.dataSelectLabel.setText(_translate("ProjectDialog", "Select", None))
        self.schemaLabel.setText(_translate("ProjectDialog", "Schema", None))

import resources_rc
