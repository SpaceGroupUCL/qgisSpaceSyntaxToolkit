# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file '/Users/jorge/Dropbox/UCL/Development/C_Implementation/esstools/ui_Settings.ui'
#
# Created: Thu Jun 19 16:22:32 2014
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

class Ui_SettingsDialog(object):
    def setupUi(self, SettingsDialog):
        SettingsDialog.setObjectName(_fromUtf8("SettingsDialog"))
        SettingsDialog.resize(320, 230)
        SettingsDialog.setMinimumSize(QtCore.QSize(320, 230))
        self.verticalLayout_2 = QtGui.QVBoxLayout(SettingsDialog)
        self.verticalLayout_2.setObjectName(_fromUtf8("verticalLayout_2"))
        self.settingsTab = QtGui.QTabWidget(SettingsDialog)
        self.settingsTab.setObjectName(_fromUtf8("settingsTab"))
        self.editTab = QtGui.QWidget()
        self.editTab.setObjectName(_fromUtf8("editTab"))
        self.formLayout_2 = QtGui.QFormLayout(self.editTab)
        self.formLayout_2.setObjectName(_fromUtf8("formLayout_2"))
        self.axialThresholdLabel = QtGui.QLabel(self.editTab)
        self.axialThresholdLabel.setObjectName(_fromUtf8("axialThresholdLabel"))
        self.formLayout_2.setWidget(0, QtGui.QFormLayout.LabelRole, self.axialThresholdLabel)
        self.axialThresholdEdit = QtGui.QLineEdit(self.editTab)
        self.axialThresholdEdit.setObjectName(_fromUtf8("axialThresholdEdit"))
        self.formLayout_2.setWidget(0, QtGui.QFormLayout.FieldRole, self.axialThresholdEdit)
        self.axialMinimumLabel = QtGui.QLabel(self.editTab)
        self.axialMinimumLabel.setObjectName(_fromUtf8("axialMinimumLabel"))
        self.formLayout_2.setWidget(1, QtGui.QFormLayout.LabelRole, self.axialMinimumLabel)
        self.axialMinimumEdit = QtGui.QLineEdit(self.editTab)
        self.axialMinimumEdit.setObjectName(_fromUtf8("axialMinimumEdit"))
        self.formLayout_2.setWidget(1, QtGui.QFormLayout.FieldRole, self.axialMinimumEdit)
        self.unlinksThresholdLabel = QtGui.QLabel(self.editTab)
        self.unlinksThresholdLabel.setObjectName(_fromUtf8("unlinksThresholdLabel"))
        self.formLayout_2.setWidget(2, QtGui.QFormLayout.LabelRole, self.unlinksThresholdLabel)
        self.unlinksThresholdEdit = QtGui.QLineEdit(self.editTab)
        self.unlinksThresholdEdit.setObjectName(_fromUtf8("unlinksThresholdEdit"))
        self.formLayout_2.setWidget(2, QtGui.QFormLayout.FieldRole, self.unlinksThresholdEdit)
        self.linksThresholdLabel = QtGui.QLabel(self.editTab)
        self.linksThresholdLabel.setObjectName(_fromUtf8("linksThresholdLabel"))
        self.formLayout_2.setWidget(3, QtGui.QFormLayout.LabelRole, self.linksThresholdLabel)
        self.linksThresholdEdit = QtGui.QLineEdit(self.editTab)
        self.linksThresholdEdit.setObjectName(_fromUtf8("linksThresholdEdit"))
        self.formLayout_2.setWidget(3, QtGui.QFormLayout.FieldRole, self.linksThresholdEdit)
        self.settingsTab.addTab(self.editTab, _fromUtf8(""))
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
        self.verticalLayout_2.addWidget(self.settingsTab)
        self.closeButtonBox = QtGui.QDialogButtonBox(SettingsDialog)
        self.closeButtonBox.setOrientation(QtCore.Qt.Horizontal)
        self.closeButtonBox.setStandardButtons(QtGui.QDialogButtonBox.Cancel|QtGui.QDialogButtonBox.Ok)
        self.closeButtonBox.setObjectName(_fromUtf8("closeButtonBox"))
        self.verticalLayout_2.addWidget(self.closeButtonBox)

        self.retranslateUi(SettingsDialog)
        self.settingsTab.setCurrentIndex(0)
        QtCore.QObject.connect(self.closeButtonBox, QtCore.SIGNAL(_fromUtf8("accepted()")), SettingsDialog.accept)
        QtCore.QObject.connect(self.closeButtonBox, QtCore.SIGNAL(_fromUtf8("rejected()")), SettingsDialog.reject)
        QtCore.QMetaObject.connectSlotsByName(SettingsDialog)

    def retranslateUi(self, SettingsDialog):
        SettingsDialog.setWindowTitle(_translate("SettingsDialog", "Space Synatx Toolkit Settings", None))
        self.axialThresholdLabel.setText(_translate("SettingsDialog", "Axial crossing threshold (m)", None))
        self.axialMinimumLabel.setText(_translate("SettingsDialog", "Minimum axial length (m)", None))
        self.unlinksThresholdLabel.setText(_translate("SettingsDialog", "Unlinks crossing threshold (m)", None))
        self.linksThresholdLabel.setText(_translate("SettingsDialog", "Links touch threshold (m)", None))
        self.settingsTab.setTabText(self.settingsTab.indexOf(self.editTab), _translate("SettingsDialog", "Layer verification", None))
        self.engineHostLabel.setText(_translate("SettingsDialog", "Host IP", None))
        self.engineHostEdit.setText(_translate("SettingsDialog", "localhost", None))
        self.engineTestButton.setText(_translate("SettingsDialog", "Test", None))
        self.settingsTab.setTabText(self.settingsTab.indexOf(self.analysisTab), _translate("SettingsDialog", "depthmapXnet", None))

import resources_rc
