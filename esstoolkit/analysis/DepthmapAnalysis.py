# -*- coding: utf-8 -*-
"""
/***************************************************************************
 essTools
                                 A QGIS plugin
 Set of tools for space syntax network analysis and results exploration
                              -------------------
        begin                : 2014-04-01
        copyright            : (C) 2014 by Jorge Gil, UCL
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

import math

from ..utility_functions import *

class DepthmapAnalysis(QObject):

    def __init__(self, iface):
        QObject.__init__(self)

        self.iface = iface

        #initialise global variables
        self.axial_layer = None
        self.unlinks_layer = None
        self.links_layer = None
        self.origins_layer = None
        self.datastore = None
        self.settings = None
        self.axial_default = ('Connectivity','Line Length','Id')
        self.segment_default = ('Angular Connectivity','Axial Connectivity','Axial Id',
                                'Axial Line Length','Axial Line Ref','Connectivity','Segment Length')
        self.user_id = ''

    def showMessage(self, msg, type='Info', lev=1, dur=2):
        self.iface.messageBar().pushMessage(type,msg,level=lev,duration=dur)

    def setupAnalysis(self, layers, settings):
        self.settings = settings
        # get relevant QGIS layer objects
        axial = layers['map']
        if axial != '':
            self.axial_layer = getLegendLayerByName(self.iface, axial)
        else:
            return None
        if layers['unlinks'] != '':
            self.unlinks_layer = getLegendLayerByName(self.iface, layers['unlinks'])
        else:
            self.unlinks_layer = ''
        if layers['links'] != '':
            self.links_layer = getLegendLayerByName(self.iface, layers['links'])
        else:
            self.links_layer = ''
        if layers['origins'] != '':
            self.origins_layer = getLegendLayerByName(self.iface, layers['origins'])
        else:
            self.origins_layer = ''
        #
        # prepare analysis layers
        if self.settings['weight']:
            weight_by = self.settings['weightBy']
        else:
            weight_by = ''
        # look for user defined ID
        self.user_id = getIdField(self.axial_layer)
        axial_data = self.prepareAxialMap(self.user_id, weight_by)
        if self.unlinks_layer:
            unlinks_data = self.prepareUnlinks()
        else:
            unlinks_data = ''
        if self.links_layer:
            links_data = self.prepareLinks()
        else:
            links_data = ''
        if self.origins_layer:
            origins_data = self.prepareOrigins()
        else:
            origins_data = ''
        radii = self.settings['rvalues']
        #
        # prepare analysis user settings
        command = ''
        header = "--layer100:nameL\n--input100:Name01\nId\tx1\ty1\tx2\ty2"
        if weight_by != '':
            header += "\t" + weight_by
        header += '\n'
        # axial analysis settings
        if self.settings['type'] == 0:
            footer = "--layer--\ntype:2\n"
            footer += "segment.radii:R," + str(radii) + "\n"
            footer += "acp.betweenness:" + str(self.settings['betweenness']) + "\n"
            footer += "acp.measures:" + str(self.settings['fullset']) + "\n"
            footer += "acp.rra:" + str(self.settings['fullset']) + "\n"
            if weight_by != '':
                footer += "acp.weightBy:" + str(self.getWeightPosition(self.settings['weightBy'])) + "\n"
            else:
                footer += "acp.weightBy:-1\n"
            if unlinks_data != '':
                footer += "acp.unlinkid:-1\n"
                footer += "acp.unlinks:" + str(unlinks_data) + "\n"
            footer += "--end--\n"
            command = header + axial_data + footer
        # segment analysis settings
        elif self.settings['type'] == 1:
            footer = "--layer--\ntype:3\n"
            footer += "segment.betweenness:" + str(self.settings['betweenness']) + "\n"
            footer += "segment.fullAngular:" + "0" + "\n"
            footer += "segment.tulip:" + "1" + "\n"
            footer += "segment.tulipCnt:" + "1024" + "\n"
            if self.settings['radius'] == 0:
                footer += "segment.segmentSteps:" + "1" + "\n"
            else:
                footer += "segment.segmentSteps:" + "0" + "\n"
            if self.settings['radius'] == 1:
                footer += "segment.angular:" + "1" + "\n"
            else:
                footer += "segment.angular:" + "0" + "\n"
            if self.settings['radius'] == 2:
                footer += "segment.metric:" + "1" + "\n"
            else:
                footer += "segment.metric:" + "0" + "\n"
            footer += "segment.radii:R," + str(radii) + "\n"
            if weight_by != '':
                footer += "segment.weightBy:" + str(self.getWeightPosition(self.settings['weightBy'])) + "\n"
            else:
                footer += "segment.weightBy:-1\n"
            if unlinks_data != '':
                footer += "acp.unlinkid:-1\n"
                footer += "acp.unlinks:" + str(unlinks_data) + "\n"
            footer += "--end--\n"
            command = header + axial_data + footer
        elif self.settings['type'] == 2:
            command = ''
        return command

    def prepareAxialMap(self, ref='', weight=''):
        axial_data = ''
        try:
            features = self.axial_layer.getFeatures()
            defaults = [""]
            if self.settings['type'] == 0:
                defaults.extend(self.axial_default)
            elif self.settings['type'] == 1:
                defaults.extend(self.segment_default)
            if ref != '':
                if weight not in defaults:
                    for f in features:
                        axial_data += str(f.attribute(ref)) + "\t"
                        axial_data += str(f.geometry().vertexAt(0).x()) + "\t" + str(f.geometry().vertexAt(0).y()) + "\t"
                        axial_data += str(f.geometry().vertexAt(1).x()) + "\t" + str(f.geometry().vertexAt(1).y()) + "\t"
                        axial_data += str(f.attribute(weight)) + "\n"
                else:
                    for f in features:
                        axial_data += str(f.attribute(ref)) + "\t"
                        axial_data += str(f.geometry().vertexAt(0).x()) + "\t" + str(f.geometry().vertexAt(0).y()) + "\t"
                        axial_data += str(f.geometry().vertexAt(1).x()) + "\t" + str(f.geometry().vertexAt(1).y()) + "\n"
            else:
                if weight not in defaults:
                    for f in features:
                        axial_data += str(f.id()) + "\t"
                        axial_data += str(f.geometry().vertexAt(0).x()) + "\t" + str(f.geometry().vertexAt(0).y()) + "\t"
                        axial_data += str(f.geometry().vertexAt(1).x()) + "\t" + str(f.geometry().vertexAt(1).y()) + "\t"
                        axial_data += str(f.attribute(weight)) + "\n"
                else:
                    for f in features:
                        axial_data += str(f.id()) + "\t"
                        axial_data += str(f.geometry().vertexAt(0).x()) + "\t" + str(f.geometry().vertexAt(0).y()) + "\t"
                        axial_data += str(f.geometry().vertexAt(1).x()) + "\t" + str(f.geometry().vertexAt(1).y()) + "\n"
            return axial_data
        except:
            self.showMessage("Exporting axial map failed.",'Error',lev=3, dur=5)
            return ''

    def prepareUnlinks(self):
        unlinks_data = ''
        # check if unlinks layer is valid
        if not fieldExists(self.unlinks_layer, 'line1') or not fieldExists(self.unlinks_layer, 'line2'):
            self.showMessage("Unlinks layer not ready for analysis: update and verify first.",'Warning',lev=2, dur=5)
            return unlinks_data
        elif fieldHasNullValues(self.unlinks_layer, 'line1') or fieldHasNullValues(self.unlinks_layer, 'line2'):
            self.showMessage("Unlinks layer not ready for analysis: update and verify first.",'Warning',lev=2, dur=5)
            return unlinks_data
        # get axial ids
        axialids, ids = getFieldValues(self.axial_layer, self.user_id)
        # assign row number by id
        try:
            features = self.unlinks_layer.getFeatures()
            for f in features:
                row1 = axialids.index(f.attribute('line1'))
                row2 = axialids.index(f.attribute('line2'))
                unlinks_data += str(row1) + ',' + str(row2) + ';'
        except:
            self.showMessage("Exporting unlinks failed.",'Error',lev=3, dur=5)
            return unlinks_data
        if unlinks_data != '':
            unlinks_data = unlinks_data[:-1]
        return unlinks_data

    def prepareLinks(self):
        links_data = ''
        try:
            features = self.links_layer.getFeatures()
            for f in features:
                links_data += str(f.attribute('line1')) + ',' + str(f.attribute('line2')) + ';'
        except:
            self.showMessage("Exporting links failed.",'Error',lev=3, dur=5)
            links_data = ''
        return links_data

    def prepareOrigins(self):
        origins_data = ''
        try:
            features = self.origins_layer.getFeatures()
            for f in features:
                origins_data += str(f.attribute('lineId')) + ';'
        except:
            self.showMessage("Exporting origins failed.",'Error',lev=3, dur=5)
            origins_data = ''
        return origins_data

    def getWeightPosition(self,name):
        pos = -1
        new_name = name
        names = []
        if self.settings['type'] == 0:
            names.extend(self.axial_default)
        elif self.settings['type'] == 1:
            names.extend(self.segment_default)
            # depthmapX assumes that the weight column is an axial property.
            new_name = "Axial "+name
        new_name = new_name.title()
        if new_name not in names:
            names.append(new_name)
        names.sort()
        pos = names.index(new_name)
        return pos

    def parseRadii(self, txt):
        radii = txt
        radii.lower()
        radii = radii.replace(' ','')
        radii = radii.split(',')
        radii.sort()
        radii = list(set(radii))
        radii = ['0' if x == 'n' else x for x in radii]
        for r in radii:
            if not isNumeric(r):
                return ''
        radii = ','.join(radii)
        return radii

    def processAnalysisResult(self, datastore, result):
        # parse the results, splitting rows and then columns
        new_result = result.split("\n")
        #discard the first row if it has garbage from comm:
        while "--result100" not in new_result[0]:
            new_result.pop(0)
        #collect result in rows
        final_result = []
        for line in new_result:
            if "--result" not in line and "--comm" not in line and line != '':
                final_result.append(line.split(","))
        if len(final_result) == 0:
            return None, None, None, None
        attributes = final_result[0]
        values = final_result[1:len(final_result)]
        # Process the attributes, renaming them and selecting only relevant ones
        exclusions = []
        # keep only most important attributes
        if self.settings['fullset'] == 0:
            exclusions = self.excludeDepthmapResults(attributes)
            # remove HH suffix from integration measure
            attributes = [x.replace(" [HH]","") for x in attributes]
        # remove weight attribute if duplicate
        if self.settings['weight']:
            weight_by = self.settings['weightBy'].title() + ' 1'
            if weight_by.title() in attributes:
                exclusions.append(attributes.index(weight_by))
        # remove attributes and values from lists
        if len(exclusions) > 0:
            exclusions.sort(reverse=True)
            values = zip(*values)
            for i in exclusions:
                attributes.pop(i)
                values.pop(i)
            values = zip(*values)
        # replace axial ref by axial id
        if "Axial Ref" in attributes:
            idx = attributes.index("Axial Ref")
            attributes[idx] = "Axial Id"
        if "Id" in attributes:
            idx = attributes.index("Id")
            attributes[idx] = "Axial Id"
        # remove spaces
        #attributes = [x.replace(" ","_") for x in attributes]
        # get data type of attributes
        types = []
        data_sample = [convertNumeric(x) for x in values[0]]
        for data in data_sample:
            data_type = None
            # get the data types
            if type(data).__name__ == 'int': data_type = QVariant.Int
            elif type(data).__name__ == 'long': data_type = QVariant.LongLong
            elif type(data).__name__ == 'str': data_type = QVariant.String
            elif type(data).__name__ == 'float': data_type = QVariant.Double
            # define the attributes, using name and type
            types.append(data_type)
        coords = [attributes.index('x1'),attributes.index('y1'),attributes.index('x2'),attributes.index('y2')]
        # calculate new normalised variables
        if self.settings['type'] == 1 and self.settings['newnorm'] == 1:
            new_attributes, values = self.calculateNormalisedSegment(attributes, values)
            attributes.extend(new_attributes)
            new_types = [QVariant.Double] * len(new_attributes)
            types.extend(new_types)
        #the attribute names must be fixed
        if datastore['type'] == 1:
            # when working with shape files
            attributes = self.fixDepthmapNames(attributes)
        else:
            # when working with geodatabases
            attr = []
            for x in attributes:
                # remove square brackets
                x = x.replace("[","")
                x = x.replace("]","")
                # make lowercase
                # x = x.lower()
                attr.append(x)
            attributes = attr

        return attributes, types, values, coords

    def excludeDepthmapResults(self,attributes):
        # list of attributes to exclude
        exclusion_list = ['[Norm]','Controllability','Entropy','Harmonic','[P-value]','[Tekl]','Intensity']
        attributes_to_remove = []
        for i, attr in enumerate(attributes):
            if any(substring in attr for substring in exclusion_list):
                attributes_to_remove.append(i)
        return attributes_to_remove

    def calculateNormalisedSegment(self, attributes, values):
        choice = []
        nc = []
        td = []
        nach = []
        nain = []
        # identify new attributes that need to be calculated
        for i, attr in enumerate(attributes):
            if 'Choice' in attr:
                choice.append(i)
                nach.append(attr.replace('Choice','NACH'))
            if 'Node Count' in attr:
                nc.append(i)
            if 'Total Depth' in attr:
                td.append(i)
                nain.append(attr.replace('Total Depth','NAIN'))
        new_attributes = []
        new_attributes.extend(nach)
        new_attributes.extend(nain)
        #attributes.extend(new_attributes)
        # calculate new values
        all_values = []
        for feat in values:
            feat = list(feat)
            calc_values = []
            for i, j in enumerate(choice):
                val = math.log(float(feat[j])+1.0)/math.log(float(feat[td[i]])+3.0)
                calc_values.append(val)
            for i, j in enumerate(td):
                if i < len(nc):
                    val = (float(feat[nc[i]])**1.2)/float(feat[j])
                else:
                    val = (float(feat[nc[i-len(nc)]])**1.2)/float(feat[j])
                calc_values.append(val)
            feat.extend(calc_values)
            all_values.append(feat)
        return new_attributes, all_values

    def fixDepthmapNames(self,names):
        #proper conversion makes short version based on real name
        replacement_table = {
            'choice' : 'CH',
            'connectivity' : 'CONN',
            '[norm]' : 'norm',
            'controllability' : 'CONTR',
            'entropy' : 'ENT',
            'harmonic' : 'har',
            'mean' : 'M',
            'depth' : 'D',
            'integration' : 'INT',
            '[hh]' : 'hh',
            '[p-value]' : 'pv',
            '[tekl]' : 'tk',
            'intensity' : 'INTEN',
            'line' : '',
            'node' : 'N',
            'count' : 'C',
            'relativised' : 'rel',
            'angular' : 'ang',
            'axial' : 'ax',
            'segment': 'seg',
            'length' : 'LEN',
            'metric' : 'm',
            't1024' : '',
            'total' : 'T',
            'wgt]' : ']',
            'wgt][norm]' : ']norm',
            'nach' : 'NACH',
            'nain' : 'NAIN'
        }
        #using simple dict / string operations
        new_names = []
        for name in names:
            parts = name.split(" ")
            new_name = ""
            for part in parts:
                part = part.lower()
                try:
                    text = replacement_table[part]
                except KeyError:
                    try:
                        text = "[" + replacement_table[part.replace("[","")]
                    except KeyError:
                        text = part
                new_name += text
            new_names.append(new_name)
        return new_names

#####
# newfeature: unused, not sure this is working properly. look at threads in verification
    def threadAxialMap(self, action):
        # create thread to export map geometry and extra attributes
        if action == 'export':
            if self.settings['weight']:
                weight_by = self.settings['weightBy']
            else:
                weight_by = ''
            self.axial_thread = ExportAxialMap(self.iface.mainWindow(), self, self.axial_layer, self.user_id, weight_by)
        #else:
        #    self.axial_thread = ImportAxialMap(self.iface.mainWindow(), self, result)
        # put it in separate thread
        self.axial_thread.status.connect(self.showMessage)
        self.axial_thread.error.connect(self.showMessage)
        self.axial_thread.result.connect(self.prepareAxialAnalysis)
        self.axial_thread.start()

#####
#class to extract the model geometry for input in Depthmap.
# can be slow with large models and need to run it in separate thread
class ExportAxialMap(QThread):
    def __init__(self, parentThread, parentObject, layer, ref='', weight=''):
        QThread.__init__(self, parentThread)
        self.parent = parentObject
        self.layer = layer
        self.abort = False
        self.id = id
        self.weight = weight

    def run(self):
        axialLayer = ''
        try:
            features = self.layer.getFeatures()
            if self.id in self.layer.dataProvider().fields():
                if self.weight != '':
                    for f in features:
                        axialLayer += str(f.attribute(self.id)) + "\t"
                        axialLayer += str(f.geometry().vertexAt(0).x()) + "\t" + str(f.geometry().vertexAt(0).y()) + "\t"
                        axialLayer += str(f.geometry().vertexAt(1).x()) + "\t" + str(f.geometry().vertexAt(1).y()) + "\t"
                        axialLayer += str(f.attribute(self.weight)) + "\n"
                else:
                    for f in features:
                        axialLayer += str(f.attribute(self.id)) + "\t"
                        axialLayer += str(f.geometry().vertexAt(0).x()) + "\t" + str(f.geometry().vertexAt(0).y()) + "\t"
                        axialLayer += str(f.geometry().vertexAt(1).x()) + "\t" + str(f.geometry().vertexAt(1).y()) + "\n"
            else:
                if self.weight != '':
                    for f in features:
                        axialLayer += str(f.id()) + "\t"
                        axialLayer += str(f.geometry().vertexAt(0).x()) + "\t" + str(f.geometry().vertexAt(0).y()) + "\t"
                        axialLayer += str(f.geometry().vertexAt(1).x()) + "\t" + str(f.geometry().vertexAt(1).y()) + "\t"
                        axialLayer += str(f.attribute(self.weight)) + "\n"
                else:
                    for f in features:
                        axialLayer += str(f.id()) + "\t"
                        axialLayer += str(f.geometry().vertexAt(0).x()) + "\t" + str(f.geometry().vertexAt(0).y()) + "\t"
                        axialLayer += str(f.geometry().vertexAt(1).x()) + "\t" + str(f.geometry().vertexAt(1).y()) + "\n"
            self.status.emit('Model exported for analysis.')
            self.result.emit(axialLayer)
        except:
            self.error.emit('Exporting model failed.')

    def stop(self):
        self.abort = True
        self.killed.emit()
        self.terminate()

    status = pyqtSignal(str)
    result = pyqtSignal(str)
    error = pyqtSignal(str)
    killed = pyqtSignal()
