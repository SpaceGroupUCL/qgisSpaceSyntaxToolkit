# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ui_About.ui'
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

class Ui_AboutDialog(object):
    def setupUi(self, AboutDialog):
        AboutDialog.setObjectName(_fromUtf8("AboutDialog"))
        AboutDialog.setWindowModality(QtCore.Qt.ApplicationModal)
        AboutDialog.resize(370, 400)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(AboutDialog.sizePolicy().hasHeightForWidth())
        AboutDialog.setSizePolicy(sizePolicy)
        AboutDialog.setMinimumSize(QtCore.QSize(370, 400))
        self.verticalLayout = QtGui.QVBoxLayout(AboutDialog)
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.messageText = QtGui.QTextEdit(AboutDialog)
        self.messageText.setEnabled(True)
        self.messageText.setAutoFillBackground(False)
        self.messageText.setFrameShape(QtGui.QFrame.NoFrame)
        self.messageText.setFrameShadow(QtGui.QFrame.Plain)
        self.messageText.setLineWidth(0)
        self.messageText.setUndoRedoEnabled(False)
        self.messageText.setReadOnly(True)
        self.messageText.setObjectName(_fromUtf8("messageText"))
        self.verticalLayout.addWidget(self.messageText)
        self.logoLabel = QtGui.QLabel(AboutDialog)
        self.logoLabel.setAutoFillBackground(True)
        self.logoLabel.setText(_fromUtf8(""))
        self.logoLabel.setObjectName(_fromUtf8("logoLabel"))
        self.verticalLayout.addWidget(self.logoLabel)
        self.closeButton = QtGui.QPushButton(AboutDialog)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.closeButton.sizePolicy().hasHeightForWidth())
        self.closeButton.setSizePolicy(sizePolicy)
        self.closeButton.setObjectName(_fromUtf8("closeButton"))
        self.verticalLayout.addWidget(self.closeButton)

        self.retranslateUi(AboutDialog)
        QtCore.QMetaObject.connectSlotsByName(AboutDialog)

    def retranslateUi(self, AboutDialog):
        AboutDialog.setWindowTitle(_translate("AboutDialog", "About the Space Syntax Toolkit", None))
        self.messageText.setHtml(_translate("AboutDialog", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'.Helvetica Neue DeskInterface\'; font-size:13pt; font-weight:400; font-style:normal;\">\n"
"<p align=\"justify\" style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-family:\'Lucida Grande\';\">The &quot;Space Syntax Toolkit&quot; has been developed at the Space Syntax Laboratory, the Bartlett School of Architecture,  University College London (UCL).</span></p>\n"
"<p align=\"justify\" style=\"-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-family:\'Lucida Grande\';\"><br /></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-family:\'Lucida Grande\';\">Author: Jorge Gil</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-family:\'Lucida Grande\';\">Contact: jorge.gil at ucl.ac.uk</span></p>\n"
"<p style=\"-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-family:\'Lucida Grande\';\"><br /></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-family:\'Lucida Grande\';\">(C) 2015, UCL</span></p></body></html>", None))
        self.closeButton.setText(_translate("AboutDialog", "Close", None))

import resources_rc
