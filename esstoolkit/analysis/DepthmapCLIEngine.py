# -*- coding: utf-8 -*-

# Space Syntax Toolkit
# Set of tools for essential space syntax network analysis and results exploration
# -------------------
# begin                : 2020-09-01
# copyright            : (C) 2020 by Petros Koutsolampros, Space Syntax Ltd.
# author               : Petros Koutsolampros
# email                : p.koutsolampros@spacesyntax.com
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.

import csv
import os
import platform
import re
import subprocess
import tempfile
import threading
from builtins import str

from qgis.PyQt.QtCore import (QObject)

from esstoolkit.analysis.DepthmapEngine import DepthmapEngine
from esstoolkit.utilities import layer_field_helpers as lfh, utility_functions as uf
from esstoolkit.utilities.exceptions import BadInputError


# Import the PyQt and QGIS libraries


class DepthmapCLIEngine(QObject, DepthmapEngine):

    def __init__(self, iface):
        QObject.__init__(self)

        self.iface = iface

        # initialise global variables
        self.axial_layer = None
        self.datastore = None
        self.settings = None
        self.axial_id = ''
        self.prep_line_data = None
        self.prep_unlink_data = None
        self.analysis_settings = None
        self.analysis_process = None
        self.analysis_graph_file = None
        self.analysis_results = None

    def showMessage(self, msg, type='Info', lev=1, dur=2):
        self.iface.messageBar().pushMessage(type, msg, level=lev, duration=dur)

    @staticmethod
    def get_depthmap_cli():
        if platform.system() == "Windows":
            ext = "exe"
        elif platform.system() == "Darwin":
            ext = "darwin"
        elif platform.system() == "Linux":
            ext = "linux"
        else:
            raise ValueError('Unknown platform: ' + platform.system())
        basepath = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
        return os.path.join(basepath, "depthmapXcli/depthmapXcli." + ext)

    @staticmethod
    def ready():
        return os.path.isfile(DepthmapCLIEngine.get_depthmap_cli())

    @staticmethod
    def parse_result_file(result_file):
        values = []
        with open(result_file, newline='') as f:
            reader = csv.reader(f)
            first_row = True
            for row in reader:
                if first_row:
                    attributes = row
                    first_row = False
                else:
                    values.append(row)
        return attributes, values

    def get_line_data_csv(self, layers, settings):

        # get relevant QGIS layer objects
        axial = layers['map']
        if axial != '':
            axial_layer = lfh.getLegendLayerByName(self.iface, axial)
        else:
            return None

        if layers['unlinks'] != '':
            unlinks_layer = lfh.getLegendLayerByName(self.iface, layers['unlinks'])
        else:
            unlinks_layer = ''
        # prepare analysis layers
        if settings['weight']:
            weight_by = settings['weightBy']
        else:
            weight_by = ''
        # look for user defined ID
        if settings['id']:
            axial_id = settings['id']
        else:
            axial_id = lfh.getIdField(axial_layer)
        # prepare map and unlinks layers
        if settings['type'] in (0, 1):
            axial_data = self.prepare_axial_map(axial_layer, settings['type'], axial_id, weight_by, ',', True)
            if axial_data == '':
                self.showMessage("The axial layer is not ready for analysis: verify it first.", 'Info', lev=1, dur=5)
                return '', ''
            if unlinks_layer:
                unlinks_data = self.prepare_unlinks()
            else:
                unlinks_data = ''
        else:
            axial_data = self.prepare_segment_map(axial_layer, settings['type'], axial_id, weight_by, ',', True)
            unlinks_data = ''
        return axial_data, unlinks_data

    @staticmethod
    def get_prep_commands(settings):
        commands = []
        if settings['type'] == 0:
            commands.append(["-m", "MAPCONVERT",
                             "-co", "axial",
                             "-con", "Axial Map",
                             "-cir"])
        elif settings['type'] == 1:
            commands.append(["-m", "MAPCONVERT",
                             "-co", "axial",
                             "-con", "Axial Map",
                             "-coc"])
            commands.append(["-m", "MAPCONVERT",
                             "-co", "segment",
                             "-con", "Segment Map",
                             "-cir",
                             "-coc",
                             "-crsl", str(settings['stubs'])])
        elif settings['type'] == 2:
            commands.append(["-m", "MAPCONVERT",
                             "-co", "segment",
                             "-con", "Segment Map",
                             "-coc",
                             "-cir"])
        return commands

    def setup_analysis(self, layers, settings):
        self.prep_line_data, self.prep_unlink_data = self.get_line_data_csv(layers, settings)
        self.analysis_settings = settings
        if self.prep_line_data:
            return True
        return False

    def parse_radii(self, txt):
        radii = txt
        radii.lower()
        radii = radii.replace(' ', '')
        radii = radii.split(',')
        radii.sort()
        radii = list(set(radii))
        radii = ['n' if x == '0' else x for x in radii]
        for r in radii:
            if r != 'n' and not uf.isNumeric(r):
                return ''
        radii = ','.join(radii)
        return radii

    def start_analysis(self):
        depthmap_cli = DepthmapCLIEngine.get_depthmap_cli()

        line_data_file = tempfile.NamedTemporaryFile('w+t', suffix='.csv')
        line_data_file.write(self.prep_line_data)
        unlink_data_file = tempfile.NamedTemporaryFile('w+t', suffix='.csv')
        unlink_data_file.write(self.prep_unlink_data)
        self.analysis_graph_file = tempfile.NamedTemporaryFile('w+t', suffix='.graph')

        subprocess.check_output([depthmap_cli,
                                 "-f", line_data_file.name,
                                 "-o", self.analysis_graph_file.name,
                                 "-m", "IMPORT",
                                 "-it", "data"])
        line_data_file.close()
        unlink_data_file.close()

        prep_commands = DepthmapCLIEngine.get_prep_commands(self.analysis_settings)

        for prep_command in prep_commands:
            cli_command = [depthmap_cli,
                           "-f", self.analysis_graph_file.name,
                           "-o", self.analysis_graph_file.name]
            cli_command.extend(prep_command)
            subprocess.check_output(cli_command)
        command = DepthmapCLIEngine.get_analysis_command(self.analysis_settings)
        cli_command = [depthmap_cli,
                       "-f", self.analysis_graph_file.name,
                       "-o", self.analysis_graph_file.name,
                       "-p"]
        cli_command.extend(command)

        self.analysis_process = DepthmapCLIEngine.AnalysisThread(cli_command)
        self.analysis_process.start()

    def parse_progress(self, msg):
        # calculate percent done
        p = re.compile(".*?step:\\s?([0-9]+)\\s?/\\s?([0-9]+)\\s?record:\\s?([0-9]+)\\s?/\\s?([0-9]+).*?")
        # p = re.compile(".*?step\\s?([0-9]+)\\s?/\\s?([0-9]+)\\s?record:\\s?([0-9]+)\\s?/\\s?([0-9]+).*?")
        m = p.match(msg)
        # extract number of nodes
        if m:
            # string matches
            self.analysis_nodes = int(m.group(4))
            if self.analysis_nodes > 0:
                prog = int(m.group(3))
                step = int(m.group(1))
                relprog = (float(prog) / float(self.analysis_nodes)) * 100
                return step, relprog
        return None, None

    class AnalysisThread(threading.Thread):
        def __init__(self, cmd):
            self.cmd = cmd
            self.p = None
            self.current_line = ''
            threading.Thread.__init__(self)

        def run(self):
            self.p = subprocess.Popen(self.cmd,
                                      stdout=subprocess.PIPE,
                                      stderr=subprocess.PIPE)
            while True:
                self.current_line = self.p.stdout.readline()
                if not self.current_line:
                    break
            self.p.stdout.close()

    def get_progress(self, settings, datastore):
        rc = self.analysis_process.p.poll()
        if rc is None:
            # process still running
            # read the last line from it...
            output = self.analysis_process.current_line
            prg = self.parse_progress(str(output))
            return prg
        elif rc == 0:
            # process exited normally
            export_data_file = tempfile.NamedTemporaryFile('w+t', suffix='.csv')
            export_command = DepthmapCLIEngine.get_export_command()
            cli_command = [DepthmapCLIEngine.get_depthmap_cli(),
                           "-f", self.analysis_graph_file.name,
                           "-o", export_data_file.name]
            cli_command.extend(export_command)
            subprocess.check_output(cli_command)

            attributes, values = self.parse_result_file(export_data_file.name)
            export_data_file.close()

            self.analysis_results = DepthmapEngine.process_analysis_result(settings, datastore,
                                                                           attributes, values)
            return 0, 100
        return None, None

    def cleanup(self):
        if os.path.isfile(self.analysis_graph_file.name):
            self.analysis_graph_file.close()

    @staticmethod
    def get_analysis_command(settings):
        if settings['weight']:
            weight_by = settings['weightBy']
        else:
            weight_by = ''
        # get radius values
        radii = settings['rvalues']
        #
        # prepare analysis user settings
        command = []
        # axial analysis settings
        if settings['type'] == 0:
            command.extend(["-m", "AXIAL"])
            command.extend(["-xa", str(radii)])
            if settings['betweenness'] == 1:
                command.append("-xac")
            if settings['fullset'] == 1:
                command.extend(["-xal", "-xar"])
            if weight_by != '':
                command.extend(["-xaw", settings['weightBy'].title()])
            # if unlinks_data != '':
            #     command += "acp.unlinkid:-1\n"
            #     command += "acp.unlinks:" + str(unlinks_data) + "\n"

        # 1: segment analysis settings with segmentation and unlinks
        # 2: segment analysis settings, data only
        elif settings['type'] in (1, 2):
            command.extend(["-m", "SEGMENT"])
            # command += "segment.stubs:" + str(settings['stubs']) + "\n"
            if settings['betweenness'] == 1:
                command.append("-sic")
            command.extend(["-st", "tulip"])
            command.extend(["-stb", "1024"])
            if settings['radius'] == 0:
                command.extend(["-srt", "steps"])
            elif settings['radius'] == 1:
                command.extend(["-srt", "angular"])
            elif settings['radius'] == 2:
                command.extend(["-srt", "metric"])
            else:
                raise BadInputError("Unknown radius type " + settings['radius'])

            command.extend(["-sr", str(radii)])
            if weight_by != '':
                command.extend(["-swa", settings['weightBy'].title()])
            # if unlinks_data != '':
            #     command += "acp.unlinkid:-1\n"
            #     command += "acp.unlinks:" + str(unlinks_data) + "\n"

        return command

    @staticmethod
    def get_export_command():
        return ["-m", "EXPORT",
                "-em", "shapegraph-map-csv"]
