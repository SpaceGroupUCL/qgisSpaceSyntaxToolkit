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
# Import the PyQt and QGIS libraries
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from qgis.core import *

# Import required modules
from ExplorerDialog import ExplorerDialog
from AttributeSymbology import *
from AttributeStats import *
from AttributeCharts import *
from .. import utility_functions as uf

import numpy as np

class ExplorerTool(QObject):

    def __init__(self, iface, settings, project):
        QObject.__init__(self)

        self.iface = iface
        self.settings = settings
        self.project = project
        self.legend = self.iface.legendInterface()

        # initialise UI
        self.dlg = ExplorerDialog(self.iface.mainWindow())

        # set up GUI signals
        self.dlg.layerChanged.connect(self.updateLayerAttributes)
        self.dlg.refreshLayers.connect(self.updateLayers)
        self.dlg.symbologyApplyButton.clicked.connect(self.applySymbology)
        self.dlg.attributesList.currentRowChanged.connect(self.updateSymbology)
        self.dlg.attributesList.currentRowChanged.connect(self.updateStats)
        self.dlg.attributesList.currentRowChanged.connect(self.updateCharts)
        self.dlg.chartChanged.connect(self.updateCharts)
        self.dlg.dependentChanged.connect(self.updateCharts)
        self.dlg.explorerTabs.currentChanged.connect(self.updateActionConnections)
        self.dlg.visibilityChanged.connect(self.onShow)

        # connect signal/slots with main program
        self.legend.itemAdded.connect(self.updateLayers)
        self.legend.itemRemoved.connect(self.updateLayers)
        self.iface.projectRead.connect(self.updateLayers)
        self.iface.newProjectCreated.connect(self.updateLayers)

        # initialise attribute explorer classes
        self.attributeSymbology = AttributeSymbology(self.iface)
        self.attributeCharts = AttributeCharts(self.iface, self.dlg.chartPlotWidget)

        # initialise internal globals
        self.current_layer = None
        self.current_renderer = None
        self.attribute_statistics = []
        self.bivariate_statistics = []
        self.attribute_values = []
        self.selection_values = []
        self.selection_ids = []
        self.updateActionConnections(0)
        self.layer_display_settings = []
        self.layer_attributes = []

    def unload(self):
        if self.dlg.isVisible():
            # Disconnect signals from main program
            self.legend.itemAdded.disconnect(self.updateLayers)
            self.legend.itemRemoved.disconnect(self.updateLayers)
            self.iface.projectRead.disconnect(self.updateLayers)
            self.iface.newProjectCreated.disconnect(self.updateLayers)
        # clear stored values
        self.attribute_statistics = []
        self.bivariate_statistics = []
        self.attribute_values = []
        self.selection_values = []

    def onShow(self):
        if self.dlg.isVisible():
            # Connect signals to QGIS interface
            self.legend.itemAdded.connect(self.updateLayers)
            self.legend.itemRemoved.connect(self.updateLayers)
            self.iface.projectRead.connect(self.updateLayers)
            self.iface.newProjectCreated.connect(self.updateLayers)
            self.updateLayers()
        else:
            # Disconnect signals to QGIS interface
            self.legend.itemAdded.disconnect(self.updateLayers)
            self.legend.itemRemoved.disconnect(self.updateLayers)
            self.iface.projectRead.disconnect(self.updateLayers)
            self.iface.newProjectCreated.disconnect(self.updateLayers)

    ##
    ## manage project and tool settings
    ##
    def getProjectSettings(self):
        # pull relevant settings from project manager
        for i, attr in enumerate(self.layer_attributes):
            settings = self.project.getGroupSettings("symbology/%s/%s" % (self.current_layer.name(), attr["name"]))
            if settings:
                #newfeature: allow custom symbology in the layer to be explored
                # feature almost in place, but all implications are not fully understood yet
                #if self.current_layer.rendererV2().usedAttributes() == attr["name"]:
                #    self.current_renderer = self.current_layer.rendererV2()
                #    self.layer_display_settings[i]["colour_range"] = 4
                #else:
                #    self.current_renderer = None
                self.layer_display_settings[i] = settings
        #self.project.readSettings(self.axial_analysis_settings,"stats")

    def updateProjectSettings(self, attr):
        # store last used setting with project
        symbology = self.layer_display_settings[attr]
        self.project.writeSettings(symbology,"symbology/%s/%s" % (self.current_layer.name(), symbology["attribute"]))
        #self.project.writeSettings(self.axial_analysis_settings,"stats")

    ##
    ## Manage layers and attributes
    ##
    def updateLayers(self):
        layers = uf.getLegendLayers(self.iface)
        has_numeric = []
        idx = 0
        if len(layers) > 0:
            for layer in layers:
                if layer.type() == 0:  # VectorLayer
                    fields = uf.getNumericFields(layer)
                    if len(fields) > 0:
                        has_numeric.append(layer.name())
                        if self.current_layer and layer.name() == self.current_layer.name():
                            idx = len(has_numeric)
        if len(has_numeric) == 0:
            has_numeric.append("Open a vector layer with numeric fields")
            self.dlg.lockLayerRefresh(True)
        else:
            has_numeric.insert(0,"Select layer to explore...")
            self.dlg.lockLayerRefresh(False)
        self.dlg.setCurrentLayer(has_numeric,idx)

    def updateLayerAttributes(self):
        no_layer = False
        self.update_attributtes = False
        # get selected layer
        layer = self.dlg.getCurrentLayer()
        if layer not in ("","Open a vector layer with numeric fields","Select layer to explore..."):
            if self.current_layer is None or self.current_layer.name() != layer:
                # fixme: throws NoneType error occasionally when adding/removing layers. trapping it for now.
                try:
                    self.current_layer = uf.getLegendLayerByName(self.iface, layer)
                except:
                    self.current_layer = None
            self.update_attributtes = True
        # get layer attributes
        if self.current_layer and self.update_attributtes:
            if not self.legend.isLayerVisible(self.current_layer):
                self.legend.setLayerVisible(self.current_layer, True)
            if self.current_layer.type() == 0:  #VectorLayer
                # fixme: throws NoneType error occasionally when adding/removing layers. trapping it for now.
                try:
                    numeric_fields, numeric_field_indices = uf.getNumericFieldNames(self.current_layer)
                    #numeric_fields = getValidFieldNames(self.current_layer,type=(QVariant.Int, QVariant.LongLong, QVariant.Double, QVariant.UInt, QVariant.ULongLong),null="all")
                except:
                    numeric_fields = []
                    numeric_field_indices = []
                if len(numeric_fields) > 0:
                    # set min and max values of attributes
                    # set this layer's default display attributes
                    self.layer_display_settings = []
                    self.layer_attributes = []
                    for i, index in enumerate(numeric_field_indices):
                        max_value = self.current_layer.maximumValue(index)
                        min_value = self.current_layer.minimumValue(index)
                        # exclude columns with only NULL values
                        if max_value != NULL and min_value != NULL:
                            # set the layer's attribute info
                            attribute_info = dict()
                            attribute_info['id']=index
                            attribute_info['name']=numeric_fields[i]
                            attribute_info['max'] = max_value
                            attribute_info['min'] = min_value
                            self.layer_attributes.append(attribute_info)
                            # set default display settings
                            attribute_display = dict(attribute="", colour_range=0, line_width=0.25, invert_colour=0, display_order=0,
                            intervals=10, interval_type=0, top_percent=100, top_value=0.0, bottom_percent=0, bottom_value=0.0)
                             # update the top and bottom value of the defaults
                            attribute_display['attribute'] = numeric_fields[i]
                            attribute_display['top_value'] = max_value
                            attribute_display['bottom_value'] = min_value
                            self.layer_display_settings.append(attribute_display)
                    # get the current display attribute
                    attributes = self.current_layer.rendererV2().usedAttributes()
                    if len(attributes) > 0:
                        display_attribute = attributes[0]
                        if display_attribute in numeric_fields:
                            current_attribute = numeric_fields.index(display_attribute)
                        else:
                            current_attribute = 0
                    else:
                        current_attribute = 0
                    # check for saved display settings for the given layer
                    self.getProjectSettings()
                    # update the dialog with this info
                    self.dlg.lockTabs(False)
                    self.dlg.setAttributesList(self.layer_attributes)
                    self.dlg.setAttributesSymbology(self.layer_display_settings)
                    self.dlg.setCurrentAttribute(current_attribute)
                    #self.updateSymbology()
                else:
                    no_layer = True
            else:
                no_layer = True
        else:
            no_layer = True
        if no_layer:
            self.current_layer = None #QgsVectorLayer()
            self.dlg.setAttributesList([])
            self.dlg.setAttributesSymbology([])
            self.dlg.setCurrentAttribute(-1)
            self.dlg.lockTabs(True)

    def updateActionConnections(self, tab):
        # change signal connections to trigger actions depending on selected tab
        # disconnect stats and charts
        if tab == 0:
            try:
                self.dlg.attributesList.currentRowChanged.disconnect(self.updateStats)
                self.iface.mapCanvas().selectionChanged.disconnect(self.updateStats)
            except: pass
            try:
                self.dlg.attributesList.currentRowChanged.disconnect(self.updateCharts)
                self.iface.mapCanvas().selectionChanged.disconnect(self.updateChartSelection)
            except: pass
        # do not disconnect symbology as it just retrieves info and updates the display: required
        # connect calculate stats
        elif tab == 1:
            try:
                self.dlg.attributesList.currentRowChanged.connect(self.updateStats)
                self.iface.mapCanvas().selectionChanged.connect(self.updateStats)
            except: pass
            try:
                self.dlg.attributesList.currentRowChanged.disconnect(self.updateCharts)
                self.iface.mapCanvas().selectionChanged.disconnect(self.updateChartSelection)
            except: pass
            self.updateStats()
        # connect calculate charts
        elif tab == 2:
            try:
                self.dlg.attributesList.currentRowChanged.disconnect(self.updateStats)
                self.iface.mapCanvas().selectionChanged.disconnect(self.updateStats)
            except: pass
            try:
                self.dlg.attributesList.currentRowChanged.connect(self.updateCharts)
                self.iface.mapCanvas().selectionChanged.connect(self.updateChartSelection)
            except: pass
            self.updateCharts()

    ##
    ## Symbology actions
    ##
    def applySymbology(self):
        """
        Update the current layer's display settings dictionary.
        Then update the layer display settings in the dialog.
        Finally, update the display using the new settings.
        """
        current_attribute = self.dlg.getCurrentAttribute()
        self.layer_display_settings[current_attribute] = self.dlg.getUpdatedDisplaySettings()
        self.updateProjectSettings(current_attribute)
        self.dlg.setAttributesSymbology(self.layer_display_settings)
        self.updateSymbology()

    def updateSymbology(self):
        if self.current_layer is not None:
            current_attribute = self.dlg.getCurrentAttribute()
            attribute = self.layer_attributes[current_attribute]
            # make this the tooltip attribute
            self.current_layer.setDisplayField(attribute['name'])
            if not self.iface.actionMapTips().isChecked():
                self.iface.actionMapTips().trigger()
            # get display settings
            settings = self.layer_display_settings[current_attribute]
            # produce new symbology renderer
            renderer = self.attributeSymbology.updateRenderer(self.current_layer, attribute, settings)
            # update the canvas
            if renderer:
                self.current_layer.setRendererV2(renderer)
                self.current_layer.triggerRepaint()
                self.iface.mapCanvas().refresh()
                self.legend.refreshLayerSymbology(self.current_layer)

    ##
    ## Stats actions
    ##
    def updateStats(self):
        if self.current_layer is not None:
            current_attribute = self.dlg.getCurrentAttribute()
            if current_attribute >= 0:
                attribute = self.layer_attributes[current_attribute]
                # check if stats have been calculated before
                idx = self.checkValuesAvailable(attribute)
                if idx == -1:
                    self.retrieveAttributeValues(attribute)
                    idx = len(self.attribute_statistics)-1
                stats = self.attribute_statistics[idx]
                # calculate stats of selected objects only
                select_stats = None
                if self.current_layer.selectedFeatureCount() > 0:
                    select_stats = dict()
                    self.selection_values, self.selection_ids = uf.getFieldValues(self.current_layer, attribute['name'], null=False, selection=True)
                    sel_values = np.array(self.selection_values)
                    select_stats['Mean'] = uf.truncateNumber(np.nanmean(sel_values))
                    select_stats['Std Dev'] = uf.truncateNumber(np.nanstd(sel_values))
                    select_stats['Median'] = uf.truncateNumber(np.median(sel_values))
                    select_stats['Minimum'] = np.nanmin(sel_values)
                    select_stats['Maximum'] = np.nanmax(sel_values)
                    select_stats['Range'] = uf.truncateNumber(select_stats['Maximum']-select_stats['Minimum'])
                    select_stats['1st Quart'] = uf.truncateNumber(np.percentile(sel_values,25))
                    select_stats['3rd Quart'] = uf.truncateNumber(np.percentile(sel_values,75))
                    select_stats['IQR'] = uf.truncateNumber(select_stats['3rd Quart']-select_stats['1st Quart'])
                    select_stats['Gini'] = uf.roundNumber(uf.calcGini(sel_values))
                else:
                    self.selection_values = []
                    self.selection_ids = []
                # update the dialog
                self.dlg.setStats(stats, select_stats)

    ##
    ## Charts actions
    ##
    def updateCharts(self):
        if self.current_layer is not None:
            current_attribute = self.dlg.getCurrentAttribute()
            if current_attribute >= 0:
                attribute = self.layer_attributes[current_attribute]
                # check if values are already available
                idx = self.checkValuesAvailable(attribute)
                # retrieve attribute values
                if idx == -1:
                    self.retrieveAttributeValues(attribute)
                    idx = len(self.attribute_values)-1
                values = self.attribute_values[idx]['values']
                ids = self.attribute_values[idx]['ids']
                bins = self.attribute_values[idx]['bins']
                # plot charts and dependent variable stats
                chart_type = self.dlg.getChartType()
                # create a histogram
                if chart_type == 0:
                    self.attributeCharts.drawHistogram(values, attribute['min'], attribute['max'], bins)
                elif chart_type == 1:
                    # create a scatter plot
                    current_dependent = self.dlg.getYAxisAttribute()
                    if current_dependent != current_attribute:
                        # prepare data for scatter plot
                        dependent = self.layer_attributes[current_dependent]
                        idx = self.checkValuesAvailable(dependent)
                        if idx == -1:
                            self.retrieveAttributeValues(dependent)
                            idx = len(self.attribute_values)-1
                        dep_values = self.attribute_values[idx]['values']
                        dep_ids = self.attribute_values[idx]['ids']
                        # check if it has already been calculated
                        idx = -1
                        for i, bistats in enumerate(self.bivariate_statistics):
                            if bistats['Layer'] == self.current_layer.name() and bistats['x'] == current_attribute and bistats['y'] == current_dependent:
                                idx = i
                                break
                        if idx == -1:
                            # get non NULL value pairs
                            xvalues = []
                            yvalues = []
                            xids = []
                            for (i, id) in enumerate(ids):
                                if id in set(dep_ids):
                                    xids.append(id)
                                    xvalues.append(values[i])
                                    yvalues.append(dep_values[dep_ids.index(id)])
                            # calculate bi-variate stats
                            bistats = dict()
                            bistats['Layer'] = self.current_layer.name()
                            bistats['xids'] = xids
                            bistats['x'] = current_attribute
                            bistats['xvalues'] = xvalues
                            bistats['y'] = current_dependent
                            bistats['yvalues'] = yvalues
                            bistats['r'] = uf.roundNumber(np.corrcoef(xvalues, yvalues)[1][0])
                            fit, residuals, rank, singular_values, rcond = np.polyfit(xvalues, yvalues, 1, None, True, None, False)
                            bistats['slope'] = fit[0]
                            bistats['intercept'] = fit[1]
                            bistats['r2'] = uf.roundNumber((1 - residuals[0] / (len(yvalues) * np.var(yvalues))))
                            # fixme: pvalue calc not correct
                            bistats['p'] = 0 #roundNumber(calcPvalue(values,yvalues))
                            if bistats['slope'] > 0:
                                bistats['line'] = "%s + %s * X" % (bistats['intercept'], bistats['slope'])
                            else:
                                bistats['line'] = "%s %s * X" % (bistats['intercept'], bistats['slope'])
                            self.bivariate_statistics.append(bistats)
                        else:
                            bistats = self.bivariate_statistics[idx]
                            xvalues = bistats['xvalues']
                            yvalues = bistats['yvalues']
                            xids = bistats['xids']
                        # update the dialog
                        self.dlg.setCorrelation(bistats)
                        # fixme: get symbols from features
                        #if len(ids) <= 100:
                        #    symbols = uf.getAllFeatureSymbols(self.current_layer)
                        #else:
                        symbols = None
                    else:
                        dependent = self.layer_attributes[current_attribute]
                        xvalues = values
                        yvalues = values
                        xids = ids
                        # calculate bi-variate stats
                        bistats = dict()
                        bistats['Layer'] = self.current_layer.name()
                        bistats['xids'] = xids
                        bistats['x'] = current_attribute
                        bistats['xvalues'] = []
                        bistats['y'] = current_attribute
                        bistats['yvalues'] = []
                        bistats['r'] = 1
                        bistats['slope'] = 1
                        bistats['intercept'] = attribute['min']
                        bistats['r2'] = 1
                        bistats['p'] = 0
                        bistats['line'] = "%s + 1 * X" % bistats['intercept']
                        # update the dialog
                        self.dlg.setCorrelation(bistats)
                        # fixme: get symbols from features
                        symbols = None
                    # plot chart
                    self.attributeCharts.drawScatterplot(xvalues, attribute['min'], attribute['max'], yvalues, dependent['min'], dependent['max'], bistats['slope'], bistats['intercept'], xids, symbols)
                # retrieve selection values
                if self.current_layer.selectedFeatureCount() > 0:
                    self.updateChartSelection()
            else:
                self.dlg.clearDependentValues()
        else:
            self.dlg.clearDependentValues()

    def updateChartSelection(self):
        if self.current_layer is not None:
            current_attribute = self.dlg.getCurrentAttribute()
            if current_attribute >= 0:
                chart_type = self.dlg.getChartType()
                if self.current_layer.selectedFeatureCount() > 0:
                    attribute = self.layer_attributes[current_attribute]
                    # retrieve selection values
                    self.selection_values, self.selection_ids = uf.getFieldValues(self.current_layer, attribute['name'], null=False, selection=True)
                    if chart_type == 0:
                        idx = self.checkValuesAvailable(attribute)
                        sel_values = np.array(self.selection_values)
                        bins = self.attribute_values[idx]['bins']
                        self.attributeCharts.setHistogramSelection(sel_values, np.min(sel_values), np.max(sel_values), bins)
                    if chart_type == 1:
                        self.attributeCharts.setScatterplotSelection(self.selection_ids)
                else:
                    self.selection_values = []
                    self.selection_ids = []
                    if chart_type == 0:
                        self.attributeCharts.setHistogramSelection([], 0, 0, 0)
                    if chart_type == 1:
                        self.attributeCharts.setScatterplotSelection([])

    def updateMapSelection(self):
        pass

    ##
    ## General functions
    ##
    def checkValuesAvailable(self, attribute):
        idx = -1
        for i, vals in enumerate(self.attribute_values):
            if vals['Layer'] == self.current_layer.name() and vals['Attribute'] == attribute['name']:
                idx = i
                break
        return idx

    def retrieveAttributeValues(self, attribute):
        storage = self.current_layer.storageType()
        if 'spatialite' in storage.lower():
            #todo: retrieve values and ids using SQL query
            values, ids = uf.getFieldValues(self.current_layer, attribute["name"], null=False)
        elif 'postgresql' in storage.lower():
            #todo: retrieve values and ids using SQL query
            values, ids = uf.getFieldValues(self.current_layer, attribute["name"], null=False)
        else:
            values, ids = uf.getFieldValues(self.current_layer, attribute["name"], null=False)
        if values and ids:
            #values = np.array(values)
            stats = dict()
            stats['Layer'] = self.current_layer.name()
            stats['Attribute'] = attribute['name']
            stats['Mean'] = uf.truncateNumber(np.nanmean(values))
            stats['Std Dev'] = uf.truncateNumber(np.nanstd(values))
            stats['Median'] = uf.truncateNumber(np.median(values))
            stats['Minimum'] = np.nanmin(values)
            stats['Maximum'] = np.nanmax(values)
            stats['Range'] = uf.truncateNumber(stats['Maximum']-stats['Minimum'])
            stats['1st Quart'] = uf.truncateNumber(np.percentile(values,25))
            stats['3rd Quart'] = uf.truncateNumber(np.percentile(values,75))
            stats['IQR'] = uf.truncateNumber(stats['3rd Quart']-stats['1st Quart'])
            stats['Gini'] = uf.roundNumber(uf.calcGini(values))
            # store the results
            self.attribute_statistics.append(stats)
            # store retrieved values for selection stats and charts
            attr = dict()
            attr['Layer'] = self.current_layer.name()
            attr['Attribute'] = attribute['name']
            attr['values'] = values
            attr['ids'] = ids
            attr['bins'] = uf.calcBins(values)
            self.attribute_values.append(attr)