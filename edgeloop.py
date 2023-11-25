import bpy
import bmesh
import math
import mathutils

from . import interpolate


class Loop():
    def __init__(self, bm, edges):
        self.bm = bm
        self.edges = edges

        self.verts = set()
        for e in self.edges:
            for v in e.verts:
                self.verts.add(v)

        # print("edgeloop length: %s" % len(self.edges))
        self.valences = []

        self.ring = {}
        for e in self.edges:
            self.ring[e] = []

        self.edge_rings = {}
        self.ends = {}

    def __str__(self):
        str = "\n"
        for index, edge in enumerate(self.edges):
            str += "edge: %s -" % (edge.index)
            str += " valence: %s" % self.valences[index]

            for r in self.get_ring(edge):
                str += " | %s " % r.index

            # print(self.edge_ring.values())
            # for k,v in self.edge_ring.items():
            #    print("key: ", k.index)
            #    print("value: ", v)

            # for loop in self.edge_ring[edge]:
            #    str += " = %s " % loop.edge.index
            str += "\n"

            ends = self.get_ring_ends(edge)
            for e in ends:
                str += " end: %s" % e.index

            str += "\n"
        return str

    def __repr__(self):
        return self.__str__()

    def set_ring(self, edge, ring_edge):
        if edge in self.ring and len(self.ring[edge]) <= 2:
            self.ring[edge].append(ring_edge)

    def get_ring(self, edge):
        if edge in self.ring:
            return self.ring[edge]

        raise Exception("edge not in Edgeloop!")

    def select(self):
        for edge in self.edges:
            edge.select = True

    def get_ring_ends(self, edge):
        ring = self.edge_rings[edge]
        return (ring[0], ring[len(ring) - 1])

    def set_curve_flow(self, tension, mix):
        count = len(self.edges)
        if count < 2:
            return

        self.bm.verts.ensure_lookup_table()
        self.bm.edges.ensure_lookup_table()

        p1, p4 = None, None

        #get starting points
        for p in self.edges[0].verts:
            if p not in self.edges[1].verts:
                p1 = p

        for p in self.edges[-1].verts:
            if p not in self.edges[-2].verts:
                p4 = p

        print(f"endpoints: {p1}, {p4}")

        def print_bm_loop(corner):
            '''
            Vert -> head -- Edge -> Tail
            link_loop_prev => where head points to
            '''
            def get_string(corner):
                return  f"{corner.index} | vert: {corner.vert.index} edge: {corner.edge.index}"

            print("----------------------------")
            l = corner
            print("corner:              ", get_string(l))
            l = corner.link_loop_next
            print("link_loop_next       ", get_string(l))
            l = corner.link_loop_prev
            print("link_loop_prev       ", get_string(l))
            l = corner.link_loop_radial_next
            print("link_loop_radial_next", get_string(l))
            l = corner.link_loop_radial_prev
            print("link_loop_radial_prev", get_string(l))
            print("----------------------------")



        def find_direction(point, edge):   
            if len(point.link_edges) == 2:    
                # |_ corner case with mesh borders            
                a = point.link_edges[0].other_vert(point).co - point.co
                b = point.link_edges[1].other_vert(point).co - point.co
              
                # if a is edge
                if point.link_edges[0] == edge:
                    c = a.cross(b)                    
                    d = c.cross(b)
                # if b is edge
                else:
                    c = b.cross(a)
                    d = c.cross(a)
                    
                return -d.normalized()
               
            elif len(point.link_edges) == 3:  
                original_corner = point.link_loops[0]
                for corner in point.link_loops:              
                    if corner.vert == point and corner.edge == edge:
                        original_corner = corner
                
                # edge is at an 'end'
                # _|_
                if len(edge.link_faces) == 2:     
                    a = edge.other_vert(point).co - point.co
                    n = edge.link_loops[0].face.normal + edge.link_loops[1].face.normal
                    n = n.normalized()
                    c = a.cross(n)
                    c = c.cross(-n)
                    return c.normalized()               
                else:
                    # |_
                    # |
                    # search for the edge which is not neighbouring 
                    # to the face connected to the input edge
                    for e in point.link_edges:
                        is_connected_to_end_edge = False
                        for f in e.link_faces:
                            if f in edge.link_faces:                                
                                is_connected_to_end_edge = True
                                break                     

                        if not is_connected_to_end_edge: 
                            b = e.other_vert(point)
                            break

                    a = point
                    c = a.co - b.co
                    return c.normalized()

            elif len(point.link_edges) == 4:    
                # regular quad case
                # _|_
                #  |  
                for corner in edge.link_loops:
                    if corner.vert == point:
                        a = point
                        b = corner.link_loop_prev.link_loop_radial_prev.link_loop_prev.vert
                        c = a.co - b.co
                        return c.normalized()                        
            else:                
                a = edge.other_vert(point).co - point.co
                n = edge.link_loops[0].face.normal + edge.link_loops[1].face.normal
                n = n.normalized()
                c = a.cross(n)
                c = c.cross(n)
                return -c.normalized()         
        
        dir1 = find_direction(p1, self.edges[0])
        dir2 = find_direction(p4, self.edges[-1])
        # return

        start_vert = p1

        p1 = p1.co
        p4 = p4.co

        scale = (p1 - p4).length * 0.5
        scale *= tension

        # p2 = p1 - (dir1 * scale)
        # p3 = p4 - (dir2 * scale)

        p2 = p1 + (dir1 * scale)
        p3 = p4 + (dir2 * scale)

        add_debug_verts = False
        if add_debug_verts:
            # bmesh.ops.create_vert(self.bm, co=p1)
            # bmesh.ops.create_vert(self.bm, co=p4)
            bmesh.ops.create_vert(self.bm, co=p2)
            bmesh.ops.create_vert(self.bm, co=p3)
       
        bias = 0
        spline_points = []
        precision = 1000

        # knot1, handle1, handle2, knot2, resolution)
      
        spline_points = mathutils.geometry.interpolate_bezier(p1, p2, p3, p4, precision)

        # for i in range(precision):
        #     mu = i / float(precision)

        #     spline_pos = interpolate.hermite_3d(p2, p1, p4, p3, mu, -tension, bias)
        #     # if add_debug_verts:
        #     #     bmesh.ops.create_vert(self.bm, co=spline_pos)
        #     spline_points.append(mathutils.Vector(spline_pos))

        total_lenght = 0
        for index in range(1, len(spline_points)):
            total_lenght += (spline_points[index] - spline_points[index-1]).magnitude


        segment_length = total_lenght /  float(len(self.edges))
        # print(total_lenght, segment_length)
        current_point = start_vert
        current_edge_index = 0
        current_length = 0

        for index in range(1, len(spline_points)):
            current_length += (spline_points[index] - spline_points[index-1]).magnitude
            
            if current_length > segment_length:                
                current_length = 0
                position = spline_points[index]

                e = self.edges[current_edge_index]
                current_point = e.other_vert(current_point)  
                current_point.co = current_point.co.lerp(position, mix)      

                current_edge_index += 1

                if current_edge_index == len(self.edges)-1:
                    break
                

    def get_average_distance(self):
        dist = 0
        for e in self.edges:
            dist += (e.verts[0].co - e.verts[1].co).length
        return dist / float(len(self.edges))

    def straighten(self, distance):
        '''
        this makes takes the end points of an edge and places them even distanced to the 'next' vert in the extension of the edge loop
        
        Moves A and B:

        A' ------ A - B -- B' 
    
        to:

        A' --- A --- B --- B'
        '''

        
        edge = self.edges[0]

        def find_neighbour(p):
            link_edges = set(p.link_edges)
            link_edges.remove(edge)

            #print("face a:", edge.link_faces[0].index, "face b:", edge.link_faces[1].index)

            faceA_is_quad = len(edge.link_faces[0].verts) == 4

            edges = link_edges
            if faceA_is_quad:
                edges -= set(edge.link_faces[0].edges)

            if not edge.is_boundary:
                faceB_is_quad = len(edge.link_faces[1].verts) == 4
                if faceB_is_quad:
                    edges -= set(edge.link_faces[1].edges)

            v = mathutils.Vector((0, 0, 0))
            count = 0

            for e in edges:
                for vert in e.verts:
                    if vert == p:
                        continue

                    v += vert.co
                    count += 1

            if count > 0:
                v /= count
                
            return v 

        a1 = edge.verts[0]
        a2 = edge.verts[1]

        a1_len = len(a1.link_edges)
        a2_len = len(a2.link_edges)
        if a1_len <= 3 or a2_len <= 3:
            return

        b1 = find_neighbour(a1)
        b2 = find_neighbour(a2)

        direction = (b2 - b1).normalized()
        max_distance = (b2 - b1).length

        if distance * 2.0 > max_distance:
            distance = max_distance * 0.5

        a1.co = b1 + distance * direction
        a2.co = b2 - distance * direction

    def set_linear(self, even_spacing):

        count = len(self.edges)
        if count < 2:
            return

        #print("even_spacing:", even_spacing)

        for p in self.edges[0].verts:
            if p not in self.edges[1].verts:
                p1 = p

        for p in self.edges[-1].verts:
            if p not in self.edges[-2].verts:
                p2 = p

        direction = (p2.co - p1.co)
        direction = direction / (count)
        direction_normalized = direction.normalized()

        last_vert = p1
        for i in range(count - 1):
            vert = self.edges[i].other_vert(last_vert)
            # print(vert.index, "--", vert.co)

            if even_spacing:
                vert.co = p1.co + direction * (i + 1)
            else:
                proj = vert.co - p1.co
                scalar = proj.dot(direction_normalized)
                vert.co = p1.co + (direction_normalized * scalar)

            last_vert = vert

    def set_flow(self, obj, tension, min_angle, mix, blend_start, blend_end, blend_type):

        # --------------------------------------------------------------
        # Get the loop vertices and calculate the start and end
        # blending.
        # --------------------------------------------------------------

        # Get the start and end vertices of the selected loop.
        loopStart = self.getStartVertices()
        loopData = None
        # If loop start data has been found get all vertices of the loop
        # for blending the end points.
        if loopStart:
            loopData = getOrderedLoopVerts(obj, loopStart)

        # Create the dictionary with the blend values for the loop
        # vertices.
        blendVerts = {}
        if loopData:
            for loopVerts in loopData:
                count = len(loopVerts)
                for i in range(count):
                    blendVerts[loopVerts[i].index] = 1.0

                if blend_start + blend_end >= count:
                    if blend_start < blend_end:
                        blend_end = max(count - blend_start - 1, 0)
                    elif blend_end < blend_start:
                        blend_start = max(count - blend_end - 1, 0)
                    else:
                        midCount = math.floor(count / 2)
                        blend_start = count - midCount
                        blend_end = count - blend_start

                if blend_start > 0:
                    interpolate.setBlendValues(loopVerts, blendVerts, blend_start, start=True)
                if blend_end > 0:
                    interpolate.setBlendValues(loopVerts, blendVerts, blend_end, start=False)

        # --------------------------------------------------------------
        # Surface calculation.
        # --------------------------------------------------------------

        visited = set()

        processedVerts = set()

        for edge in self.edges:
            target = {}

            if edge.is_boundary:
                continue

            for loop in edge.link_loops:
                if loop in visited:
                    continue

                # todo check triangles/ngons?

                visited.add(loop)
                ring1 = loop.link_loop_next.link_loop_next
                ring2 = loop.link_loop_radial_prev.link_loop_prev.link_loop_prev

                center = edge.other_vert(loop.vert)

                p1 = None
                p2 = ring1.vert
                p3 = ring2.link_loop_radial_next.vert
                p4 = None

                #print("ring1 %s - %s" % (ring1.vert.index, ring1.edge.index))
                #print("ring2 %s - %s" % (ring2.vert.index, ring2.edge.index))
                # print("p2: %s - p3: %s " % (p2.index, p3.index))

                result = []
                if not ring1.edge.is_boundary:
                    is_quad = len(ring1.face.verts) == 4
                    # if is_quad:
                    final = ring1.link_loop_radial_next.link_loop_next

                    # else:
                    #    final = ring1

                    #print("is_quad:", is_quad, " - ", final.edge.index)

                    a, b = final.edge.verts
                    if p2 == a:
                        p1 = b.co
                    else:
                        p1 = a.co

                    a = (p1 - p2.co).normalized()
                    b = (center.co - p2.co).normalized()
                    dot = min(1.0, max(-1.0, a.dot(b)))
                    angle = math.acos(dot)

                    if angle < min_angle:
                        # print("r1: %s" % (math.degrees(angle)))
                        p1 = p2.co - (p3.co - p2.co) * 0.5

                        # bmesh.ops.create_vert(self.bm, co=p1)

                else:
                    p1 = p2.co - (p3.co - p2.co)
                    # bmesh.ops.create_vert(self.bm, co=p1)

                result.append(p1)
                result.append(p2.co)

                if not ring2.edge.is_boundary:
                    is_quad = len(ring2.face.verts) == 4
                    # if is_quad:
                    final = ring2.link_loop_radial_prev.link_loop_prev
                    # else:
                    #    final = ring2

                    #print("is_quad:", is_quad, " - ", final.edge.index)

                    a, b = final.edge.verts

                    if p3 == a:
                        p4 = b.co
                    else:
                        p4 = a.co

                    a = (p4 - p3.co).normalized()
                    b = (center.co - p3.co).normalized()
                    dot = min(1.0, max(-1.0, a.dot(b)))
                    angle = math.acos(dot)

                    if angle < min_angle:
                        # print("r2: %s" % (math.degrees(angle)))
                        p4 = p3.co - (p2.co - p3.co) * 0.5

                        # bmesh.ops.create_vert(self.bm, co=p4)

                else:
                    # radial_next doenst work at boundary
                    p3 = ring2.edge.other_vert(p3)
                    p4 = p3.co - (p2.co - p3.co)
                    # bmesh.ops.create_vert(self.bm, co=p4)

                result.append(p3.co)
                result.append(p4)

                target[center] = result

            for vert, points in target.items():
                p1, p2, p3, p4 = points

                if p1 == p2 or p3 == p4:
                    print("invalid input - two control points are identical!")
                    continue

                # normalize point distances so that long edges dont skew the curve
                d = (p2 - p3).length * 0.5

                p1 = p2 + (d * (p1 - p2).normalized())
                p4 = p3 + (d * (p4 - p3).normalized())

                # print("p1: %s\np2:%s\np3: %s\np4:%s\n1" % (p1, p2, p3, p4))
                # result = mathutils.geometry.interpolate_bezier(p1, p2, p3, p4, 3)[1]

                # result = interpolate.catmullrom(p1, p2, p3, p4, 1, 3)[1]
                result = interpolate.hermite_3d(
                    p1, p2, p3, p4, 0.5, -tension, 0)
                result = mathutils.Vector(result)
                # linear = (p2 + p3) * 0.5

                # The previously used lerp function to multiply the
                # result is replaced by the end point blending which
                # includes the multiplying part.
                # vert.co = vert.co.lerp(result, mix)
                # vert.co = linear.lerp(curved, tension)

                # ------------------------------------------------------
                # Blend the end points.
                # ------------------------------------------------------
                if vert.index not in processedVerts:
                    if vert.index in blendVerts:
                        value = interpolate.blendValue(blendVerts[vert.index], mix, blend_type)
                        vert.co = vert.co.lerp(result, value)
                    else:
                        vert.co = vert.co.lerp(result, mix)

                processedVerts.add(vert.index)

    def getStartVertices(self):
        """Return a list of tuples, containing the start edge and vertex
        indicating an edge loop.

        :return: A list of tuples with the start edge and vertex of an
                 edge loop.
        :rtype: list(tuple(bmesh.types.BMEdge, bmesh.types.BMVert))
        """
        verts = set()
        for edge in self.edges:
            for loop in edge.link_loops:
                connectedEdges = loop.vert.link_edges
                selectedCount = 0
                for connected in connectedEdges:
                    if connected.select:
                        selectedCount += 1
                if selectedCount == 1:
                    verts.add((edge, loop.vert))
        return verts


# ----------------------------------------------------------------------
# Custom function to get the selected loop edges in the correct order.
#
# This most likely overlaps with existing functionality and might make
# refactoring necessary. But it shouldn't affect performance too much.
# ----------------------------------------------------------------------

def getOrderedLoopVerts(obj, edges):
    """Return a list with all edge loop vertices for each given edge.

    :param obj: The mesh object.
    :type obj: bpy.types.Object
    :param edges: The list of start edges and vertices for a selected
                  edge loop.
    :type edges: list(tuple(bmesh.types.BMEdge, bmesh.types.BMVert))

    :return: A list of loops, each containing a list of vertices of each
             edge loop.
    :rtype: list(list(bmesh.types.BMVert))
    """
    # In order to get the current selection history it's necessary to
    # get the bmesh from the current edit mesh.
    bpy.ops.object.mode_set(mode='EDIT')
    bm = bmesh.from_edit_mesh(obj.data)

    # Validate and get the selection history.
    bm.select_history.validate()
    history = bm.select_history.active

    visitedEdges = set()
    loops = []

    for edge, vertex in edges:
        # Mark the current edge as visited so that it's only processed
        # once.
        visitedEdges.add(edge.index)

        # If the start vertex is contained in any of the previously
        # collected loops, processing this vertex is not necessary since
        # it can be considered the end point of an already processed
        # oop.
        if any(vertex in loop for loop in loops):
            continue

        loopVerts = []
        loopEnd = False

        # Go over all connected edges to collect the loop vertices.
        while not loopEnd:
            # Add the first vertex of the current edge.
            loopVerts.append(vertex)
            # Get the faces connected to the current edge.
            # The next edge in the loop should be connected to different
            # faces.
            edgeFaces = [face.index for face in edge.link_faces]
            # Get the other vertex of the edge to get the connected
            # edges.
            vertex = edge.other_vert(vertex)
            connectedEdges = vertex.link_edges

            nextEdge = False

            # Go over the connected edges and check it one is selected.
            # Already visited edges can be skipped.
            for e in connectedEdges:
                if e.select and e.index not in visitedEdges:
                    # Get the connected faces. These should be unique
                    # from the previous edge.
                    connectedFaces = e.link_faces
                    if not any(face.index in edgeFaces for face in connectedFaces):
                        # Mark the edge as visited.
                        visitedEdges.add(e.index)
                        # The next edge is the current one.
                        edge = e
                        # Continue.
                        nextEdge = True
            # If there is no next edge add the last vertex to the list.
            if not nextEdge:
                loopVerts.append(vertex)
                loopEnd = True

        # Check for the order of vertices depending on the selected
        # edge.
        if history:
            index = None
            if isinstance(history, bmesh.types.BMVert):
                index = history.index
            elif isinstance(history, bmesh.types.BMEdge):
                index = history.verts[0].index

            # If the active vertex is contained in the loop list but not
            # located at the start of the list, reverse the index list.
            if index is not None:
                indices = [v.index for v in loopVerts]
                if index in indices:
                    indexPos = indices.index(index)
                    if indexPos > 1:
                        loopVerts.reverse()

        # Add the list of vertices for the loop.
        loops.append(loopVerts)

    bpy.ops.object.mode_set(mode='OBJECT')

    return loops
