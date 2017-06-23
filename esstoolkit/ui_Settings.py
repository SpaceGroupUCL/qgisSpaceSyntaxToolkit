# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ui_Settings.ui'
#
# Created by: PyQt4 UI code generator 4.11.4
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

class Ui_SettingsDialog(object):
    def setupUi(self, SettingsDialog):
        SettingsDialog.setObjectName(_fromUtf8("SettingsDialog"))
        SettingsDialog.setWindowModality(QtCore.Qt.ApplicationModal)
        SettingsDialog.resize(320, 375)
        SettingsDialog.setMinimumSize(QtCore.QSize(320, 230))
        self.verticalLayout_2 = QtGui.QVBoxLayout(SettingsDialog)
        self.verticalLayout_2.setObjectName(_fromUtf8("verticalLayout_2"))
        self.settingsTab = QtGui.QTabWidget(SettingsDialog)
        self.settingsTab.setEnabled(True)
        self.settingsTab.setObjectName(_fromUtf8("settingsTab"))
        self.analysisTab = QtGui.QWidget()
        self.analysisTab.setObjectName(_fromUtf8("analysisTab"))
        self.formLayout = QtGui.QFormLayout(self.analysisTab)
        self.formLayout.setObjectName(_fromUtf8("formLayout"))
        self.engineHostLabel = QtGui.QLabel(self.analysisTab)
        self.engineHostLabel.setObjectName(_fromUtf8("engineHostLabel"))
        self.formLayout.setWidget(0, QtGui.QFormLayout.LabelRole, self.engineHostLabel)
        self.engineHostEdit = QtGui.QLineEdit(self.analysisTab)
        self.engineHostEdit.setObjectName(_fromUtf8("engineHostEdit"))
        self.formLayout.setWidget(0, QtGui.QFormLayout.FieldRole, self.engineHostEdit)
        self.engineTestButton = QtGui.QPushButton(self.analysisTab)
        self.engineTestButton.setObjectName(_fromUtf8("engineTestButton"))
        self.formLayout.setWidget(1, QtGui.QFormLayout.LabelRole, self.engineTestButton)
        self.engineTestText = QtGui.QLineEdit(self.analysisTab)
        self.engineTestText.setEnabled(True)
        self.engineTestText.setFrame(False)
        self.engineTestText.setReadOnly(True)
        self.engineTestText.setObjectName(_fromUtf8("engineTestText"))
        self.formLayout.setWidget(1, QtGui.QFormLayout.FieldRole, self.engineTestText)
        self.settingsTab.addTab(self.analysisTab, _fromUtf8(""))
        self.explorerTab = QtGui.QWidget()
        self.explorerTab.setObjectName(_fromUtf8("explorerTab"))
        self.formLayout_2 = QtGui.QFormLayout(self.explorerTab)
        self.formLayout_2.setObjectName(_fromUtf8("formLayout_2"))
        self.colourCombo = QtGui.QComboBox(self.explorerTab)
        self.colourCombo.setObjectName(_fromUtf8("colourCombo"))
        self.colourCombo.addItem(_fromUtf8(""))
        self.colourCombo.addItem(_fromUtf8(""))
        self.colourCombo.addItem(_fromUtf8(""))
        self.colourCombo.addItem(_fromUtf8(""))
        self.colourCombo.addItem(_fromUtf8(""))
        self.formLayout_2.setWidget(2, QtGui.QFormLayout.LabelRole, self.colourCombo)
        self.colourLabel = QtGui.QLabel(self.explorerTab)
        self.colourLabel.setObjectName(_fromUtf8("colourLabel"))
        self.formLayout_2.setWidget(1, QtGui.QFormLayout.LabelRole, self.colourLabel)
        self.settingsTab.addTab(self.explorerTab, _fromUtf8(""))
        self.verticalLayout_2.addWidget(self.settingsTab)
        self.closeButtonBox = QtGui.QDialogButtonBox(SettingsDialog)
        self.closeButtonBox.setOrientation(QtCore.Qt.Horizontal)
        self.closeButtonBox.setStandardButtons(QtGui.QDialogButtonBox.Cancel|QtGui.QDialogButtonBox.Ok)
        self.closeButtonBox.setObjectName(_fromUtf8("closeButtonBox"))
        self.verticalLayout_2.addWidget(self.closeButtonBox)

        self.retranslateUi(SettingsDialog)
        self.settingsTab.setCurrentIndex(1)
        QtCore.QObject.connect(self.closeButtonBox, QtCore.SIGNAL(_fromUtf8("accepted()")), SettingsDialog.accept)
        QtCore.QObject.connect(self.closeButtonBox, QtCore.SIGNAL(_fromUtf8("rejected()")), SettingsDialog.reject)
        QtCore.QMetaObject.connectSlotsByName(SettingsDialog)

    def retranslateUi(self, SettingsDialog):
        SettingsDialog.setWindowTitle(_translate("SettingsDialog", "Space Synatx Toolkit Settings", None))
        self.engineHostLabel.setText(_translate("SettingsDialog", "depthmapXnet IP", None))
        self.engineHostEdit.setText(_translate("SettingsDialog", "localhost", None))
        self.engineTestButton.setText(_translate("SettingsDialog", "Test", None))
        self.settingsTab.setTabText(self.settingsTab.indexOf(self.analysisTab), _translate("SettingsDialog", "Graph Analysis", None))
        self.colourCombo.setItemText(0, _translate("SettingsDialog", "Classic", None))
        self.colourCombo.setItemText(1, _translate("SettingsDialog", "Red - blue", None))
        self.colourCombo.setItemText(2, _translate("SettingsDialog", "Greyscale", None))
        self.colourCombo.setItemText(3, _translate("SettingsDialog", "Monochrome", None))
        self.colourCombo.setItemText(4, _translate("SettingsDialog", "Classic inflection", None))
        self.colourLabel.setText(_translate("SettingsDialog", "Default colour range:", None))
        self.settingsTab.setTabText(self.settingsTab.indexOf(self.explorerTab), _translate("SettingsDialog", "Explorer", None))

import resources_rc
