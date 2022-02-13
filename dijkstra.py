import math


# https://blender.stackexchange.com/questions/186067/what-is-the-bmesh-equivalent-to-bpy-ops-mesh-shortest-path-select
class _Node:
    @property
    def edges(self):
        return (e for e in self.vert.link_edges if not e.tag)

    def __init__(self, v):
        self.vert = v
        self.length = math.inf
        self.shortest_path = []


def find_path(bm, v_start, v_target=None, use_topology_distance=False):
    for e in bm.edges:
        e.tag = False

    d = {v: _Node(v) for v in bm.verts}
    node = d[v_start]
    node.length = 0

    visiting = [node]

    while visiting:
        node = visiting.pop(0)

        if node.vert is v_target:
            return d

        for e in node.edges:
            e.tag = True

            if use_topology_distance:
                length = node.length + 1
            else:
                length = node.length + e.calc_length()
            v = e.other_vert(node.vert)

            visit = d[v]
            visiting.append(visit)
            if visit.length > length:
                visit.length = length
                visit.shortest_path = node.shortest_path + [e]

        visiting.sort(key=lambda n: n.length)

    return d
