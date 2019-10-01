# -*- coding: utf-8 -*-
"""
/***************************************************************************
 CatchmentAnalyser
                             Catchment Analyser
 Network based catchment analysis
                              -------------------
        begin                : 2016-05-19
        author               : Laurens Versluis
        copyright            : (C) 2016 by Space Syntax Limited
        email                : l.versluis@spacesyntax.com
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
from PyQt4.QtCore import *
from PyQt4.QtGui import *

# Import QGIS classes
from qgis.core import *
from qgis.gui import *
from qgis.utils import *

# Initialize Qt resources from file resources.py
#import resources

# Import the code for the dialog
from catchment_analyser_dialog import CatchmentAnalyserDialog
# import the main analysis module
import catchment_analysis as ca

# Import utility tools
import utility_functions as uf


class CatchmentTool(QObject):
    # initialise class with self and iface
    def __init__(self, iface):
        QObject.__init__(self)

        self.iface = iface

        self.dlg = CatchmentAnalyserDialog()
        self.analysis = None
        # Setup GUI signals
        self.dlg.networkCombo.activated.connect(self.updateCost)
        self.dlg.originsCombo.activated.connect(self.updateName)
        self.dlg.analysisButton.clicked.connect(self.runAnalysis)
        self.dlg.cancelButton.clicked.connect(self.killAnalysis)

    def load_gui(self):
        # Update layers
        self.updateLayers()
        # Show the dialog
        self.dlg.show()

    def unload_gui(self):
        try:
            self.dlg.networkCombo.activated.disconnect(self.updateCost)
            self.dlg.originsCombo.activated.disconnect(self.updateName)
            self.dlg.analysisButton.clicked.disconnect(self.runAnalysis)
            self.dlg.cancelButton.clicked.disconnect(self.killAnalysis)
        except:
            pass

    def updateLayers(self):
        self.updateNetwork()
        self.updateOrigins()

    def updateNetwork(self):
        network_layers = uf.getLegendLayersNames(self.iface, geom=[1, ], provider='all')
        self.dlg.setNetworkLayers(network_layers)
        if network_layers:
            self.updateCost()

    def updateOrigins(self):
        origins_layers = uf.getLegendLayersNames(self.iface, geom=[0, ], provider='all')
        self.dlg.setOriginLayers(origins_layers)
        if origins_layers:
            self.updateName()

    def updateCost(self):
        network = self.getNetwork()
        self.dlg.setCostFields(uf.getNumericFieldNames(network))

    def updateName(self):
        origins = self.getOrigins()
        self.dlg.setNameFields(uf.getFieldNames(origins))

    def getNetwork(self):
        return uf.getLegendLayerByName(self.iface, self.dlg.getNetwork())

    def getOrigins(self):
        return uf.getLegendLayerByName(self.iface, self.dlg.getOrigins())

    def tempNetwork(self, epsg):
        if self.dlg.networkCheck.isChecked():
            output_network = uf.createTempLayer(
                'catchment_network',
                'LINESTRING',
                epsg,
                ['id',],
                [QVariant.Int,]
            )
            return output_network


    def tempPolygon(self, epsg):
        if self.dlg.polygonCheck.isChecked():
            output_polygon = uf.createTempLayer(
                'catchment_areas',
                'MULTIPOLYGON',
                epsg,
                ['id', 'origin', 'distance'],
                [QVariant.Int, QVariant.Int, QVariant.Int]
            )
            return output_polygon

    def giveWarningMessage(self, message):
        # Gives warning according to message
        self.iface.messageBar().pushMessage(
            "Catchment Analyser: ",
            "%s" % (message),
            level=QgsMessageBar.WARNING,
            duration=5)

    def getAnalysisSettings(self):

        # Creating a combined settings dictionary
        settings = {}

        # Raise warnings
        if not self.getNetwork():
            self.giveWarningMessage("No network selected!")
        elif self.getNetwork().crs().geographicFlag() or self.getOrigins().crs().geographicFlag():
            self.giveWarningMessage("Input layer(s) without a projected CRS!")
        elif not self.getOrigins():
            self.giveWarningMessage("Catchment Analyser: No origins selected!")
        elif not self.dlg.getDistances():
            self.giveWarningMessage("No distances defined!")
        else:
            try:
                distances = [int(i) for i in self.dlg.getDistances()]
            except ValueError:
                self.giveWarningMessage("No numerical distances!")
                return

            # Get settings from the dialog
            settings['network'] = self.getNetwork()
            settings['cost'] = self.dlg.getCostField()
            settings['origins'] = self.getOrigins()
            settings['name'] = self.dlg.getName()
            settings['distances'] = distances
            settings['network tolerance'] = self.dlg.getNetworkTolerance()
            settings['polygon tolerance'] = int(self.dlg.getPolygonTolerance())
            settings['crs'] = self.getNetwork().crs()
            settings['epsg'] = self.getNetwork().crs().authid()[5:]  # removing EPSG:
            settings['temp network'] = self.tempNetwork(settings['epsg'])
            settings['temp polygon'] = self.tempPolygon(settings['epsg'])
            settings['output network check'] = self.dlg.networkCheck.isChecked()
            settings['output network'] = self.dlg.getNetworkOutput()
            settings['output polygon check'] = self.dlg.polygonCheck.isChecked()
            settings['output polygon'] = self.dlg.getPolygonOutput()

            return settings

    def runAnalysis(self):
        self.dlg.analysisProgress.reset()
        # Create an analysis instance
        settings = self.getAnalysisSettings()
        analysis = ca.CatchmentAnalysis(self.iface, settings)
        # Create new thread and move the analysis class to it
        analysis_thread = QThread()
        analysis.moveToThread(analysis_thread)
        # Setup signals

        analysis.finished.connect(self.analysisFinish)
        analysis.error.connect(self.analysisError)
        analysis.warning.connect(self.giveWarningMessage)
        analysis.progress.connect(self.dlg.analysisProgress.setValue)

        # Start analysis
        analysis_thread.started.connect(analysis.analysis)
        analysis_thread.start()
        self.analysis_thread = analysis_thread
        self.analysis = analysis

    def analysisFinish(self, output):
        # Render output
        if output:
            output_network = output['output network']
            output_polygon = output['output polygon']
            distances = output['distances']
            if output_network:
                self.renderNetwork(output_network, distances)
            if output_polygon:
                self.renderPolygon(output_polygon)
        else:
            self.giveWarningMessage('Something went wrong')
        # Clean up thread and analysis
        self.killAnalysis()

    def renderNetwork(self, output_network, distances):

        # Settings
        catchment_threshold = int(max(distances))

        # settings for 10 color ranges depending on the radius
        color_ranges = (
            (0, (0.1 * catchment_threshold), '#ff0000'),
            ((0.1 * catchment_threshold), (0.2 * catchment_threshold), '#ff5100'),
            ((0.2 * catchment_threshold), (0.3 * catchment_threshold), '#ff9900'),
            ((0.3 * catchment_threshold), (0.4 * catchment_threshold), '#ffc800'),
            ((0.4 * catchment_threshold), (0.5 * catchment_threshold), '#ffee00'),
            ((0.5 * catchment_threshold), (0.6 * catchment_threshold), '#a2ff00'),
            ((0.6 * catchment_threshold), (0.7 * catchment_threshold), '#00ff91'),
            ((0.7 * catchment_threshold), (0.8 * catchment_threshold), '#00f3ff'),
            ((0.8 * catchment_threshold), (0.9 * catchment_threshold), '#0099ff'),
            ((0.9 * catchment_threshold), (1 * catchment_threshold), '#0033ff'))

        # list with all color ranges
        ranges = []

        # for each range create a symbol with its respective color
        for lower, upper, color in color_ranges:
            symbol = QgsSymbolV2.defaultSymbol(output_network.geometryType())
            symbol.setColor(QColor(color))
            symbol.setWidth(0.5)
            range = QgsRendererRangeV2(lower, upper, symbol, '')
            ranges.append(range)

        # create renderer based on ranges and apply to network
        renderer = QgsGraduatedSymbolRendererV2('min_dist', ranges)
        output_network.setRendererV2(renderer)

        # add network to the canvas
        QgsMapLayerRegistry.instance().addMapLayer(output_network)

    def renderPolygon(self, output_polygon):

        # create a black dotted outline symbol layer
        symbol = QgsFillSymbolV2().createSimple({'color': 'grey', 'outline_width': '0'})
        symbol.setAlpha(0.2)

        # create renderer and change the symbol layer in its symbol
        output_polygon.rendererV2().setSymbol(symbol)

        # add catchment to the canvas
        QgsMapLayerRegistry.instance().addMapLayer(output_polygon)

    def analysisError(self, e, exception_string):
        QgsMessageLog.logMessage(
            'Catchment Analyser raised an exception: %s' % exception_string,
            level=QgsMessageLog.CRITICAL)

        # Closing the dialog
        self.dlg.closeDialog()

    def killAnalysis(self):
        # Check if the analysis is running
        if self.analysis:
            # Disconnect signals
            self.analysis.finished.disconnect(self.analysisFinish)
            self.analysis.error.disconnect(self.analysisError)
            self.analysis.warning.disconnect(self.giveWarningMessage)
            self.analysis.progress.disconnect(self.dlg.analysisProgress.setValue)
            # Clean up thread and analysis
            self.analysis.kill()
            self.analysis.deleteLater()
            self.analysis_thread.quit()
            self.analysis_thread.wait()
            self.analysis_thread.deleteLater()
            self.analysis = None
            # Closing the dialog
            self.dlg.closeDialog()
        else:
            self.dlg.closeDialog()
