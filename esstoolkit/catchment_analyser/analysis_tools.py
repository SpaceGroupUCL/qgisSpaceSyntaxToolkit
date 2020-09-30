# -*- coding: utf-8 -*-

# Space Syntax Toolkit
# Set of tools for essential space syntax network analysis and results exploration
# -------------------
# begin                : 2016-05-19
# copyright            : (C) 2016 by Space Syntax Limited
# author               : Laurens Versluis
# email                : l.versluis@spacesyntax.com
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.

""" Network based catchment analysis
"""

from __future__ import print_function

import math
import os.path
from builtins import object
from builtins import range
from builtins import str

from qgis.PyQt.QtCore import QSettings
from qgis.analysis import QgsNetworkSpeedStrategy
from qgis.core import (QgsGeometry, QgsPoint)


# check: https://gis.stackexchange.com/questions/220116/properter-to-get-travel-time-as-cost-for-network-analysis
class SpeedFieldProperter(QgsNetworkSpeedStrategy):
    """
    (attributeIndex, defaultSpeed=2.71828, speedToDistanceFactor = 1000)
    SpeedProperter to factor in speed and distance to edge tavel time cost
    @attributeIndex - find it out through attributeIndex = your_layer.fieldNameIndex('the_name_of_the_layercolumn')
    @defaultSpeed - not used here
    @speedToDistanceFactor - factor to adjust speed units (e.g. km/h) to distance units (e.g. meters)
    if the speed attribute is in km/h and distance in meters, this should equal 1000
    """

    def __init__(self, attributeIndex, defaultSpeed=50, speedToDistanceFactor=1000):
        QgsNetworkSpeedStrategy.__init__(self)
        self.AttributeIndex = attributeIndex
        self.DefaultSpeed = defaultSpeed
        self.SpeedToDistanceFactor = speedToDistanceFactor

    def property(self, distance, Feature):
        """
        returns the cost of the edge. In this case travel time.
        """
        attrs = Feature.attributes()
        speed = attrs[self.AttributeIndex]
        travel_time = distance / (speed * self.SpeedToDistanceFactor)
        return travel_time

    def requiredAttributes(self):
        """
        returns list of indices of feature attributes
        needed for cost calculation in property()
        """
        return [self.AttributeIndex]


class CustomCost(QgsNetworkSpeedStrategy):
    def __init__(self, costColumIndex, defaultValue):
        QgsNetworkSpeedStrategy.__init__(self)
        self.cost_column_index = costColumIndex
        self.default_value = defaultValue

    def property(self, distance, feature):
        cost = float(feature.attributes()[self.cost_column_index])
        if not cost or cost <= 0.0:
            return self.default_value
        else:
            return cost

    def requiredAttributes(self):
        return [self.cost_column_index]


class ConcaveHull(object):
    def clean_list(self, list_of_points):
        """
        Deletes duplicate points in list_of_points
        """
        return list(set(list_of_points))

    def length(self, vector):
        """
        Returns the number of elements in vector
        """
        return len(vector)

    def find_min_y_point(self, list_of_points):
        """
        Returns that point of *list_of_points* having minimal y-coordinate
        :param list_of_points: list of tuples
        :return: tuple (x, y)
        """
        min_y_pt = list_of_points[0]
        for point in list_of_points[1:]:
            if point[1] < min_y_pt[1] or (point[1] == min_y_pt[1] and point[0] < min_y_pt[0]):
                min_y_pt = point
        return min_y_pt

    def add_point(self, vector, element):
        """
        Returns vector with the given element append to the right
        """
        vector.append(element)
        return vector

    def remove_point(self, vector, element):
        """
        Returns a copy of vector without the given element
        """
        vector.pop(vector.index(element))
        return vector

    def euclidian_distance(self, point1, point2):
        """
        Returns the euclidian distance of the 2 given points.
        :param point1: tuple (x, y)
        :param point2: tuple (x, y)
        :return: float
        """
        return math.sqrt(math.pow(point1[0] - point2[0], 2) + math.pow(point1[1] - point2[1], 2))

    def nearest_points(self, list_of_points, point, k):
        # build a list of tuples of distances between point *point* and every point in *list_of_points*, and
        # their respective index of list *list_of_distances*
        list_of_distances = []
        for index in range(len(list_of_points)):
            list_of_distances.append((self.euclidian_distance(list_of_points[index], point), index))

        # sort distances in ascending order
        list_of_distances.sort()

        # get the k nearest neighbors of point
        nearest_list = []
        for index in range(min(k, len(list_of_points))):
            nearest_list.append((list_of_points[list_of_distances[index][1]]))
        return nearest_list

    def angle(self, from_point, to_point):
        """
        Returns the angle of the directed line segment, going from *from_point* to *to_point*, in radians. The angle is
        positive for segments with upward direction (north), otherwise negative (south). Values ranges from 0 at the
        right (east) to pi at the left side (west).
        :param from_point: tuple (x, y)
        :param to_point: tuple (x, y)
        :return: float
        """
        return math.atan2(to_point[1] - from_point[1], to_point[0] - from_point[0])

    def angle_difference(self, angle1, angle2):
        """
        Calculates the difference between the given angles in clockwise direction as radians.
        :param angle1: float
        :param angle2: float
        :return: float; between 0 and 2*Pi
        """
        try:
            if (angle1 > 0 and angle2 >= 0) and angle1 > angle2:
                return abs(angle1 - angle2)
            elif (angle1 >= 0 and angle2 > 0) and angle1 < angle2:
                return 2 * math.pi + angle1 - angle2
            elif (angle1 < 0 and angle2 <= 0) and angle1 < angle2:
                return 2 * math.pi + angle1 + abs(angle2)
            elif (angle1 <= 0 and angle2 < 0) and angle1 > angle2:
                return abs(angle1 - angle2)
            elif angle1 <= 0 < angle2:
                return 2 * math.pi + angle1 - angle2
            elif angle1 >= 0 >= angle2:
                return angle1 + abs(angle2)
            else:
                return 0
        except:
            print(('fail %s, %s', angle1, angle2))
            return 0

    def intersect(self, line1, line2):
        """
        Returns True if the two given line segments intersect each other, and False otherwise.
        :param line1: 2-tuple of tuple (x, y)
        :param line2: 2-tuple of tuple (x, y)
        :return: boolean
        """
        a1 = line1[1][1] - line1[0][1]
        b1 = line1[0][0] - line1[1][0]
        c1 = a1 * line1[0][0] + b1 * line1[0][1]
        a2 = line2[1][1] - line2[0][1]
        b2 = line2[0][0] - line2[1][0]
        c2 = a2 * line2[0][0] + b2 * line2[0][1]
        tmp = (a1 * b2 - a2 * b1)
        if tmp == 0:
            return False
        sx = (c1 * b2 - c2 * b1) / tmp
        if (sx > line1[0][0] and sx > line1[1][0]) or (sx > line2[0][0] and sx > line2[1][0]) or \
                (sx < line1[0][0] and sx < line1[1][0]) or (sx < line2[0][0] and sx < line2[1][0]):
            return False
        sy = (a1 * c2 - a2 * c1) / tmp
        if (sy > line1[0][1] and sy > line1[1][1]) or (sy > line2[0][1] and sy > line2[1][1]) or \
                (sy < line1[0][1] and sy < line1[1][1]) or (sy < line2[0][1] and sy < line2[1][1]):
            return False
        return True

    def point_in_polygon_q(self, point, list_of_points):
        """
        Return True if given point *point* is laying in the polygon described by the vertices *list_of_points*,
        otherwise False
        Based on the "Ray Casting Method" described by Joel Lawhead in this blog article:
        http://geospatialpython.com/2011/01/point-in-polygon.html
        """
        x = point[0]
        y = point[1]
        poly = [(pt[0], pt[1]) for pt in list_of_points]
        n = len(poly)
        inside = False

        p1x, p1y = poly[0]
        for i in range(n + 1):
            p2x, p2y = poly[i % n]
            if y > min(p1y, p2y):
                if y <= max(p1y, p2y):
                    if x <= max(p1x, p2x):
                        if p1y != p2y:
                            xints = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                        if p1x == p2x or x <= xints:
                            inside = not inside
            p1x, p1y = p2x, p2y

        return inside

    def write_wkt(self, point_list, file_name):
        """
        Writes the geometry described by *point_list* in Well Known Text format to file
        :param point_list: list of tuples (x, y)
        :param file_name: file name to write to
        :return: None
        """
        if file_name is None:
            file_name = 'hull2.wkt'
        if os.path.isfile(file_name):
            outfile = open(file_name, 'a')
        else:
            outfile = open(file_name, 'w')
            outfile.write('%s\n' % 'WKT')
        wkt = 'POLYGON((' + str(point_list[0][0]) + ' ' + str(point_list[0][1])
        for p in point_list[1:]:
            wkt += ', ' + str(p[0]) + ' ' + str(p[1])
        wkt += '))'
        outfile.write('%s\n' % wkt)
        outfile.close()
        return None

    def as_wkt(self, point_list):
        """
        Returns the geometry described by *point_list* in Well Known Text format

        Example: hull = self.as_wkt(the_hull)
                 feature.setGeometry(QgsGeometry.fromWkt(hull))

        Parameters
        ----------
        point_list : array_like
            list of tuples (x, y)

        Returns
        -------
        vl : `str`
            polygon geometry as WTK

        """

        wkt = 'POLYGON((' + str(point_list[0][0]) + ' ' + str(point_list[0][1])
        for p in point_list[1:]:
            wkt += ', ' + str(p[0]) + ' ' + str(p[1])
        wkt += '))'
        return wkt

    def as_polygon(self, point_list):
        """
        Returns the geometry described by *point_list* in as QgsGeometry

        Example: hull = self.as_wkt(the_hull)
                 feature.setGeometry(QgsGeometry.fromWkt(hull))

        Parameters
        ----------
        point_list : array_like
            list of tuples (x, y)

        Returns
        -------
        vl : `QgsGeometry`
            polygon geometry as QgsGeometry

        """
        # create a list of QgsPoint() from list of point coordinate strings in *point_list*
        points = [QgsPoint(point[0], point[1]) for point in point_list]
        # create the polygon geometry from list of point geometries
        poly = QgsGeometry.fromPolygon([points])
        return poly

    def enable_use_of_global_CRS(self):
        """
        Set new layers to use the project CRS.
        Code snipped taken from http://pyqgis.blogspot.co.nz/2012/10/basics-automatic-use-of-crs-for-new.html
        Example: old_behaviour = enable_use_of_global_CRS()
        :return: string
        """
        settings = QSettings()
        old_behaviour = settings.value('/Projections/defaultBehaviour')
        settings.setValue('/Projections/defaultBehaviour', 'useProject')
        return old_behaviour

    def disable_use_of_global_CRS(self, default_behaviour='prompt'):
        """
        Enables old settings again. If argument is missing then set behaviour to prompt.
        Example: disable_use_of_global_CRS(old_behaviour)
        :param default_behaviour:
        :return: None
        """
        settings = QSettings()
        settings.setValue('/Projections/defaultBehaviour', default_behaviour)
        return None

    def extract_points(self, geom):
        """
        Generate list of QgsPoints from QgsGeometry *geom* ( can be point, line, or polygon )
        Code taken from fTools plugin
        :param geom: an arbitrary geometry feature
        :return: list of points
        """
        temp_geom = []
        # point geometry
        if geom.type() == 0:
            if geom.isMultipart():
                temp_geom = geom.asMultiPoint()
            else:
                temp_geom.append(geom.asPoint())
        # line geometry
        if geom.type() == 1:
            # if multipart feature explode to single part
            if geom.isMultipart():
                multi_geom = geom.asMultiPolyline()
                for i in multi_geom:
                    temp_geom.extend(i)
            else:
                temp_geom = geom.asPolyline()
        # polygon geometry
        elif geom.type() == 2:
            # if multipart feature explode to single part
            if geom.isMultipart():
                multi_geom = geom.asMultiPolygon()
                # now single part polygons
                for i in multi_geom:
                    # explode to line segments
                    for j in i:
                        temp_geom.extend(j)
            else:
                multi_geom = geom.asPolygon()
                # explode to line segments
                for i in multi_geom:
                    temp_geom.extend(i)
        return temp_geom

    def sort_by_angle(self, list_of_points, last_point, last_angle):
        def getkey(item):
            return self.angle_difference(last_angle, self.angle(last_point, item))

        vertex_list = sorted(list_of_points, key=getkey, reverse=True)
        return vertex_list

    def concave_hull(self, points_list, k):
        """
        Calculates a valid concave hull polygon containing all given points. The algorithm searches for that
        point in the neighborhood of k nearest neighbors which maximizes the rotation angle in clockwise direction
        without intersecting any previous line segments.
        This is an implementation of the algorithm described by Adriano Moreira and Maribel Yasmina Santos:
        CONCAVE HULL: A K-NEAREST NEIGHBOURS APPROACH FOR THE COMPUTATION OF THE REGION OCCUPIED BY A SET OF POINTS.
        GRAPP 2007 - International Conference on Computer Graphics Theory and Applications; pp 61-68.
        :param points_list: list of tuples (x, y)
        :param k: integer
        :return: list of tuples (x, y)
        """
        # return an empty list if not enough points are given
        if k > len(points_list):
            return None

        # the number of nearest neighbors k must be greater than or equal to 3
        # kk = max(k, 3)
        kk = max(k, 2)

        # delete duplicate points
        point_set = self.clean_list(points_list)

        # if point_set has less then 3 points no polygon can be created and an empty list will be returned
        if len(point_set) < 3:
            return None

        # if point_set has 3 points then these are already vertices of the hull. Append the first point to
        # close the hull polygon
        if len(point_set) == 3:
            return self.add_point(point_set, point_set[0])

        # make sure that k neighbours can be found
        kk = min(kk, len(point_set))

        # start with the point having the smallest y-coordinate (most southern point)
        first_point = self.find_min_y_point(point_set)

        # add this points as the first vertex of the hull
        hull = [first_point]

        # make the first vertex of the hull to the current point
        current_point = first_point

        # remove the point from the point_set, to prevent him being among the nearest points
        point_set = self.remove_point(point_set, first_point)
        previous_angle = math.pi

        # step counts the number of segments
        step = 2

        # as long as point_set is not empty or search is returning to the starting point # use of step is unclear!
        while ((current_point != first_point) or (step == 2)) and (len(point_set) > 0):

            # after 3 iterations add the first point to point_set again, otherwise a hull cannot be closed
            if step == 5:
                point_set = self.add_point(point_set, first_point)

            # search the k nearest neighbors of the current point
            k_nearest_points = self.nearest_points(point_set, current_point, kk)

            # sort the candidates (neighbors) in descending order of right-hand turn. This way the algorithm progresses
            # in clockwise direction through as many points as possible
            c_points = self.sort_by_angle(k_nearest_points, current_point, previous_angle)

            its = True
            i = -1

            # search for the nearest point to which the connecting line does not intersect any existing segment
            while its is True and (i < len(c_points) - 1):
                i += 1
                if c_points[i] == first_point:
                    last_point = 1
                else:
                    last_point = 0
                j = 2
                its = False

                while its is False and (j < len(hull) - last_point):
                    its = self.intersect((hull[step - 2], c_points[i]), (hull[step - 2 - j], hull[step - 1 - j]))
                    j += 1

            # there is no candidate to which the connecting line does not intersect any existing segment, so the
            # for the next candidate fails. The algorithm starts again with an increased number of neighbors
            if its is True:
                # this tries to remove the potentially problematic recursion. might give less optimal results
                # point_set = self.remove_point(point_set, current_point)
                # continue
                return self.concave_hull(points_list, kk + 1)

            # the first point which complies with the requirements is added to the hull and gets the current point
            current_point = c_points[i]
            hull = self.add_point(hull, current_point)

            # calculate the angle between the last vertex and his precursor, that is the last segment of the hull
            # in reversed direction
            previous_angle = self.angle(hull[step - 1], hull[step - 2])

            # remove current_point from point_set
            point_set = self.remove_point(point_set, current_point)

            # increment counter
            step += 1

        all_inside = True
        i = len(point_set) - 1

        # check if all points are within the created polygon
        while (all_inside is True) and (i >= 0):
            all_inside = self.point_in_polygon_q(point_set[i], hull)
            i -= 1

        # since at least one point is out of the computed polygon, try again with a higher number of neighbors
        if all_inside is False:
            return self.concave_hull(points_list, kk + 1)

        # a valid hull has been constructed
        return hull
