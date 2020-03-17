# general imports
import itertools
from PyQt4.QtCore import QObject, pyqtSignal, QVariant
from qgis.core import QgsGeometry, QgsSpatialIndex, QgsFields, QgsField, QgsFeature, QgsMessageLog
from collections import defaultdict

# plugin module imports
try:
    from utilityFunctions import *
    from sNode import sNode
    from sEdge import sEdge
except ImportError:
    pass

# special cases:
# SELF LOOPS
#   - topology of self loop node would include itself
# DUPLICATE
#   - topology of n1 would include n2 many times

# TODO: change based on adding and deleteting features
# always use clean_feature_iterators in the outputs

unlink_feat = QgsFeature()
unlink_flds = QgsFields()
unlink_flds.append(QgsField('id', QVariant.Int))
unlink_feat.setFields(unlink_flds)

error_feat = QgsFeature()
error_flds = QgsFields()
error_flds.append(QgsField('error_type', QVariant.String))
error_feat.setFields(error_flds)


class sGraph(QObject):

    finished = pyqtSignal(object)
    error = pyqtSignal(Exception, basestring)
    progress = pyqtSignal(float)
    warning = pyqtSignal(str)
    killed = pyqtSignal(bool)

    def __init__(self, edges={}, nodes={}):
        QObject.__init__(self)
        self.sEdges = edges
        self.sNodes = nodes # can be empty
        self.total_progress = 0
        self.step = 0

        if len(self.sEdges) == 0:
            self.edge_id = 0
            self.sNodesCoords = {}
            self.node_id = 0
        else:
            self.edge_id = max(self.sEdges.keys())
            self.node_id = max(self.sNodes.keys())
            self.sNodesCoords = {snode.getCoords(): snode.id for snode in self.sNodes.values()}

        self.edgeSpIndex = QgsSpatialIndex()
        self.ndSpIndex = QgsSpatialIndex()
        res = map(lambda sedge: self.edgeSpIndex.insertFeature(sedge.feature), self.sEdges.values())
        del res

        self.errors = []
        # breakages, orphans, merges, snaps, duplicate, points, mlparts
        self.unlinks = []
        self.points = []
        self.multiparts = []

    # graph from feat iter
    # updates the id
    def load_edges(self, feat_iter, angle_threshold):

        for f in feat_iter:

            if self.killed is True:
                break

            # add edge
            geometry = f.geometry().simplify(angle_threshold)
            geometry_pl = geometry.asPolyline()
            startpoint = geometry_pl[0]
            endpoint = geometry_pl[-1]
            start = self.load_point(startpoint)
            end = self.load_point(endpoint)
            snodes = [start, end]
            self.edge_id += 1
            self.update_topology(snodes[0], snodes[1], self.edge_id)

            f.setFeatureId(self.edge_id)
            f.setGeometry(geometry)
            sedge = sEdge(self.edge_id, f, snodes)
            self.sEdges[self.edge_id] = sedge
            #self.edgeSpIndex.insertFeature(f)

        return

    # pseudo graph from feat iter (only clean features - ids are fixed)
    def load_edges_w_o_topology(self, clean_feat_iter):

        for f in clean_feat_iter:

            if self.killed is True:
                break

            self.total_progress += self.step
            self.progress.emit(self.total_progress)

            # add edge
            sedge = sEdge(f.id(), f, [])
            self.sEdges[f.id()] = sedge
            self.edgeSpIndex.insertFeature(f)

        self.edge_id = f.id()
        return

    # find existing or generate new node
    def load_point(self, point):
        try:
            node_id = self.sNodesCoords[(point[0], point[1])]
        except KeyError:
            self.node_id += 1
            node_id = self.node_id
            feature = QgsFeature()
            feature.setFeatureId(node_id)
            feature.setAttributes([node_id])
            feature.setGeometry(QgsGeometry.fromPoint(point))
            self.sNodesCoords[(point[0], point[1])] = node_id
            snode = sNode(node_id, feature, [], [])
            self.sNodes[self.node_id] = snode
        return node_id

    # store topology
    def update_topology(self, node1, node2, edge):
        self.sNodes[node1].topology.append(node2)
        self.sNodes[node1].adj_edges.append(edge)
        self.sNodes[node2].topology.append(node1)
        self.sNodes[node2].adj_edges.append(edge)
        return

    # delete point
    def delete_node(self, node_id):
        del self.sNodes[node_id]
        return True

    def remove_edge(self, nodes, e):
        self.sNodes[nodes[0]].adj_edges.remove(e)
        self.sNodes[nodes[0]].topology.remove(nodes[1])
        self.sNodes[nodes[1]].adj_edges.remove(e) # if self loop - removed twice
        self.sNodes[nodes[1]].topology.remove(nodes[0]) # if self loop - removed twice
        del self.sEdges[e]
        # spIndex self.edgeSpIndex.deleteFeature(self.sEdges[e].feature)
        return

    # create graph (broken_features_iter)
    # can be applied to edges w-o topology for speed purposes
    def break_features_iter(self, getUnlinks, angle_threshold, fix_unlinks=False):

        for sedge in self.sEdges.values():

            if self.killed is True:
                break

            self.total_progress += self.step
            self.progress.emit(self.total_progress)

            f = sedge.feature
            f_geom = f.geometry()
            pl = f_geom.asPolyline()
            lines = filter(lambda line: line != f.id(), self.edgeSpIndex.intersects(f_geom.boundingBox()))

            # self intersections
            # include first and last
            self_intersections = getSelfIntersections(pl)

            # common vertices
            intersections = list(itertools.chain.from_iterable(map(lambda line: set(pl[1:-1]).intersection(set(self.sEdges[line].feature.geometry().asPolyline())), lines)))
            intersections += self_intersections
            intersections = (set(intersections))

            if len(intersections) > 0:
                # broken features iterator
                # errors
                for pnt in intersections:
                    err_f = QgsFeature(error_feat)
                    err_f.setGeometry(QgsGeometry.fromPoint(pnt))
                    err_f.setAttributes(['broken'])
                    self.errors.append(err_f)
                vertices_indices = find_vertex_indices(pl, intersections)
                for start, end in zip(vertices_indices[:-1], vertices_indices[1:]):
                    broken_feat = QgsFeature(f)
                    broken_geom = QgsGeometry.fromPolyline(pl[start:end + 1]).simplify(angle_threshold)
                    broken_feat.setGeometry(broken_geom)
                    yield broken_feat
            else:
                simpl_geom = f.geometry().simplify(angle_threshold)
                f.setGeometry(simpl_geom)
                yield f

    def fix_unlinks(self):

        self.edgeSpIndex = QgsSpatialIndex()
        self.step = self.step / 2.0

        for e in self.sEdges.values():
            if self.killed is True:
                break

            self.total_progress += self.step
            self.progress.emit(self.total_progress)

            self.edgeSpIndex.insertFeature(e.feature)

        for sedge in self.sEdges.values():

            if self.killed is True:
                break

            self.total_progress += self.step
            self.progress.emit(self.total_progress)

            f = sedge.feature
            f_geom = f.geometry()
            pl = f_geom.asPolyline()
            lines = filter(lambda line: line!= f.id(), self.edgeSpIndex.intersects(f_geom.boundingBox()))
            lines = filter(lambda line: f_geom.crosses(self.sEdges[line].feature.geometry()), lines)
            for line in lines:
                crossing_points = f_geom.intersection(self.sEdges[line].feature.geometry())
                if crossing_points.geometry().wkbType() == 1:
                    if crossing_points.asPoint() in pl[1:-1]:
                        self.sEdges[sedge.id].feature.geometry().moveVertex(crossing_points.asPoint().x() + 1, crossing_points.asPoint().y() + 1, pl.index(crossing_points.asPoint()))
                elif crossing_points.geometry().wkbType() == 4:
                    for p in crossing_points.asMultiPoint():
                        if p in pl[1:-1]:
                            self.sEdges[sedge.id].feature.geometry().moveVertex(p.x() + 1,
                                                                            p.y() + 1,
                                                                            pl.index(p))
            # TODO: exclude vertices - might be in one of the lines

        return

    def con_comp_iter(self, group_dictionary):
        components_passed = set([])
        for id in group_dictionary.keys():

            self.total_progress += self.step
            self.progress.emit(self.total_progress)

            if {id}.isdisjoint(components_passed):
                group = [[id]]
                candidates = ['dummy', 'dummy']
                while len(candidates) > 0:
                    flat_group = group[:-1] + group[-1]
                    candidates = map(
                        lambda last_visited_node: set(group_dictionary[last_visited_node]).difference(set(flat_group)),
                        group[-1])
                    candidates = list(set(itertools.chain.from_iterable(candidates)))
                    group = flat_group + [candidates]
                    components_passed.update(set(candidates))
                yield group[:-1]

    # group points based on proximity - spatial index is not updated
    def snap_endpoints(self, snap_threshold):
        QgsMessageLog.logMessage('starting snapping', level=QgsMessageLog.CRITICAL)
        res = map(lambda snode: self.ndSpIndex.insertFeature(snode.feature), self.sNodes.values())
        filtered_nodes = {}
        # exclude nodes where connectivity = 2 - they will be merged
        self.step = self.step / float(2)
        for node in filter(lambda  n: n.adj_edges != 2, self.sNodes.values()):
            if self.killed is True:
                break

            self.total_progress += self.step
            self.progress.emit(self.total_progress)

            # find nodes within x distance
            node_geom = node.feature.geometry()
            nodes = filter(lambda nd: nd != node.id and node_geom.distance(self.sNodes[nd].feature.geometry()) <= snap_threshold,
                           self.ndSpIndex.intersects(node_geom.buffer(snap_threshold, 10).boundingBox()))
            if len(nodes) > 0:
                filtered_nodes[node.id] = nodes

        QgsMessageLog.logMessage('continuing snapping', level=QgsMessageLog.CRITICAL)
        self.step = (len(filtered_nodes) * self.step) / float(len(self.sNodes))
        for group in self.con_comp_iter(filtered_nodes):

            if self.killed is True:
                break

            self.total_progress += self.step
            self.progress.emit(self.total_progress)

            # find con_edges
            con_edges = set(itertools.chain.from_iterable([self.sNodes[node].adj_edges for node in group]))

            # collapse nodes to node
            merged_node_id, centroid_point = self.collapse_to_node(group)

            # update connected edges and their topology
            for edge in con_edges:
                sedge = self.sEdges[edge]
                start, end = sedge.nodes
                # if existing self loop
                if start == end: # and will be in group
                    if sedge.feature.geometry().length() <= snap_threshold: # short self-loop
                        self.remove_edge((start, end), edge)
                    else:
                        self.sEdges[edge].replace_start(self.node_id, centroid_point)
                        self.update_topology(merged_node_id, merged_node_id, edge)
                        self.sNodes[end].topology.remove(start)
                        self.sEdges[edge].replace_end(self.node_id, centroid_point)
                        self.sNodes[start].topology.remove(end)
                    # self.sNodes[start].topology.remove(end)
                # if becoming self loop (if one intermediate vertex - turns back on itself)
                elif start in group and end in group:
                    if (len(sedge.feature.geometry().asPolyline()) <= 3
                            or sedge.feature.geometry().length() <= snap_threshold):
                        self.remove_edge((start, end), edge)
                    else:
                        self.sEdges[edge].replace_start(self.node_id, centroid_point)
                        self.sEdges[edge].replace_end(self.node_id, centroid_point)
                        self.update_topology(merged_node_id, merged_node_id, edge)
                        self.sNodes[end].topology.remove(start)
                        self.sNodes[start].topology.remove(end)
                # if only start
                elif start in group:
                    self.sEdges[edge].replace_start(self.node_id, centroid_point)
                    self.sNodes[merged_node_id].topology.append(end)
                    self.sNodes[merged_node_id].adj_edges.append(edge)
                    self.sNodes[end].topology.append(merged_node_id)
                    self.sNodes[end].topology.remove(start)
                # if only end
                elif end in group:
                    self.sEdges[edge].replace_end(self.node_id, centroid_point)
                    self.sNodes[merged_node_id].topology.append(start)
                    self.sNodes[merged_node_id].adj_edges.append(edge)
                    self.sNodes[start].topology.append(merged_node_id)
                    self.sNodes[start].topology.remove(end)

            # errors
            for node in group:
                err_f = QgsFeature(error_feat)
                err_f.setGeometry(self.sNodes[node].feature.geometry())
                err_f.setAttributes(['snapped'])
                self.errors.append(err_f)

            # delete old nodes
            res = map(lambda item: self.delete_node(item), group)

        return

    def collapse_to_node(self, group):

        # create new node, coords
        self.node_id += 1
        feat = QgsFeature()
        centroid = (
            QgsGeometry.fromMultiPoint([self.sNodes[nd].feature.geometry().asPoint() for nd in group])).centroid()
        feat.setGeometry(centroid)
        feat.setAttributes([self.node_id])
        feat.setFeatureId(self.node_id)
        snode = sNode(self.node_id, feat, [], [])
        self.sNodes[self.node_id] = snode
        self.ndSpIndex.insertFeature(feat)

        return self.node_id, centroid.asPoint()

    # TODO add agg_cost
    def route_nodes(self, group, step):
        count = 1
        group = [group]
        while count <= step:
            last_visited = group[-1]
            group = group[:-1] + group[-1]
            con_nodes = set(itertools.chain.from_iterable([self.sNodes[last_node].topology for last_node in last_visited])).difference(group)
            group += [con_nodes]
            count += 1
            for nd in con_nodes:
                yield count - 1, nd

    def route_edges(self, group, step):
        count = 1
        group = [group]
        while count <= step:
            last_visited = group[-1]
            group = group[:-1] + group[-1]
            con_edges = set(
                itertools.chain.from_iterable([self.sNodes[last_node].topology for last_node in last_visited]))
            con_nodes = filter(lambda con_node: con_node not in group, con_nodes)
            group += [con_nodes]
            count += 1
            # TODO: return circles
            for dg in con_edges:
                yield count - 1, nd, dg

    # TODO: snap_geometries (not endpoints)
    # TODO: extend

    def clean_dupl(self, group_edges, snap_threshold, parallel=False):

        self.total_progress += self.step
        self.progress.emit(self.total_progress)

        # keep line with minimum length
        # TODO: add distance centroids
        lengths = [self.sEdges[e].feature.geometry().length() for e in group_edges]
        sorted_edges = [x for _, x in sorted(zip(lengths, group_edges))]
        min_len = min(lengths)

        #if parallel is False:
        prl_dist_threshold = 0
        #else:
        #    dist_threshold = snap_threshold
        for e in sorted_edges[1:]:
            # delete line
            if abs(self.sEdges[e].feature.geometry().length() - min_len) <= prl_dist_threshold:
                for p in set([self.sNodes[n].feature.geometry() for n in self.sEdges[e].nodes]):
                    err_f = QgsFeature(error_feat)
                    err_f.setGeometry(p)
                    err_f.setAttributes(['duplicate'])
                    self.errors.append(err_f)
                self.remove_edge(self.sEdges[e].nodes, e)
        return

    def clean_multipart(self, e):

        self.total_progress += self.step
        self.progress.emit(self.total_progress)

        # only used in the last cleaning iteration - only updates self.sEdges and spIndex (allowed to be used once in the end)
        # nodes are not added to the new edges

        for singlepart in e.feature.geometry().asMultiPolyline():

            # create new edge and update spIndex
            single_geom = QgsGeometry.fromPolyline(singlepart)
            single_feature = QgsFeature(e.feature)
            single_feature.setGeometry(single_geom)
            self.edge_id += 1
            single_feature.setFeatureId(self.edge_id)
            self.sEdges[self.edge_id] = sEdge(self.edge_id, single_feature, [])
            self.edgeSpIndex.insertFeature(single_feature)

            # add points as multipart errors
            for p in single_geom.asPolyline():
                err_f = QgsFeature(error_feat)
                err_f.setGeometry(QgsGeometry.fromPoint(p))
                err_f.setAttributes(['multipart'])
                self.errors.append(err_f)

        # delete old feature - spIndex

        self.edgeSpIndex.deleteFeature(self.sEdges[e.id].feature)
        del self.sEdges[e.id]

        return

    def clean_orphan(self, e):

        self.total_progress += self.step
        self.progress.emit(self.total_progress)

        nds = e.nodes
        snds = self.sNodes[nds[0]], self.sNodes[nds[1]]
        # connectivity of both endpoints 1
        # if parallel - A:[B,B]
        # if selfloop to line - A: [A,A, C]
        # if selfloop
        # if selfloop and parallel
        if len(set(snds[0].topology)) == len(set(snds[1].topology)) == 1 and len(set(snds[0].adj_edges)) == 1:
            del self.sEdges[e.id]
            for nd in set(nds):
                err_f = QgsFeature(error_feat)
                err_f.setGeometry(self.sNodes[nd].feature.geometry())
                err_f.setAttributes(['orphan'])
                self.errors.append(err_f)
                del self.sNodes[nd]
        return True

    # find duplicate geometries
    # find orphans

    def clean(self, duplicates, orphans, snap_threshold, closed_polylines, multiparts=False):
        # clean duplicates - delete longest from group using snap threshold
        step_original = float(self.step)
        if duplicates:
            input = [(e.id, frozenset(e.nodes)) for e in self.sEdges.values()]
            groups = defaultdict(list)
            for v, k in input: groups[k].append(v)

            dupl_candidates = dict(filter(lambda (nodes, edges): len(edges) > 1, groups.items()))

            self.step = (len(dupl_candidates) * self.step) / float(len(self.sEdges))
            for (nodes, group_edges) in dupl_candidates.items():

                if self.killed is True:
                    break

                self.total_progress += self.step
                self.progress.emit(self.total_progress)
                self.clean_dupl(group_edges, snap_threshold, False)

        self.step = step_original
        # clean orphans
        if orphans:
            for e in self.sEdges.values():

                if self.killed is True:
                    break

                self.total_progress += self.step
                self.progress.emit(self.total_progress)

                self.clean_orphan(e)

        # clean orphan closed polylines
        elif closed_polylines:

            for e in self.sEdges.values():

                if self.killed is True:
                    break

                self.total_progress += self.step
                self.progress.emit(self.total_progress)

                if len(set(e.nodes)) == 1:
                    self.clean_orphan(e)

        # break multiparts
        if multiparts:
            for e in self.sEdges.values():

                if self.killed is True:
                    break

                self.total_progress += self.step
                self.progress.emit(self.total_progress)

                if e.feature.geometry().wkbType() == 5:
                    self.clean_multipart(e)

        return

    # merge

    def merge_b_intersections(self, angle_threshold):

        # special cases: merge parallels (becomes orphan)
        # do not merge two parallel self loops

        edges_passed = set([])

        for e in self.edge_edges_iter():
            if {e}.isdisjoint(edges_passed):
                edges_passed.update({e})
                group_nodes, group_edges = self.route_polylines(e)
                if group_edges:
                    edges_passed.update({group_edges[-1]})
                    self.merge_edges(group_nodes, group_edges, angle_threshold)
        return

    def merge_collinear(self, collinear_threshold, angle_threshold=0):

        filtered_nodes = dict(filter(lambda (id, nd): len(nd.topology) == 2 and len(nd.adj_edges) == 2, graph.sNodes.items()))
        filtered_nodes = dict(filter(lambda (id, nd): angle_3_points(graph.sNodes[nd.topology[0]].feature.geometry().asPoint(), nd.feature.geometry().asPoint(), graph.sNodes[nd.topology[1]].feature.geometry().asPoint()) <= collinear_threshold, filtered_nodes.items()))
        filtered_nodes = {id: nd.adj_edges for id, nd in filtered_nodes.items()}
        filtered_edges = {}
        for k, v in filtered_nodes.items():
            try:
                filtered_edges[v[0]].append(v[1])
            except KeyError:
                filtered_edges[v[0]] = [v[1]]
            try:
                filtered_edges[v[1]].append(v[0])
            except KeyError:
                filtered_edges[v[1]] = [v[0]]

        self.step = (len(filtered_edges) * self.step) / float(len(self.sEdges))

        for group in self.collinear_comp_iter(filtered_edges):
            nodes = [self.sEdges[e].nodes for e in group]
            for idx, pair in enumerate(nodes[:-1]):
                if pair[0] in nodes[idx + 1]:
                    nodes[idx] = pair[::-1]
            if nodes[-1][1] in nodes[-2]:
                nodes[-1] = nodes[-1][::-1]
            nodes = [n[0] for n in nodes] + [nodes[-1][-1]]
            self.merge_edges(nodes, group, angle_threshold)
        return

    def collinear_comp_iter(self, group_dictionary):
        components_passed = set([])
        for id, top in group_dictionary.items():

            self.total_progress += self.step
            self.progress.emit(self.total_progress)

            if {id}.isdisjoint(components_passed) and len(top) != 2:
                group = [[id]]
                candidates = ['dummy', 'dummy']
                while len(candidates) > 0:
                    flat_group = group[:-1] + group[-1]
                    candidates = map(
                        lambda last_visited_node: set(group_dictionary[last_visited_node]).difference(set(flat_group)),
                        group[-1])
                    candidates = list(set(itertools.chain.from_iterable(candidates)))
                    group = flat_group + [candidates]
                    components_passed.update(set(candidates))
                yield group[:-1]

    def edge_edges_iter(self):
        # what if two parallel edges at the edge - should become self loop
        for nd_id, nd in self.sNodes.items():

            if self.killed is True:
                break

            self.total_progress += self.step
            self.progress.emit(self.total_progress)

            con_edges = nd.adj_edges
            if (len(nd.topology) != 2 and len(con_edges) != 2):  # not set to include parallels and self loops
                for e in con_edges:
                    yield e

    def route_polylines(self, startedge):
        # if edge has been passed
        startnode, endnode = self.sEdges[startedge].nodes
        if len(self.sNodes[endnode].topology) != 2 : # not set to account for self loops
            startnode, endnode = endnode, startnode
        group_nodes = [startnode, endnode]
        group_edges = [startedge]
        while len(set(self.sNodes[group_nodes[-1]].adj_edges)) == 2:
            last_visited = group_nodes[-1]
            if last_visited in self.sNodes[last_visited].topology:  # to account for self loops
                break
            con_edge = set(self.sNodes[last_visited].adj_edges).difference(set(group_edges)).pop()
            con_node = [n for n in self.sEdges[con_edge].nodes if n != last_visited][0] # to account for self loops
            group_nodes.append(con_node)
            group_edges.append(con_edge)
        if len(group_nodes) > 2:
            return group_nodes, group_edges
        else:
            return None, None

    def generate_unlinks(self): # for osm or other

        # spIndex # TODO change OTF - insert/delete feature
        self.edgeSpIndex = QgsSpatialIndex()

        self.step = self.step / float(4)
        for e in self.sEdges.values():
            if self.killed is True:
                break

            self.total_progress += self.step
            self.progress.emit(self.total_progress)

            self.edgeSpIndex.insertFeature(e.feature)

        unlinks_id = 0
        self.step = float(3.0) * self.step
        for id, e in self.sEdges.items():

            if self.killed is True:
                break

            self.total_progress += self.step
            self.progress.emit(self.total_progress)

            f_geom = e.feature.geometry()
            # to avoid duplicate unlinks - id > line
            lines = filter(lambda line: f_geom.crosses(self.sEdges[line].feature.geometry()) and id > line, self.edgeSpIndex.intersects(f_geom.boundingBox()))

            for line in lines:
                crossing_points = f_geom.intersection(self.sEdges[line].feature.geometry())
                # in some cases the startpoint or endpoint is returned - exclude
                if crossing_points.geometry().wkbType() == 1 and crossing_points.asPoint() not in f_geom.asPolyline():
                    un_f = QgsFeature(unlink_feat)
                    un_f.setGeometry(crossing_points)
                    un_f.setFeatureId(unlinks_id)
                    un_f.setAttributes([unlinks_id])
                    unlinks_id += 1
                    self.unlinks.append(un_f)
                elif crossing_points.geometry().wkbType() == 4:
                    for p in crossing_points.asMultiPoint():
                        if p not in f_geom.asPolyline():
                            un_f = QgsFeature(unlink_feat)
                            un_f.setGeometry(QgsGeometry.fromPoint(p))
                            un_f.setFeatureId(unlinks_id)
                            un_f.setAttributes([unlinks_id])
                            unlinks_id += 1
                            self.unlinks.append(un_f)
        return


    # TODO: features added - pass through clean_iterator (can be ml line)
    def merge_edges(self, group_nodes, group_edges, angle_threshold):

        geoms = map(lambda e: self.sEdges[e].feature.geometry(), group_edges)
        lengths = map(lambda g: g.length(), geoms)
        max_len = max(lengths)

        # merge edges
        self.edge_id += 1
        feat = QgsFeature()
        # attributes from longest
        longest_feat = self.sEdges[group_edges[lengths.index(max_len)]].feature
        feat.setAttributes(longest_feat.attributes())
        merged_geom = merge_geoms(geoms, angle_threshold)
        if merged_geom.wkbType() == 2:
            p0 = merged_geom.asPolyline()[0]
            p1 = merged_geom.asPolyline()[-1]
        else:
            p0 = merged_geom.asMultiPolyline()[0][0]
            p1 = merged_geom.asMultiPolyline()[-1][-1]

        # special case - if self loop breaks at intersection of other line & then merged back on old self loop point
        # TODO: include in merged_geoms functions to make indepedent
        selfloop_point = self.sNodes[group_nodes[0]].feature.geometry().asPoint()
        if p0 == p1 and p0 != selfloop_point:
            merged_points = geoms[0].asPolyline()
            geom1 = self.sEdges[group_edges[0]].feature.geometry().asPolyline()
            if not geom1[0] == selfloop_point:
                merged_points = merged_points[::-1]
            for geom in geoms[1:]:
                points = geom.asPolyline()
                if not points[0] == merged_points[-1]:
                    merged_points += (points[::-1])[1:]
                else:
                    merged_points += points[1:]
            merged_geom = QgsGeometry.fromPolyline(merged_points)
            if merged_geom.wkbType() != 2:
                print 'ml', merged_geom.wkbType()

        feat.setGeometry(merged_geom)
        feat.setFeatureId(self.edge_id)

        if p0 == self.sNodes[group_nodes[0]].feature.geometry().asPoint():
            merged_edge = sEdge(self.edge_id, feat, [group_nodes[0], group_nodes[-1]])
        else:
            merged_edge = sEdge(self.edge_id, feat, [group_nodes[-1], group_nodes[0]])
        self.sEdges[self.edge_id] = merged_edge

        # update ends
        self.sNodes[group_nodes[0]].topology.remove(group_nodes[1])
        self.update_topology(group_nodes[0], group_nodes[-1], self.edge_id)
        #if group_nodes == [group_nodes[0], group_nodes[1], group_nodes[0]]:
        self.sNodes[group_nodes[-1]].topology.remove(group_nodes[-2])
        self.sNodes[group_nodes[0]].adj_edges.remove(group_edges[0])
        self.sNodes[group_nodes[-1]].adj_edges.remove(group_edges[-1])

        # middle nodes del
        for nd in group_nodes[1:-1]:
            err_f = QgsFeature(error_feat)
            err_f.setGeometry(self.sNodes[nd].feature.geometry())
            err_f.setAttributes(['merged'])
            self.errors.append(err_f)
            del self.sNodes[nd]

        # del edges
        for e in group_edges:
            del self.sEdges[e]

        return

    def simplify_circles(self):
        roundabouts = NULL
        short = NULL
        res = map(lambda group: self.collapse_to_node(group), con_components(roundabouts + short))
        return

    def simplify_parallel_lines(self):
        dual_car = NULL
        res = map(lambda group: self.collapse_to_medial_axis(group), con_components(dual_car))
        pass

    def collapse_to_medial_axis(self):
        pass

    def simplify_angle(self, max_angle_threshold):
        pass

    def catchment_iterator(self, origin_point, closest_edge, cost_limit, origin_name):
        # find closest line
        edge_geom = self.sEdges[closest_edge].feature.geometry()
        nodes = set(self.sEdges[closest_edge].nodes)

        # endpoints
        branches = []
        shortest_line = origin_point.shortestLine(edge_geom)
        point_on_line = shortest_line.intersection(edge_geom)
        fraction = edge_geom.lineLocatePoint(point_on_line)
        fractions = [fraction, 1 - fraction]
        degree = 0
        for node, fraction in zip(nodes, fractions):
            branches.append((None, node, closest_edge, self.sNodes[node].feature.geometry().distance(point_on_line),))

        for k in self.sEdges.keys():
            self.sEdges[k].visited[origin_name] = None

        self.sEdges[closest_edge].visited[origin_name] = True

        while len(branches) > 0:

            branches = [nbr for (org, dest, edge, agg_cost) in branches if agg_cost < cost_limit and dest != [] for nbr in self.get_next_edges(dest, agg_cost, origin_name)]

            #fraction = 1 - ((agg_cost - cost_limit) / float(cost_limit))
            #degree += 1

    def get_next_edges(self, old_dest, agg_cost,origin_name):
        new_origin = old_dest[0]
        new_branches = []
        for edg in set(self.sNodes[new_origin].adj_edges):
            sedge = self.sEdges[edg]
            if sedge.visited[origin_name] is None:
                sedge.visited[origin_name] = new_origin
                new_agg_cost = agg_cost + sedge.len
                sedge.agg_cost[origin_name] = new_agg_cost
                self.sEdges[edg] = sedge
                new_dest = [n for n in sedge.nodes if n != new_origin]
                new_branches.append((new_origin, new_dest, edg, new_agg_cost))
        return new_branches


    def kill(self):
        self.killed = True
