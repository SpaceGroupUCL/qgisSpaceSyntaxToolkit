import math

from qgis.PyQt.QtCore import QVariant
from qgis.core import (NULL)

from esstoolkit.analysis.AnalysisEngine import AnalysisEngine
from esstoolkit.utilities import layer_field_helpers as lfh, utility_functions as uf


class DepthmapEngine:
    def __init__(self):
        self.axial_default = ('Connectivity', 'Id', 'Line Length')
        self.segment_default = ('Angular Connectivity', 'Axial Connectivity', 'Axial Id',
                                'Axial Line Length', 'Axial Line Ref', 'Connectivity', 'Segment Length')
        self.rcl_default = ('Angular Connectivity', 'Axial Line Ref', 'Connectivity', 'Id', 'Segment Length')

    def prepare_axial_map(self, axial_layer, map_type, ref='', weight='', sep='\t', include_header=False):
        try:
            features = axial_layer.getFeatures()
            defaults = [""]
            if map_type == 0:
                defaults.extend(self.axial_default)
            elif map_type == 1:
                defaults.extend(self.segment_default)
            # I leave all the if clauses outside the for loop to gain some speed
            map_data = ''
            if include_header:
                map_data = 'Ref,x1,y1,x2,y2'
                if weight not in defaults:
                    map_data += weight
                map_data += "\n"
            if ref != '':
                if weight not in defaults:
                    for f in features:
                        map_data += str(f.attribute(ref)) + sep
                        map_data += str(f.geometry().vertexAt(0).x()) + sep + \
                                    str(f.geometry().vertexAt(0).y()) + sep
                        map_data += str(f.geometry().vertexAt(1).x()) + sep + \
                                    str(f.geometry().vertexAt(1).y()) + sep
                        map_data += str(f.attribute(weight)) + "\n"
                else:
                    for f in features:
                        map_data += str(f.attribute(ref)) + sep
                        map_data += str(f.geometry().vertexAt(0).x()) + sep + \
                                    str(f.geometry().vertexAt(0).y()) + sep
                        map_data += str(f.geometry().vertexAt(1).x()) + sep + \
                                    str(f.geometry().vertexAt(1).y()) + "\n"
            else:
                if weight not in defaults:
                    for f in features:
                        map_data += str(f.id()) + sep
                        map_data += str(f.geometry().vertexAt(0).x()) + sep + \
                                    str(f.geometry().vertexAt(0).y()) + sep
                        map_data += str(f.geometry().vertexAt(1).x()) + sep + \
                                    str(f.geometry().vertexAt(1).y()) + sep
                        map_data += str(f.attribute(weight)) + "\n"
                else:
                    for f in features:
                        map_data += str(f.id()) + sep
                        map_data += str(f.geometry().vertexAt(0).x()) + sep + \
                                    str(f.geometry().vertexAt(0).y()) + sep
                        map_data += str(f.geometry().vertexAt(1).x()) + sep + \
                                    str(f.geometry().vertexAt(1).y()) + "\n"
            return map_data
        except:
            raise AnalysisEngine.AnalysisEngineError("Exporting axial map failed.")

    def prepare_segment_map(self, axial_layer, map_type, ref='', weight='', sep='\t', include_header=False):
        try:
            features = axial_layer.getFeatures()
            defaults = [""]
            if map_type == 0:
                defaults.extend(self.axial_default)
            elif map_type == 1:
                defaults.extend(self.segment_default)
            elif map_type == 2:
                defaults.extend(self.rcl_default)
            # I leave all the if clauses outside the for loop to gain some speed
            map_data = ''
            if include_header:
                map_data = 'Ref,x1,y1,x2,y2'
                if weight not in defaults:
                    map_data += weight
                map_data += "\n"
            if ref != '':
                if weight not in defaults:
                    for f in features:
                        nr = 0
                        while f.geometry().vertexIdFromVertexNr(nr + 1)[0]:
                            map_data += str(f.attribute(ref)) + sep
                            map_data += str(f.geometry().vertexAt(nr).x()) + sep + \
                                        str(f.geometry().vertexAt(nr).y()) + sep
                            map_data += str(f.geometry().vertexAt(nr + 1).x()) + sep + \
                                        str(f.geometry().vertexAt(nr + 1).y()) + sep
                            map_data += str(f.attribute(weight)) + "\n"
                            nr += 1
                else:
                    for f in features:
                        nr = 0
                        while f.geometry().vertexIdFromVertexNr(nr + 1)[0]:
                            map_data += str(f.attribute(ref)) + sep
                            map_data += str(f.geometry().vertexAt(nr).x()) + sep + \
                                        str(f.geometry().vertexAt(nr).y()) + sep
                            map_data += str(f.geometry().vertexAt(nr + 1).x()) + sep + \
                                        str(f.geometry().vertexAt(nr + 1).y()) + "\n"
                            nr += 1
            else:
                if weight not in defaults:
                    for f in features:
                        nr = 0
                        while f.geometry().vertexIdFromVertexNr(nr + 1)[0]:
                            map_data += str(f.id()) + sep
                            map_data += str(f.geometry().vertexAt(nr).x()) + sep + \
                                        str(f.geometry().vertexAt(nr).y()) + sep
                            map_data += str(f.geometry().vertexAt(nr + 1).x()) + sep + \
                                        str(f.geometry().vertexAt(nr + 1).y()) + sep
                            map_data += str(f.attribute(weight)) + "\n"
                            nr += 1
                else:
                    for f in features:
                        nr = 0
                        while f.geometry().vertexIdFromVertexNr(nr + 1)[0]:
                            map_data += str(f.id()) + sep
                            map_data += str(f.geometry().vertexAt(nr).x()) + sep + \
                                        str(f.geometry().vertexAt(nr).y()) + sep
                            map_data += str(f.geometry().vertexAt(nr + 1).x()) + sep + \
                                        str(f.geometry().vertexAt(nr + 1).y()) + "\n"
                            nr += 1
            return map_data
        except Exception as e:
            raise AnalysisEngine.AnalysisEngineError("Exporting segment map failed.")

    def prepare_unlinks(self, axial_layer, unlinks_layer, axial_id, use_coords=False,
                        sep=",", linesep=";", include_header=False):
        unlinks_data = ''
        # check if unlinks layer is valid
        if not lfh.fieldExists(unlinks_layer, 'line1') or not lfh.fieldExists(unlinks_layer, 'line2'):
            raise AnalysisEngine.AnalysisEngineError("Unlinks layer not ready for analysis: update and verify first.")
            return unlinks_data
        elif lfh.fieldHasNullValues(unlinks_layer, 'line1') or lfh.fieldHasNullValues(unlinks_layer, 'line2'):
            raise AnalysisEngine.AnalysisEngineError("Unlinks layer not ready for analysis: update and verify first.")
            return unlinks_data
        # get axial ids
        axialids, ids = lfh.getFieldValues(axial_layer, axial_id)
        if include_header:
            unlinks_data = 'x' + sep + 'y' + linesep
        # assign row number by id
        try:
            features = unlinks_layer.getFeatures()
            for f in features:
                if use_coords:
                    row1 = f.geometry().asPoint().x()
                    row2 = f.geometry().asPoint().y()
                else:
                    row1 = axialids.index(f.attribute('line1'))
                    row2 = axialids.index(f.attribute('line2'))
                unlinks_data += str(row1) + sep + str(row2) + linesep
        except Exception as e:
            raise AnalysisEngine.AnalysisEngineError("Exporting unlinks failed: " + str(e))
        if unlinks_data != '':
            unlinks_data = unlinks_data[:-1]
        return unlinks_data

    @staticmethod
    def fix_depthmap_names(names):
        # proper conversion makes short version based on real name
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
        # using simple dict / string operations
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

    @staticmethod
    def parse_radii(txt):
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

    @staticmethod
    def process_analysis_result(settings, datastore, attributes, values):
        if not attributes:
            return AnalysisEngine.AnalysisResults(None, None, None, None)
        if not values:
            return AnalysisEngine.AnalysisResults(attributes, None, None, None)
        # Process the attributes, renaming them and selecting only relevant ones
        exclusions = []
        # keep only most important attributes
        if settings['fullset'] == 0:
            exclusions = DepthmapEngine.exclude_depthmap_results(attributes)
            # remove HH suffix from integration measure
            attributes = [x.replace(" [HH]", "") for x in attributes]
        # remove weight attribute if duplicate
        if settings['weight']:
            weight_by = settings['weightBy'].title() + ' 1'
            if weight_by.title() in attributes:
                exclusions.append(attributes.index(weight_by.title()))
            # also remove the invalid "Axial Segment Length" attribute
            if "Axial Segment Length" in attributes:
                exclusions.append(attributes.index("Axial Segment Length"))
        # replace axial line ref
        if "Axial Line Ref" in attributes:
            idx = attributes.index("Axial Line Ref")
            if settings['type'] == 2:
                exclusions.append(idx)
            else:
                attributes[idx] = "Axial Ref"
        # replace id by something more explicit about the source
        if "Id" in attributes:
            idx = attributes.index("Id")
            if settings['type'] == 2:
                # this is for the id of the user's submitted segment/rcl data
                attributes[idx] = "Segment Id"
            elif settings['type'] == 1:
                # this is for the id of the user's submitted axial data
                attributes[idx] = "Axial Id"
            else:
                # this is the original id of the user's submitted axial data
                #    attributes[idx] = self.axial_id
                # does not keep the user's original id as it can clash with new attribute names
                attributes[idx] = "Axial Id"

        # remove attributes and values from lists
        if len(exclusions) > 0:
            exclusions.sort(reverse=True)
            values = list(zip(*values))
            for i in exclusions:
                attributes.pop(i)
                values.pop(i)
            values = list(zip(*values))
        # remove spaces
        attributes = [x.replace(" ", "_") for x in attributes]
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
        if settings['type'] in (1, 2) and settings['newnorm'] == 1:
            new_attributes, values = DepthmapEngine.calculate_normalised_segment(attributes, values)
            attributes.extend(new_attributes)
            new_types = [QVariant.Double] * len(new_attributes)
            types.extend(new_types)
        # the attribute names must be fixed
        if datastore['type'] == 0:
            # when working with shape files
            attributes = DepthmapEngine.fix_depthmap_names(attributes)
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
        return AnalysisEngine.AnalysisResults(attributes, types, values, coords)

    @staticmethod
    def exclude_depthmap_results(attributes):
        # list of attributes to exclude
        exclusion_list = ['[Norm]', 'Controllability', 'Entropy', 'Harmonic', '[P-value]', '[Tekl]', 'Intensity']
        attributes_to_remove = []
        for i, attr in enumerate(attributes):
            if any(substring in attr for substring in exclusion_list):
                attributes_to_remove.append(i)
        return attributes_to_remove

    @staticmethod
    def calculate_normalised_segment(attributes, values):
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
        # attributes.extend(new_attributes)
        # calculate new values
        all_values = []
        for feat in values:
            feat = list(feat)
            calc_values = []
            for i, j in enumerate(choice):
                try:
                    val = math.log(float(feat[j]) + 1.0) / math.log(float(feat[td[i]]) + 3.0)
                    calc_values.append(val)
                except:
                    calc_values.append(NULL)
            for i, j in enumerate(td):
                try:
                    if i < len(nc):
                        val = (float(feat[nc[i]]) ** 1.2) / (float(feat[j]) + 2.0)
                    else:
                        val = (float(feat[nc[i - len(nc)]]) ** 1.2) / (float(feat[j]) + 2.0)
                    calc_values.append(val)
                except:
                    calc_values.append(NULL)
            feat.extend(calc_values)
            all_values.append(feat)
        return new_attributes, all_values
