# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file '/Users/jorge/github/qgisSpaceSyntaxToolkit/esstoolkit/analysis/ui_DepthmapAdvanced.ui'
#
# Created: Fri Jun 12 10:33:43 2015
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

class Ui_DepthmapAdvancedDialog(object):
    def setupUi(self, DepthmapAdvancedDialog):
        DepthmapAdvancedDialog.setObjectName(_fromUtf8("DepthmapAdvancedDialog"))
        DepthmapAdvancedDialog.resize(280, 230)
        DepthmapAdvancedDialog.setMinimumSize(QtCore.QSize(280, 230))
        self.gridLayout = QtGui.QGridLayout(DepthmapAdvancedDialog)
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
        self.axialCalculateChoiceCheck = QtGui.QCheckBox(DepthmapAdvancedDialog)
        self.axialCalculateChoiceCheck.setObjectName(_fromUtf8("axialCalculateChoiceCheck"))
        self.gridLayout.addWidget(self.axialCalculateChoiceCheck, 1, 0, 1, 2)
        self.axialDistanceCombo = QtGui.QComboBox(DepthmapAdvancedDialog)
        self.axialDistanceCombo.setObjectName(_fromUtf8("axialDistanceCombo"))
        self.axialDistanceCombo.addItem(_fromUtf8(""))
        self.axialDistanceCombo.addItem(_fromUtf8(""))
        self.axialDistanceCombo.addItem(_fromUtf8(""))
        self.gridLayout.addWidget(self.axialDistanceCombo, 3, 1, 1, 1)
        self.axialCalculateFullCheck = QtGui.QCheckBox(DepthmapAdvancedDialog)
        self.axialCalculateFullCheck.setObjectName(_fromUtf8("axialCalculateFullCheck"))
        self.gridLayout.addWidget(self.axialCalculateFullCheck, 0, 0, 1, 2)
        self.closeButtonBox = QtGui.QDialogButtonBox(DepthmapAdvancedDialog)
        self.closeButtonBox.setOrientation(QtCore.Qt.Horizontal)
        self.closeButtonBox.setStandardButtons(QtGui.QDialogButtonBox.Cancel|QtGui.QDialogButtonBox.Ok)
        self.closeButtonBox.setObjectName(_fromUtf8("closeButtonBox"))
        self.gridLayout.addWidget(self.closeButtonBox, 6, 0, 1, 2)
        self.axialCalculateNormCheck = QtGui.QCheckBox(DepthmapAdvancedDialog)
        self.axialCalculateNormCheck.setObjectName(_fromUtf8("axialCalculateNormCheck"))
        self.gridLayout.addWidget(self.axialCalculateNormCheck, 2, 0, 1, 2)
        self.axialDistanceLabel = QtGui.QLabel(DepthmapAdvancedDialog)
        self.axialDistanceLabel.setObjectName(_fromUtf8("axialDistanceLabel"))
        self.gridLayout.addWidget(self.axialDistanceLabel, 3, 0, 1, 1)
        self.axialRadiusCombo = QtGui.QComboBox(DepthmapAdvancedDialog)
        self.axialRadiusCombo.setObjectName(_fromUtf8("axialRadiusCombo"))
        self.axialRadiusCombo.addItem(_fromUtf8(""))
        self.axialRadiusCombo.addItem(_fromUtf8(""))
        self.axialRadiusCombo.addItem(_fromUtf8(""))
        self.gridLayout.addWidget(self.axialRadiusCombo, 4, 1, 1, 1)
        self.axialRadiusLabel = QtGui.QLabel(DepthmapAdvancedDialog)
        self.axialRadiusLabel.setObjectName(_fromUtf8("axialRadiusLabel"))
        self.gridLayout.addWidget(self.axialRadiusLabel, 4, 0, 1, 1)
        self.axialStubsLabel = QtGui.QLabel(DepthmapAdvancedDialog)
        self.axialStubsLabel.setObjectName(_fromUtf8("axialStubsLabel"))
        self.gridLayout.addWidget(self.axialStubsLabel, 5, 0, 1, 1)
        self.axialStubsEdit = QtGui.QLineEdit(DepthmapAdvancedDialog)
        self.axialStubsEdit.setPlaceholderText(_fromUtf8(""))
        self.axialStubsEdit.setObjectName(_fromUtf8("axialStubsEdit"))
        self.gridLayout.addWidget(self.axialStubsEdit, 5, 1, 1, 1)
        self.gridLayout.setColumnMinimumWidth(1, 1)
        self.gridLayout.setColumnStretch(1, 1)

        self.retranslateUi(DepthmapAdvancedDialog)
        QtCore.QObject.connect(self.closeButtonBox, QtCore.SIGNAL(_fromUtf8("accepted()")), DepthmapAdvancedDialog.accept)
        QtCore.QObject.connect(self.closeButtonBox, QtCore.SIGNAL(_fromUtf8("rejected()")), DepthmapAdvancedDialog.reject)
        QtCore.QMetaObject.connectSlotsByName(DepthmapAdvancedDialog)

    def retranslateUi(self, DepthmapAdvancedDialog):
        DepthmapAdvancedDialog.setWindowTitle(_translate("DepthmapAdvancedDialog", "Advanced Settings", None))
        self.axialCalculateChoiceCheck.setText(_translate("DepthmapAdvancedDialog", "Calculate choice", None))
        self.axialDistanceCombo.setItemText(0, _translate("DepthmapAdvancedDialog", "Topological", None))
        self.axialDistanceCombo.setItemText(1, _translate("DepthmapAdvancedDialog", "Angular", None))
        self.axialDistanceCombo.setItemText(2, _translate("DepthmapAdvancedDialog", "Metric", None))
        self.axialCalculateFullCheck.setText(_translate("DepthmapAdvancedDialog", "Calculate full set of measures", None))
        self.axialCalculateNormCheck.setText(_translate("DepthmapAdvancedDialog", "Calculate NACH and NAIN", None))
        self.axialDistanceLabel.setText(_translate("DepthmapAdvancedDialog", "Distance type:", None))
        self.axialRadiusCombo.setItemText(0, _translate("DepthmapAdvancedDialog", "Topological", None))
        self.axialRadiusCombo.setItemText(1, _translate("DepthmapAdvancedDialog", "Angular", None))
        self.axialRadiusCombo.setItemText(2, _translate("DepthmapAdvancedDialog", "Metric", None))
        self.axialRadiusLabel.setText(_translate("DepthmapAdvancedDialog", "Radius type:", None))
        self.axialStubsLabel.setText(_translate("DepthmapAdvancedDialog", "Stubs removal %:", None))

import resources_rc
