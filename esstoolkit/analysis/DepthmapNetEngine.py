# -*- coding: utf-8 -*-

# Space Syntax Toolkit
# Set of tools for essential space syntax network analysis and results exploration
# -------------------
# begin                : 2014-04-01
# copyright            : (C) 2015 by Jorge Gil, UCL
# author               : Jorge Gil
# email                : jorge.gil@ucl.ac.uk
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.

from builtins import str

from qgis.PyQt.QtCore import (QObject, QThread, pyqtSignal)
from qgis.core import (QgsVertexId)

from esstoolkit.analysis.AnalysisEngine import AnalysisEngine
from esstoolkit.analysis.DepthmapEngine import DepthmapEngine
from esstoolkit.analysis.DepthmapNetSocket import DepthmapNetSocket
from esstoolkit.utilities import layer_field_helpers as lfh


# Import the PyQt and QGIS libraries


class DepthmapNetEngine(QObject, DepthmapEngine):

    def __init__(self, iface):
        QObject.__init__(self)

        self.iface = iface

        # initialise global variables
        self.axial_layer = None
        self.axial_id = ''
        self.socket = None
        self.command = ''
        self.analysis_results = None

    def ready(self):
        return self.connect_depthmap_net()

    @staticmethod
    def get_depthmap_connection():
        # newfeature: get these settings from settings manager.
        # no need for it now as it's hardcoded in depthmapXnet.
        connection = {'host': 'localhost', 'port': 31337}
        return connection

    def connect_depthmap_net(self):
        connection = self.get_depthmap_connection()
        self.socket = DepthmapNetSocket()
        # connect socket
        result = self.socket.connectSocket(connection['host'], connection['port'])
        # if connection fails give warning and stop analysis
        if result != '':
            self.iface.messageBar().pushMessage("Info", "Make sure depthmapXnet is running.", level=0, duration=4)
            connected = False
            self.socket.closeSocket()
        else:
            connected = True
        return connected

    def start_analysis(self):
        # start the analysis by sending the command and starting the timer
        self.socket.sendData(self.command)

    def parse_results(self, result):
        # parse the results, splitting rows and then columns
        new_result = result.split("\n")
        # discard the first row if it has garbage from comm:
        while "--result100" not in new_result[0]:
            new_result.pop(0)
        # collect result in rows
        final_result = []
        for line in new_result:
            if "--result" not in line and "--comm" not in line and line != '':
                final_result.append(line.split(","))
        if len(final_result) == 0:
            return None, None
        attributes = final_result[0]
        values = final_result[1:len(final_result)]
        return attributes, values

    def parse_progress(self, msg):
        # calculate percent done and adjust timer
        relprog = 0
        step = 0
        # extract number of nodes
        if "--comm: 2," in msg:
            pos1 = msg.find(": 2,")
            pos2 = msg.find(",0 --", pos1)
            self.analysis_nodes = int(msg[(pos1 + 4):pos2])
            step = int(self.analysis_nodes) * 0.2
        # extract progress info from string
        progress = msg.split("\n")
        # calculate progress
        if self.analysis_nodes > 0:
            pos1 = progress[-2].find(": 3,")
            pos2 = progress[-2].find(",0 ")
            prog = progress[-2][(pos1 + 4):pos2]
            relprog = (float(prog) / float(self.analysis_nodes)) * 100
        return step, relprog

    def get_progress(self, analysis_settings, datastore):
        if not self.socket.isReady():
            raise AnalysisEngine.AnalysisEngineError("Socket connection failed, make sure"
                                                     "depthmapXNet is running")
        connected, msg = self.socket.checkData(4096)
        if "--r" in msg or "esult" in msg:
            # retrieve all the remaining data
            if not msg.endswith("--result--\n"):
                received, result = self.socket.receiveData(4096, "--result--\n")
                if received:
                    msg += result
            self.socket.closeSocket()
            attributes, values = self.parse_results(msg)
            self.analysis_results = DepthmapEngine.process_analysis_result(analysis_settings, datastore, attributes, values)
            return 0, 100
        elif "--comm: 3," in msg:
            return self.parse_progress(msg)
        elif not connected:
            raise AnalysisEngine.AnalysisEngineError("Socket connection failed, make sure"
                                                     "depthmapXNet is running")
        return None, None

    def cleanup(self):
        self.socket.closeSocket()

    def showMessage(self, msg, type='Info', lev=1, dur=2):
        self.iface.messageBar().pushMessage(type, msg, level=lev, duration=dur)

    def setup_analysis(self, layers, settings):
        self.settings = settings
        # get relevant QGIS layer objects
        axial = layers['map']
        if axial != '':
            self.axial_layer = lfh.getLegendLayerByName(self.iface, axial)
        else:
            return False
        if layers['unlinks'] != '':
            self.unlinks_layer = lfh.getLegendLayerByName(self.iface, layers['unlinks'])
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
            self.axial_id = lfh.getIdField(self.axial_layer)
        # prepare map and unlinks layers
        if self.settings['type'] in (0, 1):
            axial_data = self.prepare_axial_map(self.axial_layer, self.settings['type'],
                                                self.axial_id, weight_by, '\t', False)
            if axial_data == '':
                self.showMessage("The axial layer is not ready for analysis: verify it first.", 'Info', lev=1, dur=5)
                return False
            if self.unlinks_layer:
                unlinks_data = self.prepare_unlinks(self.axial_layer, self.unlinks_layer, self.axial_id)
            else:
                unlinks_data = ''
        else:
            axial_data = self.prepare_segment_map(self.axial_layer, settings['type'],
                                                  self.axial_id, weight_by, '\t', False)
            unlinks_data = ''
        # get radius values
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
            footer += "--end--\n"
            command = header + axial_data + footer
        self.command = command
        return command and command != ''

    def getWeightPosition(self, name):
        pos = -1
        names = []
        weight_name = name.title()
        if self.settings['type'] == 0:
            names.extend(self.axial_default)
        elif self.settings['type'] == 1:
            names.extend(self.segment_default)
            # depthmapX creates a weight column as an axial property. to remove later
            weight_name = "Axial %s" % weight_name
        elif self.settings['type'] == 2:
            names.extend(self.rcl_default)
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
        # else:
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
                        while f.geometry().vertexIdFromVertexNr(nr + 1, vid):
                            segment_data += str(f.attribute(self.id)) + "\t"
                            segment_data += str(f.geometry().vertexAt(nr).x()) + "\t" + \
                                            str(f.geometry().vertexAt(nr).y()) + "\t"
                            segment_data += str(f.geometry().vertexAt(nr + 1).x()) + "\t" + \
                                            str(f.geometry().vertexAt(nr + 1).y()) + "\t"
                            segment_data += str(f.attribute(self.weight)) + "\n"
                            nr += 1
                else:
                    for f in features:
                        nr = 0
                        while f.geometry().vertexIdFromVertexNr(nr + 1, vid):
                            segment_data += str(f.attribute(self.id)) + "\t"
                            segment_data += str(f.geometry().vertexAt(nr).x()) + "\t" + \
                                            str(f.geometry().vertexAt(nr).y()) + "\t"
                            segment_data += str(f.geometry().vertexAt(nr + 1).x()) + "\t" + \
                                            str(f.geometry().vertexAt(nr + 1).y()) + "\n"
                            nr += 1
            else:
                if self.weight != '':
                    for f in features:
                        nr = 0
                        while f.geometry().vertexIdFromVertexNr(nr + 1, vid):
                            segment_data += str(f.id()) + "\t"
                            segment_data += str(f.geometry().vertexAt(nr).x()) + "\t" + \
                                            str(f.geometry().vertexAt(nr).y()) + "\t"
                            segment_data += str(f.geometry().vertexAt(nr + 1).x()) + "\t" + \
                                            str(f.geometry().vertexAt(nr + 1).y()) + "\t"
                            segment_data += str(f.attribute(self.weight)) + "\n"
                            nr += 1
                else:
                    for f in features:
                        nr = 0
                        while f.geometry().vertexIdFromVertexNr(nr + 1, vid):
                            segment_data += str(f.id()) + "\t"
                            segment_data += str(f.geometry().vertexAt(nr).x()) + "\t" + \
                                            str(f.geometry().vertexAt(nr).y()) + "\t"
                            segment_data += str(f.geometry().vertexAt(nr + 1).x()) + "\t" + \
                                            str(f.geometry().vertexAt(nr + 1).y()) + "\n"
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
