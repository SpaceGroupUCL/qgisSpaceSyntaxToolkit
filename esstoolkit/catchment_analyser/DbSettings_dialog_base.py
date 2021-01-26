# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'DbSettings_dialog_base.ui'
#
# Created by: PyQt4 UI code generator 4.11.4
#
# WARNING! All changes made in this file will be lost!

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

class Ui_DbSettingsDialogBase(object):
    def setupUi(self, DbSettingsDialogBase):
        DbSettingsDialogBase.setObjectName(_fromUtf8("DbSettingsDialogBase"))
        DbSettingsDialogBase.resize(285, 166)
        self.layoutWidget = QtGui.QWidget(DbSettingsDialogBase)
        self.layoutWidget.setGeometry(QtCore.QRect(10, 10, 261, 141))
        self.layoutWidget.setObjectName(_fromUtf8("layoutWidget"))
        self.verticalLayout = QtGui.QVBoxLayout(self.layoutWidget)
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.gridLayout = QtGui.QGridLayout()
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
        self.label_5 = QtGui.QLabel(self.layoutWidget)
        self.label_5.setObjectName(_fromUtf8("label_5"))
        self.gridLayout.addWidget(self.label_5, 0, 0, 1, 1)
        self.dbCombo = QtGui.QComboBox(self.layoutWidget)
        self.dbCombo.setObjectName(_fromUtf8("dbCombo"))
        self.gridLayout.addWidget(self.dbCombo, 0, 1, 1, 1)
        self.label_6 = QtGui.QLabel(self.layoutWidget)
        self.label_6.setObjectName(_fromUtf8("label_6"))
        self.gridLayout.addWidget(self.label_6, 1, 0, 1, 1)
        self.schemaCombo = QtGui.QComboBox(self.layoutWidget)
        self.schemaCombo.setObjectName(_fromUtf8("schemaCombo"))
        self.gridLayout.addWidget(self.schemaCombo, 1, 1, 1, 1)
        self.label_7 = QtGui.QLabel(self.layoutWidget)
        self.label_7.setObjectName(_fromUtf8("label_7"))
        self.gridLayout.addWidget(self.label_7, 2, 0, 1, 1)
        self.nameLineEdit = QtGui.QLineEdit(self.layoutWidget)
        self.nameLineEdit.setText(_fromUtf8(""))
        self.nameLineEdit.setObjectName(_fromUtf8("nameLineEdit"))
        self.gridLayout.addWidget(self.nameLineEdit, 2, 1, 1, 1)
        self.verticalLayout.addLayout(self.gridLayout)
        self.horizontalLayout = QtGui.QHBoxLayout()
        self.horizontalLayout.setObjectName(_fromUtf8("horizontalLayout"))
        spacerItem = QtGui.QSpacerItem(18, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem)
        self.okButton = QtGui.QPushButton(self.layoutWidget)
        self.okButton.setObjectName(_fromUtf8("okButton"))
        self.horizontalLayout.addWidget(self.okButton)
        self.verticalLayout.addLayout(self.horizontalLayout)

        self.retranslateUi(DbSettingsDialogBase)
        QtCore.QMetaObject.connectSlotsByName(DbSettingsDialogBase)

    def retranslateUi(self, DbSettingsDialogBase):
        DbSettingsDialogBase.setWindowTitle(_translate("DbSettingsDialogBase", "DbSettings", None))
        self.label_5.setText(_translate("DbSettingsDialogBase", "database", None))
        self.label_6.setText(_translate("DbSettingsDialogBase", "schema", None))
        self.label_7.setText(_translate("DbSettingsDialogBase", "table name", None))
        self.okButton.setText(_translate("DbSettingsDialogBase", "OK", None))

