import bpy
import bmesh
import math
import mathutils

from . import interpolate

from .op_set_vertex_curve  import map_segment_onto_spline 

class Loop():
    def __init__(self, bm, edges):
        self.bm = bm
        self.edges = edges

        #ordered verts of this loop
        self.verts = []        
        if len(self.edges) > 1:
            last_vert = None
            for p in self.edges[0].verts:
                if p not in self.edges[1].verts:
                    last_vert = p

            self.verts.append(last_vert)
            for i in range(len(self.edges)):                
                vert = self.edges[i].other_vert(last_vert)     
                self.verts.append(vert)
                last_vert = vert
        else:
            self.verts = [self.edges[0].verts[0], self.edges[0].verts[1]]

        # make sure start vert stays 'stable'         
        if self.verts[0].co.x + self.verts[0].co.y + self.verts[0].co.z < self.verts[-1].co.x + self.verts[-1].co.y + self.verts[-1].co.z:
            self.verts.reverse()
            self.edges.reverse()

        #store intial vertex coordinates      
        self.initial_vert_positions = []
        for i, v in enumerate(self.verts):
            self.initial_vert_positions.append(v.co.copy())

        self.is_cyclic = self.verts[0] == self.verts[-1]
        
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

    def set_curve_flow(self, tension, use_rail):
        count = len(self.edges)
        if count < 2 or self.is_cyclic:
            return

        self.bm.verts.ensure_lookup_table()
        self.bm.edges.ensure_lookup_table()

        start_vert, end_vert = None, None
        #get starting points
        for p in self.edges[0].verts:
            if p not in self.edges[1].verts:
                start_vert = p

        for p in self.edges[-1].verts:
            if p not in self.edges[-2].verts:
                end_vert = p

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
                # original_corner = point.link_loops[0]
                # for corner in point.link_loops:              
                #     if corner.vert == point and corner.edge == edge:
                #         original_corner = corner
                
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
        
        # if use_rail:
        #     dir1 = self.edges[0].other_vert(start_vert).co - start_vert.co
        #     dir1 = dir1.normalized()
        #     dir2 = self.edges[-1].other_vert(end_vert).co - end_vert.co
        #     dir2 = dir2.normalized()
        # else:
        #     dir1 = find_direction(start_vert, self.edges[0])
        #     dir2 = find_direction(end_vert, self.edges[-1])
        
        dir1 = self.edges[0].other_vert(start_vert).co - start_vert.co
        dir1 = dir1.normalized()
        dir2 = self.edges[-1].other_vert(end_vert).co - end_vert.co
        dir2 = dir2.normalized()

        if use_rail:
            p1 = self.edges[0].other_vert(start_vert).co
            p4 = self.edges[-1].other_vert(end_vert).co
        else:
            p1 = start_vert.co
            p4 = end_vert.co

        scale = (p1 - p4).length * 0.5
        scale *= tension

        p2 = p1 + (dir1 * scale)
        p3 = p4 + (dir2 * scale)
         
        #add_debug_verts = False
        #if add_debug_verts:
        #    # bmesh.ops.create_vert(self.bm, co=p1)
        #    # bmesh.ops.create_vert(self.bm, co=p4)
        #    bmesh.ops.create_vert(self.bm, co=p2)
        #    bmesh.ops.create_vert(self.bm, co=p3)
       
        spline_points = []
        precision = 1000      
        spline_points = mathutils.geometry.interpolate_bezier(p1, p2, p3, p4, precision)

        if use_rail:
            map_segment_onto_spline(self.verts[1:-1], spline_points)
        else:
            map_segment_onto_spline(self.verts, spline_points)




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
        if count < 2 or self.is_cyclic:
            return

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

            if even_spacing:
                vert.co = p1.co + direction * (i + 1)
            else:
                proj = vert.co - p1.co
                scalar = proj.dot(direction_normalized)
                vert.co = p1.co + (direction_normalized * scalar)

            last_vert = vert


    def blend_start_end(self, blend_start, blend_end, blend_type):
        
        if self.is_cyclic:
            return

        count = len(self.verts)
        start_count = blend_start
        end_count = blend_end
      
        if start_count + end_count >= count:
            if start_count < end_count:
                end_count = max(count - start_count - 1, 0)
            elif end_count < start_count:
                start_count = max(count - end_count - 1, 0)
            else:
                midCount = math.floor(count / 2)
                start_count = count - midCount
                end_count = count - start_count
                
        #print(f"start:{blend_start} - end:{blend_end} - vertcount: {count}")
        #print(f"start_count:{start_count} - end_count:{end_count} - count: {count}")
      
        def apply_blend(blend_range, reverse):
            indices = list(range(count))          
            if reverse:
                indices.reverse()

            distances = [0]
            total_length = 0
          
            for i in range(1, blend_range+1):               
                a = self.verts[indices[i]]
                b = self.verts[indices[i-1]]
                length = (a.co - b.co).length
                total_length += length
                distances.append(total_length)

            # print(f"total length: {total_length} - number of distances: {len(distances)}")
          
            if total_length == 0:
                return
 
            for i in range(blend_range+1):
                blend_value = distances[i] / total_length                
            
                if blend_type == 'SMOOTH':
                    blend_value = interpolate.smooth_step(0.0, 1.0, blend_value)

                vert = self.verts[indices[i]]
                intital_position = self.initial_vert_positions[indices[i]] 
                vert.co = intital_position.lerp(vert.co, blend_value)

        if blend_start > 0:
            apply_blend(min(count-1, start_count), reverse=False)
        if blend_end > 0:
            apply_blend(min(count-1, end_count), reverse=True)


    def set_flow(self, tension, min_angle):
     
        for edge in self.edges:
            target = {}

            if edge.is_boundary:
                continue

            for loop in edge.link_loops:              
                # todo check triangles/ngons?

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
                    
                    final = ring1.link_loop_radial_next.link_loop_next
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
              
                # result = interpolate.catmullrom(p1, p2, p3, p4, 1, 3)[1]
                result = interpolate.hermite_3d(p1, p2, p3, p4, 0.5, -tension, 0)
                result = mathutils.Vector(result)                
                vert.co = result
 
            

