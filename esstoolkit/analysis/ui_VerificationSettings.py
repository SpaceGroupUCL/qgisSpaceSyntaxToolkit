# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'analysis/ui_VerificationSettings.ui'
#
# Created by: PyQt4 UI code generator 4.11.4
#
# WARNING! All changes made in this file will be lost!

from __future__ import absolute_import
from builtins import object
from qgis.PyQt import QtCore, QtGui

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

class Ui_VerificationSettingsDialog(object):
    def setupUi(self, VerificationSettingsDialog):
        VerificationSettingsDialog.setObjectName(_fromUtf8("VerificationSettingsDialog"))
        VerificationSettingsDialog.setWindowModality(QtCore.Qt.ApplicationModal)
        VerificationSettingsDialog.resize(320, 180)
        VerificationSettingsDialog.setMinimumSize(QtCore.QSize(320, 180))
        self.gridLayout = QtGui.QGridLayout(VerificationSettingsDialog)
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
        self.axialThresholdLabel = QtGui.QLabel(VerificationSettingsDialog)
        self.axialThresholdLabel.setAlignment(QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft|QtCore.Qt.AlignVCenter)
        self.axialThresholdLabel.setObjectName(_fromUtf8("axialThresholdLabel"))
        self.gridLayout.addWidget(self.axialThresholdLabel, 0, 0, 1, 1)
        self.axialThresholdEdit = QtGui.QLineEdit(VerificationSettingsDialog)
        self.axialThresholdEdit.setObjectName(_fromUtf8("axialThresholdEdit"))
        self.gridLayout.addWidget(self.axialThresholdEdit, 0, 1, 1, 1)
        self.axialMinimumLabel = QtGui.QLabel(VerificationSettingsDialog)
        self.axialMinimumLabel.setObjectName(_fromUtf8("axialMinimumLabel"))
        self.gridLayout.addWidget(self.axialMinimumLabel, 1, 0, 1, 1)
        self.axialMinimumEdit = QtGui.QLineEdit(VerificationSettingsDialog)
        self.axialMinimumEdit.setObjectName(_fromUtf8("axialMinimumEdit"))
        self.gridLayout.addWidget(self.axialMinimumEdit, 1, 1, 1, 1)
        self.unlinksThresholdLabel = QtGui.QLabel(VerificationSettingsDialog)
        self.unlinksThresholdLabel.setObjectName(_fromUtf8("unlinksThresholdLabel"))
        self.gridLayout.addWidget(self.unlinksThresholdLabel, 2, 0, 1, 1)
        self.unlinksThresholdEdit = QtGui.QLineEdit(VerificationSettingsDialog)
        self.unlinksThresholdEdit.setObjectName(_fromUtf8("unlinksThresholdEdit"))
        self.gridLayout.addWidget(self.unlinksThresholdEdit, 2, 1, 1, 1)
        self.linksThresholdEdit = QtGui.QLineEdit(VerificationSettingsDialog)
        self.linksThresholdEdit.setObjectName(_fromUtf8("linksThresholdEdit"))
        self.gridLayout.addWidget(self.linksThresholdEdit, 3, 1, 1, 1)
        self.closeButtonBox = QtGui.QDialogButtonBox(VerificationSettingsDialog)
        self.closeButtonBox.setOrientation(QtCore.Qt.Horizontal)
        self.closeButtonBox.setStandardButtons(QtGui.QDialogButtonBox.Cancel|QtGui.QDialogButtonBox.Ok)
        self.closeButtonBox.setObjectName(_fromUtf8("closeButtonBox"))
        self.gridLayout.addWidget(self.closeButtonBox, 4, 0, 1, 2)
        self.linksThresholdLabel = QtGui.QLabel(VerificationSettingsDialog)
        self.linksThresholdLabel.setObjectName(_fromUtf8("linksThresholdLabel"))
        self.gridLayout.addWidget(self.linksThresholdLabel, 3, 0, 1, 1)

        self.retranslateUi(VerificationSettingsDialog)
        QtCore.QObject.connect(self.closeButtonBox, QtCore.SIGNAL(_fromUtf8("accepted()")), VerificationSettingsDialog.accept)
        QtCore.QObject.connect(self.closeButtonBox, QtCore.SIGNAL(_fromUtf8("rejected()")), VerificationSettingsDialog.reject)
        QtCore.QMetaObject.connectSlotsByName(VerificationSettingsDialog)

    def retranslateUi(self, VerificationSettingsDialog):
        VerificationSettingsDialog.setWindowTitle(_translate("VerificationSettingsDialog", "Layer Verification Settings", None))
        self.axialThresholdLabel.setText(_translate("VerificationSettingsDialog", "Axial crossing threshold (m)", None))
        self.axialMinimumLabel.setText(_translate("VerificationSettingsDialog", "Minimum axial length (m)", None))
        self.unlinksThresholdLabel.setText(_translate("VerificationSettingsDialog", "Unlinks crossing threshold (m)", None))
        self.linksThresholdLabel.setText(_translate("VerificationSettingsDialog", "Links touch threshold (m)", None))

from . import resources_rc
