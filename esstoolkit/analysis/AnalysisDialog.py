# -*- coding: utf-8 -*-
"""
/***************************************************************************
 essToolkit
                            Space Syntax Toolkit
 Set of tools for essential space syntax network analysis and results exploration
                              -------------------
        begin                : 2014-04-01
        copyright            : (C) 2015, UCL
        author               : Jorge Gil
        email                : jorge.gil@ucl.ac.uk
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""

from PyQt4 import QtCore, QtGui
from ui_Analysis import Ui_AnalysisDialog
from DepthmapAdvancedDialog import DepthmapAdvancedDialog
from VerificationSettingsDialog import VerificationSettingsDialog

from .. import utility_functions as uf


class AnalysisDialog(QtGui.QDockWidget, Ui_AnalysisDialog):
    dialogClosed = QtCore.pyqtSignal()
    updateDatastore = QtCore.pyqtSignal(str)

    def __init__(self, parent):

        QtGui.QDockWidget.__init__(self, parent)
        # Set up the user interface from Designer.
        self.setupUi(self)

        # define globals
        self.layers = [{'idx': 0, 'name': ''},{'idx': 0, 'name': ''},{'idx': 0, 'name': ''},{'idx': 0, 'name': ''}]
        self.axial_verify_report = [{'progress': 0, 'summary': [], 'filter': -1, 'report': dict(), 'nodes': []}
                                    , {'progress': 0, 'summary': [], 'filter': -1, 'report': dict(), 'nodes': []}]
        self.axial_verification_settings = {'ax_dist': 1.0, 'ax_min': 1.0, 'unlink_dist': 5.0, 'link_dist': 1.0}

        self.dlg_depthmap = DepthmapAdvancedDialog()
        self.dlg_verify = VerificationSettingsDialog(self.axial_verification_settings)

        # set up internal GUI signals
        self.analysisLayersTabs.currentChanged.connect(self.__selectLayerTab)
        self.analysisMapCombo.activated.connect(self.selectMapLayer)
        self.analysisUnlinksCombo.activated.connect(self.selectUnlinksLayer)
        self.axialVerifySettingsButton.clicked.connect(self.showAxialEditSettings)
        self.axialReportFilterCombo.activated.connect(self.selectAxialProblemsFilter)
        self.axialDepthmapWeightCheck.toggled.connect(self.setDepthmapWeighted)
        self.axialDepthmapAxialRadio.clicked.connect(self.setDepthmapAxialAnalysis)
        self.axialDepthmapSegmentRadio.clicked.connect(self.setDepthmapSegmentAnalysis)
        self.axialDepthmapSettingsButton.clicked.connect(self.showAxialDepthmapAdvancedSettings)
        self.axialDepthmapRadiusText.editingFinished.connect(self.checkDepthmapInputText)
        self.axialDepthmapOutputText.editingFinished.connect(self.checkDepthmapInputText)

        # initialise
        self.axial_analysis_type = 0
        self.__selectLayerTab(0)
        self.lockAxialEditTab(True)
        self.lockAxialDepthmapTab(True)
        self.setDatastore('', '')
        self.updateAxialVerifyReport()
        self.clearAxialDepthmapTab()


    #####
    # General functions of the analysis dialog
    def closeEvent(self, event):
        self.dialogClosed.emit()
        return QtGui.QDockWidget.closeEvent(self, event)

    def setDatastore(self, txt, path):
        self.analysisDataEdit.setText(txt)
        self.analysisDataEdit.setToolTip(path)

    def __selectLayerTab(self, tab):
        self.layers_tab = tab
        self.updateAnalysisTabs()

    def getLayerTab(self):
        return self.layers_tab

    def lockLayerTab(self, onoff):
        self.analysisLayersTabs.setDisabled(onoff)

    def setMapLayers(self, names, idx):
        layers = ['-----']
        if names:
            layers.extend(names)
        self.analysisMapCombo.clear()
        self.analysisMapCombo.addItems(layers)
        self.analysisMapCombo.setCurrentIndex(idx+1)
        self.layers[0]['idx'] = idx+1
        self.layers[0]['name'] = layers[idx+1]
        if idx == -1:
            self.clearAxialProblems()

    def selectMapLayer(self):
        self.layers[0]['idx'] = self.analysisMapCombo.currentIndex()
        self.layers[0]['name'] = self.analysisMapCombo.currentText()
        # update the UI
        self.clearAxialProblems()
        self.updateAnalysisTabs()
        self.updateAxialDepthmapTab()

    def setUnlinksLayers(self, names, idx):
        layers = ['-----']
        if names:
            layers.extend(names)
        self.analysisUnlinksCombo.clear()
        self.analysisUnlinksCombo.addItems(layers)
        self.analysisUnlinksCombo.setCurrentIndex(idx+1)
        self.layers[1]['idx'] = idx+1
        self.layers[1]['name'] = layers[idx+1]
        if idx == -1:
            self.clearAxialProblems(1)

    def selectUnlinksLayer(self):
        self.layers[1]['name'] = self.analysisUnlinksCombo.currentText()
        self.layers[1]['idx'] = self.analysisUnlinksCombo.currentIndex()
        # update the UI
        self.clearAxialProblems(1)
        self.updateAnalysisTabs()


    def getAnalysisLayers(self):
        layers = {'map':'','unlinks':''}
        for i, layer in enumerate(self.layers):
            name = layer['name']
            if name != '-----':
                if i == 0:
                    layers['map'] = name
                elif i == 1:
                    layers['unlinks'] = name
        return layers

    def updateAnalysisTabs(self):
        index = self.layers[self.layers_tab]['idx']
        # must have a map layer to verify unlinks, links and origins
        axindex = self.layers[0]['idx']
        if axindex < 1:
            self.axialDepthmapTab.setDisabled(True)
        if index < 1 or axindex < 1:
            self.axialEditTab.setDisabled(True)
            self.clearAxialProblems()
            self.clearAxialVerifyReport()
        else:
            self.axialDepthmapTab.setDisabled(False)
            self.axialEditTab.setDisabled(False)
            self.lockAxialEditTab(False)
            self.updateAxialVerifyReport()
            # if the data store field is empty, use the same as the selected map layer
            if self.analysisDataEdit.text() in ("", "specify for storing analysis results"):
                self.updateDatastore.emit(self.layers[0]['name'])
        #self.updateAxialDepthmapTab()

    #####
    # Functions of the edit layer tab
    #####
    def lockAxialEditTab(self, onoff):
        self.axialVerifyButton.setDisabled(onoff)
        if self.layers_tab > 0:
            self.axialUpdateButton.setDisabled(onoff)
        else:
            self.axialUpdateButton.setDisabled(True)
        self.axialVerifyCancelButton.setDisabled(not onoff)
        self.axialVerifySettingsButton.setDisabled(onoff)

    def updateAxialVerifyReport(self):
        d = self.axial_verify_report[self.layers_tab]
        self.axialVerifyProgressBar.setValue(d['progress'])
        self.setAxialProblems(d['report'], d['nodes'])
        self.setAxialProblemsFilter(d['summary'], d['filter'])
        if len(d['nodes']) > 0:
            self.axialReportFilterCombo.setDisabled(False)
            self.axialReportList.setDisabled(False)
        else:
            self.axialReportFilterCombo.setDisabled(True)
            self.axialReportList.setDisabled(True)
            self.clearAxialVerifyReport()

    def clearAxialVerifyReport(self):
        self.axialVerifyProgressBar.setValue(0)
        self.axialReportFilterCombo.clear()
        self.axialReportList.clear()
        self.axialReportList.horizontalHeader().hide()
        self.axialReportList.setColumnCount(0)
        self.axialReportList.setRowCount(0)
        self.axialReportFilterCombo.setDisabled(True)
        self.axialReportList.setDisabled(True)

    def setAxialVerifyTooltip(self, txt):
        self.axialVerifyButton.setToolTip(txt)

    def updateAxialVerifyProgressbar(self, value):
        self.axialVerifyProgressBar.setValue(value)
        self.axial_verify_report[self.layers_tab]['progress'] = value

    def setAxialVerifyProgressbar(self, value, maximum=100):
        self.axialVerifyProgressBar.setValue(value)
        self.axialVerifyProgressBar.setRange(0, maximum)

    def setAxialProblemsFilter(self, problems, idx=0):
        self.axialReportFilterCombo.clear()
        self.axial_verify_report[self.layers_tab]['summary'] = problems
        self.axialReportFilterCombo.addItems(problems)
        self.axial_verify_report[self.layers_tab]['filter'] = idx
        self.axialReportFilterCombo.setCurrentIndex(idx)
        self.selectAxialProblemsFilter()

    def selectAxialProblemsFilter(self):
        self.axial_verify_report[self.layers_tab]['filter'] = self.axialReportFilterCombo.currentIndex()
        if self.layers_tab == 0:
            self.filterAxialProblems()
        elif self.layers_tab == 1:
            self.filterUnlinkProblems()

    def getAxialProblemsFilter(self):
        txt = self.axialReportFilterCombo.currentText()
        return txt.split('(')[0].lower().rstrip()

    def setAxialProblems(self, report, nodes):
        self.axial_verify_report[self.layers_tab]['report'] = report
        self.axial_verify_report[self.layers_tab]['nodes'] = nodes
        if len(nodes) > 0:
            self.axialReportFilterCombo.setDisabled(False)
            self.axialReportList.setDisabled(False)
        else:
            self.axialReportFilterCombo.setDisabled(True)
            self.axialReportList.setDisabled(True)

    def clearAxialProblems(self, tab=None):
        if tab:
            self.axial_verify_report[tab]['progress'] = 0
            self.axial_verify_report[tab]['summary'] = []
            self.axial_verify_report[tab]['filter'] = -1
            self.axial_verify_report[tab]['report'] = dict()
            self.axial_verify_report[tab]['nodes'] = []
        else:
            self.axial_verify_report[self.layers_tab]['progress'] = 0
            self.axial_verify_report[self.layers_tab]['summary'] = []
            self.axial_verify_report[self.layers_tab]['filter'] = -1
            self.axial_verify_report[self.layers_tab]['report'] = dict()
            self.axial_verify_report[self.layers_tab]['nodes'] = []

    def filterAxialProblems(self):
        # extract filter text
        select = self.getAxialProblemsFilter()
        report = self.axial_verify_report[self.layers_tab]['report']
        nodes_list = self.axial_verify_report[self.layers_tab]['nodes']
        self.axialReportList.clear()
        self.axialReportList.setRowCount(0)
        # build list of individual problems
        problems = []
        if select:
            if select == "all problems":
                for problem in nodes_list:
                    errors = []
                    for k, v in report.iteritems():
                        if len(v) > 0:
                            if type(v[0]) is list:
                                for i in v:
                                    if problem in i:
                                        errors.append(k)
                            else:
                                if problem in v:
                                    errors.append(k)
                    problems.append((problem, ', '.join(errors)))
            elif select == "island":
                for i, v in enumerate(report[select]):
                    ids = [str(fid) for fid in v]
                    problems.append((i, ','.join(ids)))
            elif select == "no problems found!":
                return
            else:
                for v in report[select]:
                    problems.append((v,select))
            # update the interface
            self.axialReportList.setColumnCount(2)
            self.axialReportList.setHorizontalHeaderLabels(["ID", "Problem"])
            self.axialReportList.horizontalHeader().setResizeMode(0, QtGui.QHeaderView.ResizeToContents)
            self.axialReportList.horizontalHeader().setResizeMode(1, QtGui.QHeaderView.Stretch)
            self.axialReportList.setRowCount(len(problems))
            for i, rec in enumerate(problems):
                item = QtGui.QTableWidgetItem(str(rec[0]))
                self.axialReportList.setItem(i, 0, item)
                item = QtGui.QTableWidgetItem(rec[1])
                self.axialReportList.setItem(i, 1, item)
            self.axialReportList.horizontalHeader().show()
            self.axialReportList.resizeRowsToContents()

    def filterUnlinkProblems(self):
        # extract filter text
        select = self.getAxialProblemsFilter()
        report = self.axial_verify_report[self.layers_tab]['report']
        nodes_list = self.axial_verify_report[self.layers_tab]['nodes']
        self.axialReportList.clear()
        self.axialReportList.setRowCount(0)
        # build list of individual problems
        problems = []
        if select:
            if select == "all problems":
                for fid in nodes_list:
                    errors = []
                    for k, v in report.iteritems():
                        if fid[0] in v:
                            errors.append(k)
                    problems.append((fid[0], fid[1], fid[2], ', '.join(errors)))
            elif select == "no problems found!":
                return
            else:
                for fid in nodes_list:
                    if fid[0] in report[select]:
                        problems.append((fid[0], fid[1], fid[2], select))
            # update the interface
            self.axialReportList.setColumnCount(4)
            self.axialReportList.setHorizontalHeaderLabels(["ID", "Line1", "Line2", "Problem"])
            self.axialReportList.setRowCount(len(problems))
            for i, rec in enumerate(problems):
                item = QtGui.QTableWidgetItem(str(rec[0]))
                self.axialReportList.setItem(i, 0, item)
                item = QtGui.QTableWidgetItem(str(rec[1]))
                self.axialReportList.setItem(i, 1, item)
                item = QtGui.QTableWidgetItem(str(rec[2]))
                self.axialReportList.setItem(i, 2, item)
                item = QtGui.QTableWidgetItem(rec[3])
                self.axialReportList.setItem(i, 3, item)
            self.axialReportList.horizontalHeader().setResizeMode(0, QtGui.QHeaderView.ResizeToContents)
            self.axialReportList.horizontalHeader().setResizeMode(1, QtGui.QHeaderView.ResizeToContents)
            self.axialReportList.horizontalHeader().setResizeMode(2, QtGui.QHeaderView.ResizeToContents)
            self.axialReportList.horizontalHeader().setResizeMode(3, QtGui.QHeaderView.Stretch)
            self.axialReportList.horizontalHeader().show()
            self.axialReportList.resizeRowsToContents()

    def getAxialVerifyProblems(self):
        ids = []
        rows = [item.row() for item in self.axialReportList.selectedItems()]
        #if not rows:
        #    rows = [item.row() for item in self.axialReportList.selectedItems()]
        rows = sorted(set(rows))
        if self.getAxialProblemsFilter() == "island":
            for i in rows:
                ids.extend(self.axialReportList.item(i, 1).text().split(','))
        else:
            for i in rows:
                ids.append(self.axialReportList.item(i, 0).text())
        return ids

    def getAxialEditSettings(self):
        return self.axial_verification_settings

    def showAxialEditSettings(self):
        self.dlg_verify.show()

    #####
    # Functions of the depthmapX remote tab
    #####
    def setAxialDepthmapTab(self, settings):
        if settings is not None:
            # set the type of analysis
            if 'type' in settings:
                self.axial_analysis_type = settings['type']
                if settings['type'] == 0:
                    self.axialDepthmapAxialRadio.setChecked(True)
                elif settings['type'] == 1:
                    self.axialDepthmapSegmentRadio.setChecked(True)
            # if project specifies radii set them, for same type of analysis
            if 'rvalues' in settings:
                self.setDepthmapRadiusText(settings['rvalues'])
            else:
                self.setDepthmapRadiusText("n")
            # project use of weights
            if 'weight' in settings:
                self.axialDepthmapWeightCheck.setChecked(settings['weight'])
                #self.setDepthmapWeighted(settings['weight'])
            else:
                self.axialDepthmapWeightCheck.setChecked(False)
                #self.setDepthmapWeighted(0)
            # project output name
            if 'output' in settings:
                self.setAxialDepthmapOutputTable(settings['output'])
            # project calculate full set of advanced measures
            if 'fullset' in settings:
                self.dlg_depthmap.setCalculateFull(settings['fullset'])
            else:
                self.dlg_depthmap.setCalculateFull(False)
            # project calculate betweenness
            if 'betweenness' in settings:
                self.dlg_depthmap.setCalculateChoice(settings['betweenness'])
            else:
                self.dlg_depthmap.setCalculateChoice(True)
            # project list of radii
            if 'radius' in settings:
                self.dlg_depthmap.setRadiusType(settings['radius'])
            else:
                self.dlg_depthmap.setRadiusType(2)
            # project calculate new normalised segment measures
            if 'newnorm' in settings:
                self.dlg_depthmap.setCalculateNorm(settings['newnorm'])
            else:
                self.dlg_depthmap.setCalculateNorm(True)
            # project remove stubs setting for segment map creation
            if 'stubs' in settings:
                self.dlg_depthmap.setRemoveStubs(settings['stubs'])
            else:
                self.dlg_depthmap.setRemoveStubs(40)

    def updateAxialDepthmapTab(self):
        if self.layers[0]['idx'] > 0:
            self.lockAxialDepthmapTab(False)
            # update weights combo box and output name
            layer = uf.getLayerByName(self.layers[0]['name'])
            txt, idxs = uf.getNumericFieldNames(layer)
            if self.axial_analysis_type == 0:
                self.setAxialDepthmapOutputTable(self.layers[0]['name'])
                txt.insert(0, "Line Length")
            elif self.axial_analysis_type == 1:
                self.setAxialDepthmapOutputTable(self.layers[0]['name']+'_segment')
                txt.insert(0, "Segment Length")
            self.setDepthmapWeightAttributes(txt)
            self.updateAxialDepthmapAdvancedSettings()
        else:
            self.lockAxialDepthmapTab(True)
            #self.setDepthmapWeightAttributes([])
            #self.setAxialDepthmapOutputTable('')
            #self.clearAxialDepthmapTab()

    def lockAxialDepthmapTab(self, onoff):
        self.axialDepthmapAxialRadio.setDisabled(onoff)
        self.axialDepthmapSegmentRadio.setDisabled(onoff)
        self.axialDepthmapRadiusText.setDisabled(onoff)
        self.axialDepthmapOutputText.setDisabled(onoff)
        self.axialDepthmapCalculateButton.setDisabled(onoff)
        self.axialDepthmapSettingsButton.setDisabled(onoff)
        self.axialDepthmapCancelButton.setDisabled(not onoff)
        self.axialDepthmapWeightCheck.setDisabled(onoff)
        if onoff:
            self.axialDepthmapWeightCheck.setDisabled(onoff)
        else:
            self.setDepthmapWeighted(self.getDepthmapWeighted())

    def clearAxialDepthmapTab(self):
        self.axialDepthmapAxialRadio.setChecked(True)
        self.setDepthmapRadiusText('n')
        self.axialDepthmapWeightCheck.setChecked(False)
        self.axialDepthmapOutputText.clear()
        self.axialDepthmapProgressBar.setValue(0)
        self.axialDepthmapReportList.clear()

    def setDepthmapAxialAnalysis(self):
        self.axial_analysis_type = 0
        self.setDepthmapRadiusText('n')
        self.updateAxialDepthmapTab()

    def setDepthmapSegmentAnalysis(self):
        self.axial_analysis_type = 1
        self.setDepthmapRadiusText('n')
        self.updateAxialDepthmapTab()

    def getDepthmapAnalysisType(self):
        return self.axial_analysis_type

    def setDepthmapRadiusText(self, txt):
        self.axialDepthmapRadiusText.setText(txt)

    def checkDepthmapInputText(self):
        if self.axialDepthmapRadiusText.text() != '' and self.axialDepthmapOutputText.text() != '':
            self.axialDepthmapCalculateButton.setDisabled(False)
            self.setAxialDepthmapCalculateTooltip('')
        else:
            self.axialDepthmapCalculateButton.setDisabled(True)
            self.setAxialDepthmapCalculateTooltip('Check if the radius values and output table name are correct.')

    def getDepthmapRadiusText(self):
        return self.axialDepthmapRadiusText.text()

    def setDepthmapWeighted(self, state):
        if state == 1:
            self.axialDepthmapWeightCombo.setDisabled(False)
        else:
            self.axialDepthmapWeightCombo.setDisabled(True)

    def setDepthmapWeightAttributes(self, txt):
        self.axialDepthmapWeightCombo.clear()
        self.axialDepthmapWeightCombo.addItems(txt)
        self.axialDepthmapWeightCombo.setCurrentIndex(0)

    def getDepthmapWeighted(self):
        if self.axialDepthmapWeightCheck.isChecked():
            return 1
        else:
            return 0

    def getDepthmapWeightAttribute(self):
        return self.axialDepthmapWeightCombo.currentText()

    def setAxialDepthmapOutputTable(self, txt):
        self.axialDepthmapOutputText.setText(txt)

    def getAxialDepthmapOutputTable(self):
        return self.axialDepthmapOutputText.text()

    def updateAxialDepthmapAdvancedSettings(self):
        # these settings are only available in segment analysis
        if self.axial_analysis_type == 1:  # segment analysis
            self.dlg_depthmap.setDistanceType(1)
            self.dlg_depthmap.axialDistanceCombo.setDisabled(True)
            self.dlg_depthmap.setRadiusType(2)
            self.dlg_depthmap.axialRadiusLabel.setDisabled(False)
            self.dlg_depthmap.axialRadiusCombo.setDisabled(False)
            #self.dlg_depthmap.setCalculateNorm(True)
            self.dlg_depthmap.axialCalculateNormCheck.setDisabled(False)
            self.dlg_depthmap.axialStubsLabel.setDisabled(False)
            self.dlg_depthmap.axialStubsEdit.setDisabled(False)
        elif self.axial_analysis_type == 0:  # and axial analysis alternative
            self.dlg_depthmap.setDistanceType(0)
            self.dlg_depthmap.axialDistanceCombo.setDisabled(True)
            self.dlg_depthmap.setRadiusType(0)
            self.dlg_depthmap.axialRadiusLabel.setDisabled(True)
            self.dlg_depthmap.axialRadiusCombo.setDisabled(True)
            self.dlg_depthmap.axialCalculateNormCheck.setDisabled(True)
            self.dlg_depthmap.axialStubsLabel.setDisabled(True)
            self.dlg_depthmap.axialStubsEdit.setDisabled(True)

    def showAxialDepthmapAdvancedSettings(self):
        self.dlg_depthmap.show()

    def getAxialDepthmapDistanceType(self):
        return self.dlg_depthmap.axialDistanceCombo.currentIndex()

    def getAxialDepthmapRadiusType(self):
        return self.dlg_depthmap.axialRadiusCombo.currentIndex()

    def getAxialDepthmapFullset(self):
        if self.dlg_depthmap.axialCalculateFullCheck.isChecked():
            return 1
        else:
            return 0

    def getAxialDepthmapChoice(self):
        if self.dlg_depthmap.axialCalculateChoiceCheck.isChecked():
            return 1
        else:
            return 0

    def getAxialDepthmapNormalised(self):
        if self.dlg_depthmap.axialCalculateNormCheck.isChecked():
            return 1
        else:
            return 0

    def getAxialDepthmapStubs(self):
        return self.dlg_depthmap.axialStubsEdit.text()

    def setAxialDepthmapCalculateTooltip(self, txt):
        self.axialDepthmapCalculateButton.setToolTip(txt)

    def setAxialDepthmapProgressbar(self, value, maximum=100):
        self.axialDepthmapProgressBar.setMaximum(maximum)
        self.axialDepthmapProgressBar.setValue(value)

    def updateAxialDepthmapProgressbar(self, value):
        self.axialDepthmapProgressBar.setValue(value)

    def writeAxialDepthmapReport(self, txt):
        self.axialDepthmapReportList.appendPlainText(txt)

    def clearAxialDepthmapReport(self):
        self.axialDepthmapReportList.clear()

    #newfeature: set different toolboxes for convex, isovist, VGA, agents