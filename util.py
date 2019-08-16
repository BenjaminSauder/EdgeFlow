from collections import deque

import bpy
import bmesh

from . import edgeloop


def walk_boundary(start_edge, limit_to_edges=None):
    edge_loop = set([start_edge])
    visited = set()

    candidates = [start_edge]
    while True:
        for candidate in candidates:
            for vert in candidate.verts:
                if len(vert.link_edges) > 2:  # valence of verts as a blocker
                    for edge in vert.link_edges:
                        if edge.is_boundary and edge not in edge_loop:
                            if limit_to_edges != None:
                                if edge in limit_to_edges:
                                    edge_loop.add(edge)
                            else:
                                edge_loop.add(edge)

            visited.add(candidate)

        candidates = edge_loop - visited
        if len(visited) == len(edge_loop):
            break

    #sorting this mess..
    raw_edge_loop = list(edge_loop)

    start_edge = raw_edge_loop[0]
    raw_edge_loop.remove(start_edge)

    sorted_edge_loop = deque()
    sorted_edge_loop.append(start_edge)
    add = sorted_edge_loop .append

    for p in start_edge.verts:
        while True:

            edge = None
            for e in raw_edge_loop:
                if p in e.verts:
                    edge = e

            if edge != None:
                add(edge)
                p = edge.other_vert(p)
                raw_edge_loop.remove(edge)
            else:
                break

        add = sorted_edge_loop .appendleft

    #for e in list(sorted_edge_loop ):
    #    print("###", e.index)

    if len(sorted_edge_loop ) != len(edge_loop):
        raise  Exception("WTF")

    return list(sorted_edge_loop)


def walk_ngon(start_edge, limit_to_edges=None):
    edge_loop = deque()
    edge_loop.append(start_edge)

    start_loops = []
    face_valence = []
    for linked_loop in start_edge.link_loops:
        vert_count = len(linked_loop.face.verts)
        if vert_count > 4:
            start_loops.append(linked_loop)
            face_valence.append(vert_count)

    max_value = max(face_valence)
    start_loop = start_loops[face_valence.index(max_value)]

    # print(start_loop.vert.index, start_loop.edge.index)

    loop = start_loop.link_loop_next
    while len(loop.vert.link_edges) < 4 and loop.edge not in edge_loop:
        if limit_to_edges != None and loop.edge not in limit_to_edges:
            break

        edge_loop.append(loop.edge)
        # print("next", loop.edge.index)
        loop = loop.link_loop_next

    # print("switch")
    loop = start_loop.link_loop_prev
    while len(loop.edge.other_vert(loop.vert).link_edges) < 4 and loop.edge not in edge_loop:
        if limit_to_edges != None and loop.edge not in limit_to_edges:
            break

        edge_loop.appendleft(loop.edge)
        loop = loop.link_loop_prev
        # print("prev", loop.edge.index)

    return list(edge_loop)


def walk_edge_loop(start_edge, limit_to_edges=None):
    edge_loop = deque()
    edge_loop.append(start_edge)
    add = edge_loop.append

    for loop in start_edge.link_loops:
        start_valence = len(loop.vert.link_edges)
        # print("start_valence", start_valence)

        if start_valence <= 4:
            while True:
                valence = len(loop.vert.link_edges)
                # print("valence: %s | vert: %s edge: %s" % (valence, loop.vert.index, loop.edge.index))

                if valence == 4 and start_valence == valence:
                    loop = loop.link_loop_prev.link_loop_radial_prev.link_loop_prev

                    if limit_to_edges != None:
                        if loop.edge in limit_to_edges:
                            add(loop.edge)
                        else:
                            break
                    else:
                        add(loop.edge)

                        # print("add edge:", loop.edge.index)
                else:
                    # print("break valence", valence, loop.face != face)
                    break
        else:
            pass
            # print("ignore this direction")
        add = edge_loop.appendleft

    return list(edge_loop)


def get_edgeloop(bm, start_edge, limit_to_edges=None):
    start_loops = start_edge.link_loops

    is_ngon = False
    for loop in start_loops:
        if len(loop.face.verts) > 4:
            is_ngon = True
            break

    quad_flow = len(start_edge.verts[0].link_edges) == 4 and len(start_edge.verts[1].link_edges) == 4
    loop_end = (len(start_edge.verts[0].link_edges) > 4 and len(start_edge.verts[1].link_edges) == 4 or
                len(start_edge.verts[0].link_edges) == 4 and len(start_edge.verts[1].link_edges) > 4)

    # print( "is quad flow", quad_flow)
    # print("is loop end", loop_end)

    if is_ngon and not quad_flow and not loop_end:
        return edgeloop.Loop(bm, walk_ngon(start_edge, limit_to_edges))

    elif start_edge.is_boundary:
        return edgeloop.Loop(bm, walk_boundary(start_edge, limit_to_edges))
    else:
        return edgeloop.Loop(bm, walk_edge_loop(start_edge, limit_to_edges))


def get_edgeloops(bm, edges):
    '''
    edge_loop = get_edgeloop(edges[0])

    for e in edge_loop:
        e.select = True

    return
    '''

    not_visited = set(edges)

    edge_loops = []
    while (len(not_visited) > 0):
        next = not_visited.pop()

        edge_loop = get_edgeloop(bm, next, not_visited)
        edge_loops.append(edge_loop)

        for edge in edge_loop.edges:
            if edge in not_visited:
                not_visited.remove(edge)

    # print("edge_loops:", len(edge_loops))

    edge_loops = compute_edgeloop_data(edge_loops)
    return edge_loops


def find_edge_ring_neighbours(edgeloops, edge_to_Edgeloop):
    # find neighbouring edge rings
    for edgeloop in edgeloops:
        for edge in edgeloop.edges:

            if len(edgeloop.get_ring(edge)) == 2:
                continue

            for link_loop in edge.link_loops:
                if len(link_loop.face.verts) != 4:
                    continue

                next = link_loop.link_loop_next.link_loop_next.edge

                if next not in edgeloop.get_ring(edge):
                    if next in edge_to_Edgeloop.keys():
                        edgeloop.set_ring(edge, next)
                        edge_to_Edgeloop[next].set_ring(next, edge)


def find_control_edgeloop(edgeloops, edge_to_Edgeloop):
    for edgeloop in edgeloops:
        for edge in edgeloop.edges:
            if edge in edgeloop.edge_rings:
                continue

            #print("start edge: ", edge.index)

            edge_ring = deque()
            edge_ring.append(edge.link_loops[0])
            ends = []
            append_func = edge_ring.append

            for index, loop in enumerate(edge.link_loops):
                next = loop
                prev = None
                visited = set()
                while True:

                    ring = next.link_loop_prev.link_loop_prev
                    #print(ring.edge.index)
                    if ring in visited:
                        break
                    visited.add(ring)

                    if ring.edge not in edge_to_Edgeloop:
                        ends.append(ring)
                        break

                    # print( ring.edge.index )
                    append_func(ring)
                    prev = next
                    next = ring.link_loop_radial_prev

                    if ring.edge.is_boundary:
                        ends.append(ring)
                        break

                #edges have max 2 loops so this I can just switch like this
                if index == 0:
                    append_func = edge_ring.appendleft


            #print("edge_ring:")
            #for l in edge_ring:
            #    print(l.edge.index)
            for ring in edge_ring:
                edge_to_Edgeloop[ring.edge].edge_rings[ring.edge] = edge_ring
                edge_to_Edgeloop[ring.edge].ends[ring.edge] = ends
            #edgeloop.edge_rings[ring] = edge_ring


def compute_edge_ring_valences(edgeloops, edge_to_Edgeloop):
    for edgeloop in edgeloops:
        max_valence = -1
        for edge in edgeloop.edges:
            valence = 0
            visited = set()
            search = set()
            search.add(edge)
            while len(search) > 0:
                current = search.pop()
                visited.add(current)

                loop = edge_to_Edgeloop[current]
                ring_edges = loop.get_ring(current)

                add_to_valence = True
                for ring in ring_edges:
                    if ring not in visited:
                        search.add(ring)
                        if add_to_valence:
                            valence += 1
                            add_to_valence = False

            edgeloop.valences.append(valence)
            max_valence = max(max_valence, valence)
        edgeloop.max_valence = max_valence


def compute_edgeloop_data(edgeloops):
    edge_to_Edgeloop = {}

    for edgeloop in edgeloops:
        for edge in edgeloop.edges:
            edge_to_Edgeloop[edge] = edgeloop

    find_edge_ring_neighbours(edgeloops, edge_to_Edgeloop)
    compute_edge_ring_valences(edgeloops, edge_to_Edgeloop)

    find_control_edgeloop(edgeloops, edge_to_Edgeloop)

    result = sorted(edgeloops, key=lambda edgeloop: edgeloop.max_valence)
    result = list(reversed(result))

    #for el in edgeloops:
    #    print(el)

    return result
