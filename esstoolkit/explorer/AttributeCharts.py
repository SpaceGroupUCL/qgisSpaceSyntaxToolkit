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
            self.scatter = pg.ScatterPlotItem()
            self.region = pg.LinearRegionItem()
            #self.roi = None
        # newfeature: support simple charts without pyqtgraph
        else:
            pass

    def drawHistogram(self, values, min, max, bins):
        # compute the histogram
        if bins >= 50:
            bin = 51
        else:
            bin = bins+1
        y, x = np.histogram(values, bins=np.linspace(min, max, num=bin))
        # plot the chart
        if has_pyqtgraph:
            curve = pg.PlotCurveItem()
            self.plot.clear()
            curve.setData(x, y, stepMode=True, fillLevel=0, brush=(230, 230, 230), pen=pg.mkPen(None))
            self.plot.addItem(curve)
            # newfeature: add the selection tool
            #self.region = pg.LinearRegionItem([min,min],bounds=[min, max])
            #self.region.sigRegionChanged.connect(self.getHistogramSelection)
            #self.plot.addItem(self.region)
        # newfeature: support simple charts without pyqtgraph
        else:
            pass

    # newfeature: allow selection of items in chart and selecting them on the map
    def changedHistogramSelection(self):
        sel_min, sel_max = self.region.getRegion()
        self.histogramSelected.emit(sel_min, sel_max)

    def setHistogramSelection(self, values, min, max, bins):
        # compute the histogram
        if bins >= 50:
            bin = 51
        else:
            bin = bins+1
        y, x = np.histogram(values, bins=np.linspace(min, max, num=bin))
        # plot the chart
        if has_pyqtgraph:
            sel_curve = pg.PlotCurveItem()
            sel_curve.setData(x, y, stepMode=True, fillLevel=0, brush=(230, 0, 0), pen=pg.mkPen(None))
            self.plot.addItem(sel_curve)
        # newfeature: support simple charts without pyqtgraph
        else:
            pass

    def drawBoxPlot(self, values):
        pass

    def drawScatterplot(self, xvalues, yvalues, ids, symbols=None):
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
                    points.append({'x':x,'y':y,'data':id,'size':3,'pen':pg.mkPen(None), 'brush':symb})
                self.scatter.addPoints(points)
            else:
                self.scatter.addPoints(x=xvalues,y=yvalues,data=ids,size=3,pen=pg.mkPen(None), brush=pg.mkBrush(235, 235, 235, 255))
            self.plot.addItem(self.scatter)
            # newfeature: add the selection tool
            #self.scatter.sigClicked.connect(self.getScatterplotSelection)
            #minX = min(values)
            #maxX = max(values)
            #minY = min(yvalues)
            #maxY = max(yvalues)
            #self.roi = pg.PolyLineROI([[minX,minY],[maxX,minY],[maxX,maxY],[minX,maxY]], closed=True)
            #self.roi.sigRegionChangeFinished.connect(self.getRightPlotSelection)
            #self.plot.addItem(self.roi)
            #self.plot.disableAutoRange('xy')
            #self.plot.autoRange()

        # newfeature: support simple charts without pyqtgraph
        else:
            pass


    # newfeature: allow selection of items in chart and selecting them on the map
    def changedScatterplotSelection(self):
        ids = []
        self.scatterplotSelected.emit(ids)

    def setScatterplotSelection(self, ids):
        points = []
        #if has_pyqtgraph:
            #for id in ids:
                #self.scatter.points()[id].setPen('r',width=2)
            #    points.append(self.scatter.points()[id])
            #for point in points:
            #    point.setPen('r',width=2)