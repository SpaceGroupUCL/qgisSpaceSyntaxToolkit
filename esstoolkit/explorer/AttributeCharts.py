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
# Import the PyQt and QGIS libraries, essential libraries
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from qgis.core import *

from math import atan

# try to import installed pyqtgraph, if not available use the one shipped with the esstoolkit
try:
    import pyqtgraph as pg
    has_pyqtgraph = True
except ImportError, e:
    try:
        from ..external import pyqtgraph as pg
        has_pyqtgraph = True
    except ImportError, e:
        has_pyqtgraph = False

import numpy as np
from operator import itemgetter

from .. import utility_functions as uf


class AttributeCharts(QObject):
    histogramSelected = pyqtSignal(int, int)
    scatterplotSelected = pyqtSignal(list)

    def __init__(self, iface, plot):
        QObject.__init__(self)

        self.iface = iface
        self.plot = plot

        if has_pyqtgraph:
            self.plot.setClipToView(True)
            self.hist_selection = pg.PlotCurveItem()
            self.scatter_selection = []
            self.scatter = pg.ScatterPlotItem()
            self.region = pg.LinearRegionItem()
            #self.roi = None

    #----
    # Histogram functions
    def drawHistogram(self, values, xmin, xmax, bins):
        # compute the histogram
        if bins >= 50:
            bin = 51
        else:
            bin = bins+1
        y, x = np.histogram(values, bins=np.linspace(xmin, xmax, num=bin))
        # plot the chart
        if has_pyqtgraph:
            curve = pg.PlotCurveItem()
            self.plot.clear()
            curve.setData(x, y, stepMode=True, fillLevel=0, brush=(230, 230, 230), pen=pg.mkPen(None))
            self.plot.addItem(curve)
            self.plot.setLimits(xMin=xmin, xMax=xmax, yMin=0, yMax=max(y))
            # add the selection tool
            self.region = pg.LinearRegionItem([xmax,xmax],bounds=[xmin, xmax])
            self.region.sigRegionChanged.connect(self.changedHistogramSelection)
            self.plot.addItem(self.region)

    # allow selection of items in chart and selecting them on the map
    def changedHistogramSelection(self):
        sel_min, sel_max = self.region.getRegion()
        self.histogramSelected.emit(sel_min, sel_max)

    def setHistogramSelection(self, values, xmin, xmax, bins):
        if has_pyqtgraph:
            if len(values) > 0:
                # compute the histogram
                if bins >= 50:
                    bin = 51
                else:
                    bin = bins+1
                y, x = np.histogram(values, bins=np.linspace(xmin, xmax, num=bin))
                # plot the selection chart
                self.hist_selection = pg.PlotCurveItem()
                self.hist_selection.setData(x, y, stepMode=True, fillLevel=0, brush=(230, 0, 0), pen=pg.mkPen(None))
                self.plot.addItem(self.hist_selection)
            elif self.hist_selection:
                self.plot.removeItem(self.hist_selection)

    #----
    # Scatterplot functions
    def drawScatterplot(self, xvalues, xmin, xmax, yvalues, ymin, ymax, slope, intercept, ids, symbols=None):
        # plot the chart
        if has_pyqtgraph:
            self.scatter = pg.ScatterPlotItem()
            self.plot.clear()
            # each point takes the colour of the map
            if symbols:
                points = []
                for i, id in enumerate(ids):
                    x = xvalues[i]
                    y = yvalues[i]
                    symb = symbols[i]
                    points.append({'x': x, 'y': y, 'data': id, 'size': 3, 'pen': pg.mkPen(None), 'brush': symb})
                self.scatter.addPoints(points)
            else:
                self.scatter.addPoints(x=xvalues, y=yvalues, data=ids, size=3, pen=pg.mkPen(None), brush=pg.mkBrush(235, 235, 235, 255))
            self.plot.addItem(self.scatter)
            self.plot.setLimits(xMin=xmin, xMax=xmax, yMin=ymin, yMax=ymax)
            # add the regression line
            regress_line = pg.InfiniteLine()
            regress_line.setAngle(atan(slope/1) * 180 / 3.1459)
            regress_line.setValue((0,intercept))
            regress_line.setPen(color='r', width=1)
            self.plot.addItem(regress_line)
            # newfeature: add the selection tool
            #self.scatter.sigClicked.connect(self.getScatterplotSelection)
            #self.roi = pg.PolyLineROI([[xmin, ymin],[xmax, ymin],[xmax, ymax],[xmin, ymax]], closed=True)
            #self.roi.sigRegionChangeFinished.connect(self.getRightPlotSelection)
            #self.plot.addItem(self.roi)
            #self.plot.disableAutoRange('xy')
            self.plot.autoRange()


    # newfeature: allow selection of items in chart and selecting them on the map
    def changedScatterplotSelection(self):
        ids = []
        self.scatterplotSelected.emit(ids)

    def setScatterplotSelection(self, ids):
        if has_pyqtgraph:
            if len(ids) > 0:
                for id in ids:
                    self.scatter.points()[id].setPen('r',width=3)
                    self.scatter_selection.append(self.scatter.points()[id])
            elif len(self.scatter_selection) > 0:
                for point in self.scatter_selection:
                    point.resetPen()
                self.scatter_selection = []
