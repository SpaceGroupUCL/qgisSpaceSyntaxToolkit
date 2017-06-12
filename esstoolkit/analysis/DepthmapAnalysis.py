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

import math

from .. import utility_functions as uf

class DepthmapAnalysis(QObject):

    def __init__(self, iface):
        QObject.__init__(self)

        self.iface = iface

        #initialise global variables
        self.axial_layer = None
        self.datastore = None
        self.settings = None
        self.axial_default = ('Connectivity','Line Length','Id')
        self.segment_default = ('Angular Connectivity','Axial Connectivity','Axial Id',
                                'Axial Line Length','Axial Line Ref','Connectivity','Segment Length')
        self.axial_id = ''

    def showMessage(self, msg, type='Info', lev=1, dur=2):
        self.iface.messageBar().pushMessage(type,msg,level=lev,duration=dur)

    def setupAnalysis(self, layers, settings):
        self.settings = settings
        # get relevant QGIS layer objects
        axial = layers['map']
        if axial != '':
            self.axial_layer = uf.getLegendLayerByName(self.iface, axial)
        else:
            return None
        if layers['unlinks'] != '':
            self.unlinks_layer = uf.getLegendLayerByName(self.iface, layers['unlinks'])
        else:
            self.unlinks_layer = ''
        #
        # prepare analysis layers
        if self.settings['weight']:
            weight_by = self.settings['weightBy']
        else:
            weight_by = ''
        # look for user defined ID
        if self.settings['id']:
            self.axial_id = self.settings['id']
        else:
            self.axial_id = uf.getIdField(self.axial_layer)
        if self.settings['type'] in (0,1):
            axial_data = self.prepareAxialMap(self.axial_id, weight_by)
        else:
            #axial_data = self.prepareAxialMap(self.axial_id, weight_by)
            axial_data = self.prepareSegmentMap(self.axial_id, weight_by)
        if axial_data == '':
            self.showMessage("The axial layer is not ready for analysis: verify its geometry first.", 'Info', lev=1, dur=5)
            return ''
        if self.unlinks_layer:
            unlinks_data = self.prepareUnlinks()
        else:
            unlinks_data = ''
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
        # segment analysis settings with segmentation and unlinks
        elif self.settings['type'] == 1:
            footer = "--layer--\ntype:3\n"
            footer += "segment.stubs:" + str(self.settings['stubs']) + "\n"
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
        # segment analysis settings, data only
        elif self.settings['type'] == 2:
            footer = "--layer--\ntype:4\n"
            footer += "segment.stubs:" + str(self.settings['stubs']) + "\n"
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
            # I leave all the if clauses outside the for loop to gain some speed
            if ref != '':
                if weight not in defaults:
                    for f in features:
                        axial_data += str(f.attribute(ref)) + "\t"
                        axial_data += str(f.geometry().vertexAt(0).x()) + "\t" +\
                                      str(f.geometry().vertexAt(0).y()) + "\t"
                        axial_data += str(f.geometry().vertexAt(1).x()) + "\t" +\
                                      str(f.geometry().vertexAt(1).y()) + "\t"
                        axial_data += str(f.attribute(weight)) + "\n"
                else:
                    for f in features:
                        axial_data += str(f.attribute(ref)) + "\t"
                        axial_data += str(f.geometry().vertexAt(0).x()) + "\t" +\
                                      str(f.geometry().vertexAt(0).y()) + "\t"
                        axial_data += str(f.geometry().vertexAt(1).x()) + "\t" +\
                                      str(f.geometry().vertexAt(1).y()) + "\n"
            else:
                if weight not in defaults:
                    for f in features:
                        axial_data += str(f.id()) + "\t"
                        axial_data += str(f.geometry().vertexAt(0).x()) + "\t" +\
                                      str(f.geometry().vertexAt(0).y()) + "\t"
                        axial_data += str(f.geometry().vertexAt(1).x()) + "\t" +\
                                      str(f.geometry().vertexAt(1).y()) + "\t"
                        axial_data += str(f.attribute(weight)) + "\n"
                else:
                    for f in features:
                        axial_data += str(f.id()) + "\t"
                        axial_data += str(f.geometry().vertexAt(0).x()) + "\t" +\
                                      str(f.geometry().vertexAt(0).y()) + "\t"
                        axial_data += str(f.geometry().vertexAt(1).x()) + "\t" +\
                                      str(f.geometry().vertexAt(1).y()) + "\n"
            return axial_data
        except:
            self.showMessage("Exporting axial map failed.", 'Error', lev=3, dur=5)
            return ''

    def prepareSegmentMap(self, ref='', weight=''):
        segment_data = ''
        try:
            features = self.axial_layer.getFeatures()
            defaults = [""]
            if self.settings['type'] == 0:
                defaults.extend(self.axial_default)
            elif self.settings['type'] in (1, 2):
                defaults.extend(self.segment_default)
            # I leave all the if clauses outside the for loop to gain some speed
            vid = QgsVertexId()
            if ref != '':
                if weight not in defaults:
                    for f in features:
                        nr = 0
                        while f.geometry().vertexIdFromVertexNr(nr+1,vid):
                            segment_data += str(f.attribute(ref)) + "\t"
                            segment_data += str(f.geometry().vertexAt(nr).x()) + "\t" +\
                                          str(f.geometry().vertexAt(nr).y()) + "\t"
                            segment_data += str(f.geometry().vertexAt(nr+1).x()) + "\t" +\
                                          str(f.geometry().vertexAt(nr+1).y()) + "\t"
                            segment_data += str(f.attribute(weight)) + "\n"
                            nr += 1
                else:
                    for f in features:
                        nr = 0
                        while f.geometry().vertexIdFromVertexNr(nr+1,vid):
                            segment_data += str(f.attribute(ref)) + "\t"
                            segment_data += str(f.geometry().vertexAt(nr).x()) + "\t" +\
                                          str(f.geometry().vertexAt(nr).y()) + "\t"
                            segment_data += str(f.geometry().vertexAt(nr+1).x()) + "\t" +\
                                          str(f.geometry().vertexAt(nr+1).y()) + "\n"
                            nr += 1
            else:
                if weight not in defaults:
                    for f in features:
                        nr = 0
                        while f.geometry().vertexIdFromVertexNr(nr+1,vid):
                            segment_data += str(f.id()) + "\t"
                            segment_data += str(f.geometry().vertexAt(nr).x()) + "\t" +\
                                          str(f.geometry().vertexAt(nr).y()) + "\t"
                            segment_data += str(f.geometry().vertexAt(nr+1).x()) + "\t" +\
                                          str(f.geometry().vertexAt(nr+1).y()) + "\t"
                            segment_data += str(f.attribute(weight)) + "\n"
                            nr += 1
                else:
                    for f in features:
                        nr = 0
                        while f.geometry().vertexIdFromVertexNr(nr+1,vid):
                            segment_data += str(f.id()) + "\t"
                            segment_data += str(f.geometry().vertexAt(nr).x()) + "\t" +\
                                          str(f.geometry().vertexAt(nr).y()) + "\t"
                            segment_data += str(f.geometry().vertexAt(nr+1).x()) + "\t" +\
                                          str(f.geometry().vertexAt(nr+1).y()) + "\n"
                            nr += 1
            return segment_data
        except:
            self.showMessage("Exporting segment map failed.", 'Error', lev=3, dur=5)
            return ''

    def prepareUnlinks(self):
        unlinks_data = ''
        # check if unlinks layer is valid
        if not uf.fieldExists(self.unlinks_layer, 'line1') or not uf.fieldExists(self.unlinks_layer, 'line2'):
            self.showMessage("Unlinks layer not ready for analysis: update and verify first.", 'Info', lev=1, dur=5)
            return unlinks_data
        elif uf.fieldHasNullValues(self.unlinks_layer, 'line1') or uf.fieldHasNullValues(self.unlinks_layer, 'line2'):
            self.showMessage("Unlinks layer not ready for analysis: update and verify first.", 'Info', lev=1, dur=5)
            return unlinks_data
        # get axial ids
        axialids, ids = uf.getFieldValues(self.axial_layer, self.axial_id)
        # assign row number by id
        try:
            features = self.unlinks_layer.getFeatures()
            for f in features:
                row1 = axialids.index(f.attribute('line1'))
                row2 = axialids.index(f.attribute('line2'))
                unlinks_data += str(row1) + ',' + str(row2) + ';'
        except:
            self.showMessage("Exporting unlinks failed.", 'Warning',lev=1, dur=5)
            return unlinks_data
        if unlinks_data != '':
            unlinks_data = unlinks_data[:-1]
        return unlinks_data

    def getWeightPosition(self,name):
        pos = -1
        names = []
        weight_name = name.title()
        if self.settings['type'] == 0:
            names.extend(self.axial_default)
        elif self.settings['type'] == 1:
            names.extend(self.segment_default)
            # depthmapX creates a weight column as an axial property. to remove later
            weight_name = "Axial %s" % weight_name
        if weight_name not in names:
            names.append(weight_name)
        names.sort()
        # this is an exception, segment length is not an attribute in the axial table
        # but one of the defaults made available in the weights drop down. The original name must be used
        if name == "Segment Length":
            pos = names.index(name)
        else:
            pos = names.index(weight_name)
        return pos

    def parseRadii(self, txt):
        radii = txt
        radii.lower()
        radii = radii.replace(' ', '')
        radii = radii.split(',')
        radii.sort()
        radii = list(set(radii))
        radii = ['0' if x == 'n' else x for x in radii]
        for r in radii:
            if not uf.isNumeric(r):
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
        if values == []:
            return attributes, None, None, None
        # Process the attributes, renaming them and selecting only relevant ones
        exclusions = []
        # keep only most important attributes
        if self.settings['fullset'] == 0:
            exclusions = self.excludeDepthmapResults(attributes)
            # remove HH suffix from integration measure
            attributes = [x.replace(" [HH]", "") for x in attributes]
        # remove weight attribute if duplicate
        if self.settings['weight']:
            weight_by = self.settings['weightBy'].title() + ' 1'
            if weight_by.title() in attributes:
                exclusions.append(attributes.index(weight_by.title()))
            # also remove the invalid "Axial Segment Length" attribute
            if "Axial Segment Length" in attributes:
                exclusions.append(attributes.index("Axial Segment Length"))
        # replace axial ref by axial id
        if "Axial Ref" in attributes:
            idx = attributes.index("Axial Ref")
            attributes[idx] = "Axial Id"
        if "Id" in attributes:
            idx = attributes.index("Id")
            if self.settings['type'] == 1:
                attributes[idx] = "Axial Id"
            elif self.axial_id in attributes:
                attributes[idx] = "Axial Id"
            else:
                attributes[idx] = self.axial_id
        # remove attributes and values from lists
        if len(exclusions) > 0:
            exclusions.sort(reverse=True)
            values = zip(*values)
            for i in exclusions:
                attributes.pop(i)
                values.pop(i)
            values = zip(*values)
        # remove spaces
        attributes = [x.replace(" ","_") for x in attributes]
        # get data type of attributes
        types = []
        data_sample = [uf.convertNumeric(x) for x in values[0]]
        for data in data_sample:
            data_type = None
            # get the data types
            if type(data).__name__ == 'int':
                data_type = QVariant.Int
            elif type(data).__name__ == 'long':
                data_type = QVariant.LongLong
            elif type(data).__name__ == 'str':
                data_type = QVariant.String
            elif type(data).__name__ == 'float':
                data_type = QVariant.Double
            # store the attributes type
            types.append(data_type)
        # get coords
        coords = [attributes.index('x1'), attributes.index('y1'), attributes.index('x2'), attributes.index('y2')]
        # calculate new normalised variables
        if self.settings['type'] in (1, 2) and self.settings['newnorm'] == 1:
            new_attributes, values = self.calculateNormalisedSegment(attributes, values)
            attributes.extend(new_attributes)
            new_types = [QVariant.Double] * len(new_attributes)
            types.extend(new_types)
        #the attribute names must be fixed
        if datastore['type'] == 0:
            # when working with shape files
            attributes = self.fixDepthmapNames(attributes)
        else:
            # when working with geodatabases
            attr = []
            for x in attributes:
                # remove square brackets
                x = x.replace("[", "")
                x = x.replace("]", "")
                # make lowercase
                x = x.lower()
                attr.append(x)
            attributes = attr

        return attributes, types, values, coords

    def excludeDepthmapResults(self, attributes):
        # list of attributes to exclude
        exclusion_list = ['[Norm]', 'Controllability', 'Entropy', 'Harmonic', '[P-value]', '[Tekl]', 'Intensity']
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
                nach.append(attr.replace('Choice', 'NACH'))
            if 'Node_Count' in attr:
                nc.append(i)
            if 'Total_Depth' in attr:
                td.append(i)
                nain.append(attr.replace('Total_Depth', 'NAIN'))
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
                try:
                    val = math.log(float(feat[j])+1.0)/math.log(float(feat[td[i]])+3.0)
                    calc_values.append(val)
                except:
                    calc_values.append(NULL)
            for i, j in enumerate(td):
                try:
                    if i < len(nc):
                        val = (float(feat[nc[i]])**1.2)/(float(feat[j])+2.0)
                    else:
                        val = (float(feat[nc[i-len(nc)]])**1.2)/(float(feat[j])+2.0)
                    calc_values.append(val)
                except:
                    calc_values.append(NULL)
            feat.extend(calc_values)
            all_values.append(feat)
        return new_attributes, all_values

    def fixDepthmapNames(self, names):
        #proper conversion makes short version based on real name
        replacement_table = {
            'choice': 'CH',
            'connectivity': 'CONN',
            '[norm]': 'norm',
            'controllability': 'CONTR',
            'entropy': 'ENT',
            'harmonic': 'har',
            'mean': 'M',
            'depth': 'D',
            'integration': 'INT',
            '[hh]': 'hh',
            '[p-value]': 'pv',
            '[tekl]': 'tk',
            'intensity': 'INTEN',
            'line': '',
            'node': 'N',
            'count': 'C',
            'relativised': 'rel',
            'angular': 'ang',
            'axial': 'ax',
            'segment': 'seg',
            'length': 'LEN',
            'metric': 'm',
            't1024': '',
            'total': 'T',
            'wgt]': ']',
            'wgt][norm]': ']norm',
            'nach': 'NACH',
            'nain': 'NAIN'
        }
        #using simple dict / string operations
        new_names = []
        for name in names:
            parts = name.split("_")
            new_name = ""
            for part in parts:
                part = part.lower()
                try:
                    text = replacement_table[part]
                except KeyError:
                    try:
                        text = "[" + replacement_table[part.replace("[", "")]
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
            self.axial_thread = ExportMap(self.iface.mainWindow(), self, self.axial_layer, self.user_id, weight_by)
        #else:
        #    self.axial_thread = ImportAxialMap(self.iface.mainWindow(), self, result)
        # put it in separate thread
        self.axial_thread.status.connect(self.showMessage)
        self.axial_thread.error.connect(self.showMessage)
        self.axial_thread.result.connect(self.prepareAxialAnalysis)
        self.axial_thread.start()


#####
# class to extract the model geometry for input in Depthmap.
# can be slow with large models and need to run it in separate thread
class ExportMap(QThread):
    def __init__(self, parent_thread, parent_object, layer, ref='', weight=''):
        QThread.__init__(self, parent_thread)
        self.parent = parent_object
        self.layer = layer
        self.abort = False
        self.id = ref
        self.weight = weight

    def run(self):
        segment_data = ''
        try:
            features = self.axial_layer.getFeatures()
            # I leave all the if clauses outside the for loop to gain some speed
            vid = QgsVertexId()
            if self.id != '':
                if self.weight != '':
                    for f in features:
                        nr = 0
                        while f.geometry().vertexIdFromVertexNr(nr+1,vid):
                            segment_data += str(f.attribute(self.id)) + "\t"
                            segment_data += str(f.geometry().vertexAt(nr).x()) + "\t" +\
                                          str(f.geometry().vertexAt(nr).y()) + "\t"
                            segment_data += str(f.geometry().vertexAt(nr+1).x()) + "\t" +\
                                          str(f.geometry().vertexAt(nr+1).y()) + "\t"
                            segment_data += str(f.attribute(self.weight)) + "\n"
                            nr += 1
                else:
                    for f in features:
                        nr = 0
                        while f.geometry().vertexIdFromVertexNr(nr+1,vid):
                            segment_data += str(f.attribute(self.id)) + "\t"
                            segment_data += str(f.geometry().vertexAt(nr).x()) + "\t" +\
                                          str(f.geometry().vertexAt(nr).y()) + "\t"
                            segment_data += str(f.geometry().vertexAt(nr+1).x()) + "\t" +\
                                          str(f.geometry().vertexAt(nr+1).y()) + "\n"
                            nr += 1
            else:
                if self.weight != '':
                    for f in features:
                        nr = 0
                        while f.geometry().vertexIdFromVertexNr(nr+1,vid):
                            segment_data += str(f.id()) + "\t"
                            segment_data += str(f.geometry().vertexAt(nr).x()) + "\t" +\
                                          str(f.geometry().vertexAt(nr).y()) + "\t"
                            segment_data += str(f.geometry().vertexAt(nr+1).x()) + "\t" +\
                                          str(f.geometry().vertexAt(nr+1).y()) + "\t"
                            segment_data += str(f.attribute(self.weight)) + "\n"
                            nr += 1
                else:
                    for f in features:
                        nr = 0
                        while f.geometry().vertexIdFromVertexNr(nr+1,vid):
                            segment_data += str(f.id()) + "\t"
                            segment_data += str(f.geometry().vertexAt(nr).x()) + "\t" +\
                                          str(f.geometry().vertexAt(nr).y()) + "\t"
                            segment_data += str(f.geometry().vertexAt(nr+1).x()) + "\t" +\
                                          str(f.geometry().vertexAt(nr+1).y()) + "\n"
                            nr += 1
            self.status.emit('Model exported for analysis.')
            self.result.emit(segment_data)
        except:
            self.error.emit('Exporting segment map failed.')

    def stop(self):
        self.abort = True
        self.killed.emit()
        self.terminate()

    status = pyqtSignal(str)
    result = pyqtSignal(str)
    error = pyqtSignal(str)
    killed = pyqtSignal()
