# general imports
from qgis.PyQt.QtCore import QObject


class sEdge(QObject):
    def __init__(self, id, feature, nodes):
        QObject.__init__(self)
        self.id = id
        self.feature = feature
        self.nodes = nodes

        # TODO: only for catchment
        # self.visited = {}
        # self.agg_cost = {}
        # self.len = self.feature.geometry().length()

    def get_startnode(self):
        return self.nodes[0]

    def get_endnode(self):
        return self.nodes[1]

    def replace_start(self, id, point):
        self.nodes[0] = id
        geometry = self.feature.geometry()
        geometry.moveVertex(point.x(), point.y(), 0)
        self.feature.setGeometry(geometry)
        return

    def replace_end(self, id, point):
        self.nodes[1] = id
        geometry = self.feature.geometry()
        geometry.moveVertex(point.x(), point.y(), len(self.feature.geometry().asPolyline()) - 1)
        self.feature.setGeometry(geometry)
        return
