# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'gate_transformer/network_transformer_dialog_base.ui'
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

class Ui_NetworkTransformerDialogBase(object):
    def setupUi(self, NetworkTransformerDialogBase):
        NetworkTransformerDialogBase.setObjectName(_fromUtf8("NetworkTransformerDialogBase"))
        NetworkTransformerDialogBase.setEnabled(True)
        NetworkTransformerDialogBase.resize(400, 250)
        NetworkTransformerDialogBase.setMinimumSize(QtCore.QSize(400, 250))
        self.gridLayout = QtGui.QGridLayout(NetworkTransformerDialogBase)
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
        self.resize_radio = QtGui.QRadioButton(NetworkTransformerDialogBase)
        self.resize_radio.setObjectName(_fromUtf8("resize_radio"))
        self.gridLayout.addWidget(self.resize_radio, 4, 0, 1, 1)
        self.rotate_radio = QtGui.QRadioButton(NetworkTransformerDialogBase)
        self.rotate_radio.setObjectName(_fromUtf8("rotate_radio"))
        self.gridLayout.addWidget(self.rotate_radio, 3, 0, 1, 1)
        self.run_button = QtGui.QPushButton(NetworkTransformerDialogBase)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Maximum, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.run_button.sizePolicy().hasHeightForWidth())
        self.run_button.setSizePolicy(sizePolicy)
        self.run_button.setObjectName(_fromUtf8("run_button"))
        self.gridLayout.addWidget(self.run_button, 6, 3, 1, 1)
        self.label = QtGui.QLabel(NetworkTransformerDialogBase)
        self.label.setObjectName(_fromUtf8("label"))
        self.gridLayout.addWidget(self.label, 0, 0, 1, 1)
        self.rescale_radio = QtGui.QRadioButton(NetworkTransformerDialogBase)
        self.rescale_radio.setObjectName(_fromUtf8("rescale_radio"))
        self.gridLayout.addWidget(self.rescale_radio, 5, 0, 1, 1)
        self.rotate_spinBox = QtGui.QSpinBox(NetworkTransformerDialogBase)
        self.rotate_spinBox.setMaximum(360)
        self.rotate_spinBox.setSingleStep(5)
        self.rotate_spinBox.setProperty("value", 90)
        self.rotate_spinBox.setObjectName(_fromUtf8("rotate_spinBox"))
        self.gridLayout.addWidget(self.rotate_spinBox, 3, 1, 1, 3)
        self.comboBox = QtGui.QComboBox(NetworkTransformerDialogBase)
        self.comboBox.setObjectName(_fromUtf8("comboBox"))
        self.gridLayout.addWidget(self.comboBox, 0, 1, 1, 3)
        self.resize_spinBox = QtGui.QSpinBox(NetworkTransformerDialogBase)
        self.resize_spinBox.setMaximum(1000000000)
        self.resize_spinBox.setSingleStep(5)
        self.resize_spinBox.setProperty("value", 25)
        self.resize_spinBox.setObjectName(_fromUtf8("resize_spinBox"))
        self.gridLayout.addWidget(self.resize_spinBox, 4, 1, 1, 3)
        self.rescale_spinBox = QtGui.QDoubleSpinBox(NetworkTransformerDialogBase)
        self.rescale_spinBox.setMaximum(1000000000.0)
        self.rescale_spinBox.setSingleStep(0.25)
        self.rescale_spinBox.setProperty("value", 2.0)
        self.rescale_spinBox.setObjectName(_fromUtf8("rescale_spinBox"))
        self.gridLayout.addWidget(self.rescale_spinBox, 5, 1, 1, 3)
        self.close_button = QtGui.QPushButton(NetworkTransformerDialogBase)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Maximum, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.close_button.sizePolicy().hasHeightForWidth())
        self.close_button.setSizePolicy(sizePolicy)
        self.close_button.setObjectName(_fromUtf8("close_button"))
        self.gridLayout.addWidget(self.close_button, 6, 2, 1, 1)

        self.retranslateUi(NetworkTransformerDialogBase)
        QtCore.QMetaObject.connectSlotsByName(NetworkTransformerDialogBase)

    def retranslateUi(self, NetworkTransformerDialogBase):
        NetworkTransformerDialogBase.setWindowTitle(_translate("NetworkTransformerDialogBase", "GateTransformer", None))
        self.resize_radio.setText(_translate("NetworkTransformerDialogBase", "Resize Line (metre)", None))
        self.rotate_radio.setText(_translate("NetworkTransformerDialogBase", "Rotate Line (degree)", None))
        self.run_button.setText(_translate("NetworkTransformerDialogBase", "Transform", None))
        self.label.setText(_translate("NetworkTransformerDialogBase", "Gates Layer:", None))
        self.rescale_radio.setText(_translate("NetworkTransformerDialogBase", "Rescale Line (multiple)", None))
        self.rotate_spinBox.setSuffix(_translate("NetworkTransformerDialogBase", "deg", None))
        self.resize_spinBox.setSuffix(_translate("NetworkTransformerDialogBase", "m", None))
        self.close_button.setText(_translate("NetworkTransformerDialogBase", "Close", None))

