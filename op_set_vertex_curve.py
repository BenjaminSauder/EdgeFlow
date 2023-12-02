import time
import math

import bpy
from bpy.props import IntProperty, BoolProperty
import bmesh
import mathutils

from . import interpolate
from . import dijkstra


def collect_vert_path(bm, selected, use_topology_distance):
    '''
    Find the shortest paths from the selected verts this is based on input order.
    [a,b,c] -> ([a,b],[b,c])
    '''
    current = len(selected) - 1

    path = []
    while current > 0:
        start = bm.verts[selected[current]]
        end = bm.verts[selected[current-1]]

        current -= 1

        nodes = dijkstra.find_path(bm, start, end, use_topology_distance=use_topology_distance)
        path.append((start, end, nodes))

    vert_path = []
    for p in path:
        start, end, nodes = p
        node = nodes[end]

        start_end_path = node.shortest_path

        if start not in vert_path:
            vert_path.append(start)

        for e in start_end_path:
            if e.verts[0] not in vert_path:
                vert_path.append(e.verts[0])
            elif e.verts[1] not in vert_path:
                vert_path.append(e.verts[1])
  
    vert_path = list(reversed(vert_path))
    return vert_path


def split_vert_path_into_segments(bm, selected, vert_path):
    '''
    Splits the vert path into segments based on selected vertices
    selected [a1,b1,c1,d1] vert_path[a1, a2, a3, b, b2, c1, c2, c3, d1] -> [a1,b1,c1,d1], ([a1,a2,a3,b], [b1,b2,c], [c1,c2,3,d])
    '''
    knots = []
    segments = [[]]

    for v in vert_path:
        current_knot_index = len(knots)
        current_knot = bm.verts[selected[current_knot_index]]

        if v == current_knot:
            knots.append(current_knot)
            segments[-1].append(v)

            if current_knot_index != 0 and current_knot_index != len(selected)-1:
                segments.append([v])
        else:
            segments[-1].append(v)

    return knots, segments


def map_segment_onto_spline(segment, positions):
    '''
    Calculates the total arc length, and evenly distributes the points based on this.
    '''

    total_lenght = 0
    for index in range(len(positions)):
        if index == 0:
            continue
        total_lenght += (positions[index] - positions[index-1]).magnitude

    segment_part_length = total_lenght / float(len(segment)-1)

    current_segment_index = 1
    current_length = 0
    for index in range(len(positions)):
        if index == 0:
            continue

        current_length += (positions[index] - positions[index-1]).magnitude

        if current_length >= segment_part_length:

            remainder = current_length - segment_part_length
            current_length = current_length % segment_part_length

            p1 = positions[index-1]
            p2 = positions[index]
            p = p1 + (p1-p2).normalized() * remainder

            if current_segment_index != 0 and current_segment_index != len(segment)-1:
                v = segment[current_segment_index]
                v.co = p

                current_segment_index += 1


def curve_hermite(bm, selected, vert_path, tension):
    knots, segments = split_vert_path_into_segments(bm, selected, vert_path)
    
    if len(knots) == 1:                
        return 1, 'Path found is too short - try toggling "Edge Distance"'
  
    for index, segment in enumerate(segments):
        is_start = index == 0
        is_end = index == len(segments)-1
        # print("--")
        if not is_start and not is_end:
            # print("middle segment:")
            p0 = knots[index-1].co
            p1 = knots[index].co
            p2 = knots[index+1].co
            p3 = knots[index+2].co
        elif is_start:
            # print("start segment:")
            p1 = knots[index].co
            p2 = knots[index+1].co

            delta = (p1-p2)
            p3 = knots[index+2].co
            p3 = p2 - ((p2-p3).normalized() * delta.magnitude)

            # do a topology search to find the 'previous' edge
            for corner in knots[index].link_loops:                
                if corner.link_loop_next.vert == segment[index+1]:           
                    p0 = corner.link_loop_prev.link_loop_radial_prev.link_loop_prev
                    break
                elif corner.link_loop_prev.vert == segment[index+1]:
                    p0 = corner.link_loop_radial_prev.link_loop_next.link_loop_next
                    break 
            p0 = p0.vert.co
        
        elif is_end:
            # print("end segment:")
            p1 = knots[-2].co
            p2 = knots[-1].co

            delta = (p0-p1)
            p0 = knots[-3].co
            p0 = p1 - ((p1-p0).normalized() * delta.magnitude)

            # do a topology search to find the 'previous' edge
            for corner in knots[-1].link_loops:                
                if corner.link_loop_next.vert == segment[-2]:           
                    p3 = corner.link_loop_prev.link_loop_radial_prev.link_loop_prev                   
                    break
                elif corner.link_loop_prev.vert == segment[-2]:                   
                    p3 = corner.link_loop_radial_prev.link_loop_next.link_loop_next
                    break 
            p3 = p3.vert.co

       
        bias = 0
        spline_points = []
        precision = 1000
        for i in range(precision):
            mu = i / float(precision)
            spline_pos = interpolate.hermite_3d(p0, p1, p2, p3, mu, -tension, bias)
            spline_points.append(mathutils.Vector(spline_pos))

        map_segment_onto_spline(segment, spline_points)

    return 0, ""


def curve_bezier(bm, selected, vert_path):

    knots, segments = split_vert_path_into_segments(bm, selected, vert_path)

    for index, segment in enumerate(segments):

        is_start = index == 0
        is_end = index == len(segments)-1

        if not is_start and not is_end:
            p0 = knots[index-1]
            p1 = knots[index]
            p2 = knots[index+1]
            p3 = knots[index+2]

            center_dir_left = (p1.co-p0.co + p1.co-p2.co).normalized()
            up_dir_left = center_dir_left.cross(p2.co - p1.co).normalized()
            tangent_left = up_dir_left.cross(center_dir_left).normalized()
            dot_left = center_dir_left.dot((p1.co-p2.co).normalized())

            center_dir_right = (p1.co-p2.co + p3.co-p2.co).normalized()
            up_dir_right = center_dir_right.cross(p2.co - p3.co).normalized()
            tangent_right = up_dir_right.cross(center_dir_right).normalized()
            dot_right = center_dir_right.dot((p1.co-p2.co).normalized())

            length_left = (p2.co - p1.co).magnitude * dot_left * 0.5
            length_right = (p3.co - p2.co).magnitude * dot_right * 0.5

        elif is_start:
            p1 = knots[index]
            p2 = knots[index+1]
            p3 = knots[index+2]

            center_dir_right = (p2.co-p1.co + p2.co-p3.co).normalized()
            up_dir_right = center_dir_right.cross(p2.co - p3.co).normalized()
            tangent_right = up_dir_right.cross(center_dir_right).normalized()

            dot_right = center_dir_right.dot((p2.co-p1.co).normalized())

            tangent_left = center_dir_right

            length_right = (p3.co - p2.co).magnitude * dot_right * 0.5
            length_left = length_right

        elif is_end:
            p0 = knots[-3]
            p1 = knots[-2]
            p2 = knots[-1]

            center_dir_left = (p1.co-p0.co + p1.co-p2.co).normalized()
            up_dir_left = center_dir_left.cross(p2.co - p1.co).normalized()
            tangent_left = up_dir_left.cross(center_dir_left).normalized()

            dot_left = center_dir_left.dot((p1.co-p2.co).normalized())

            print(dot_left, dot_right)

            tangent_right = center_dir_left

            length_left = (p1.co - p2.co).magnitude * dot_left * 0.5
            length_right = length_left

        p1_knot = p1.co + tangent_left * length_left
        p2_knot = p2.co + tangent_right * length_right

        print(f"(p1: {p1.co}, p1_knot: {p1_knot}")
        print(f"(p2: {p2.co}, p2_knot: {p2_knot}")

        precision = 100
        positions = mathutils.geometry.interpolate_bezier(
            p1.co, p1_knot, p2_knot, p2.co, len(segment) * precision)

        total_lenght = 0
        for index in range(len(positions)):
            if index == 0:
                continue
            total_lenght += (positions[index] - positions[index-1]).magnitude

        segment_part_length = total_lenght / float(len(segment)-1)

        print("total_lenght:", total_lenght)
        print("segment_part_length:", segment_part_length)

        current_segment_index = 1
        current_length = 0
        for index in range(len(positions)):
            if index == 0:
                continue

            current_length += (positions[index] - positions[index-1]).magnitude

            if current_length > segment_part_length:
                current_length = 0  # segment_part_length

                # todo maybe interpolate between these two points?
                print(current_segment_index, "/", len(segment))

                p = positions[index]

                if current_segment_index != 0 and current_segment_index != len(segment)-1:
                    v = segment[current_segment_index]
                    v.co = p

                    current_segment_index += 1

#        positions = mathutils.geometry.interpolate_bezier(p1.co, p1_knot, p2_knot, p2.co, len(segment))
#        for index, v in enumerate(segment):
#            if index != 0 and index != len(segment)-1:
#                v.co = positions[index]

        # print("." * 66)
        return 0



def circle_3_points(bm, selected, vert_path, tension):
    knots, segments = split_vert_path_into_segments(bm, selected, vert_path)

    vert_a = knots[0]
    vert_b = knots[1]
    vert_c = knots[2]
   
    a = vert_a.co
    b = vert_b.co
    c = vert_c.co

    ac_center = (a+c) * 0.5
    b = b + (b-ac_center).normalized() * tension

    ab = b-a
    bc = c-b
    
    up = ab.cross(bc).normalized()

    p1 = a + ab * 0.5
    p3 = b + bc * 0.5
    p2 = ab.cross(up).normalized()
    p4 = bc.cross(up).normalized()

    intersection = mathutils.geometry.intersect_line_line(p1, p1 + p2, p3, p3 + p4)

    if not intersection: 
        return False
    
    center = intersection[0] 
 
    start = a - center
    middle = b - center
    end = c - center

    radius = (a - center).magnitude

    for index, vert in enumerate(segments[0]):
        mu = index / (len(segments[0])-1)
        interpolated = start.slerp(middle, mu)
        interpolated = interpolated.normalized() * radius
        vert.co = interpolated + center

    for index, vert in enumerate(segments[1]):
        mu = index / (len(segments[1])-1)
        interpolated = middle.slerp(end, mu)
        interpolated = interpolated.normalized() * radius

        vert.co = interpolated + center
    
    return 0, ""


def circle_2_points(bm, selected, vert_path, tension):
    '''
    Spaces the vertices into a half circle between two points, orientation is based on the topology of the first vert
    '''

    vert_a = bm.verts[selected[0]]
    vert_b = bm.verts[selected[1]]
   
    a = vert_a.co
    c = vert_b.co

    center = (a + c) * 0.5
    radius = (a - c).magnitude * 0.5

    n = None
    for corner in vert_a.link_loops:        
        if corner.link_loop_next.vert == vert_path[1]:           
            n = (vert_a.co - corner.link_loop_prev.vert.co).normalized()
            break
        elif corner.link_loop_prev.vert == vert_path[1]:
            n = (corner.link_loop_next.vert.co - vert_a.co).normalized()
            break 

    #n = n.cross(c-a).normalized()
    n = -n
    # n = (vert_a.normal + vert_b.normal).normalized()
    b = center + n * radius

    u = c - center
    v = b - center

    positions = []
    samples = len(vert_path)*100
    for sample in range(samples):
        mu = sample / samples

        t = math.pi - (mu * math.pi)     
        p = center + math.cos(t) * u + math.sin(t) * v * (1.0 + tension)
        
        positions.append(p)

    map_segment_onto_spline(vert_path, positions)

    return 0, ""

'''

OPERATOR

'''


class SetVertexCurveOp(bpy.types.Operator):
    bl_idname = "mesh.align_vertex_curve"
    bl_label = "Align vertices to curve defined by selected vertices."
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = '''Curves vertices between the selected vertices in picking order of the selected vertices.
    2 vertices selected: placed on a half circle between endpoints.
    3 vertices selected: placed onto a circle segment between endpoints.
    4+ vertices selected: placed onto a spline going through selected vertices

    ALT: reuse last settings
    '''

    tension : IntProperty(name="Tension", default=0, min=-500, max=500, description="Tension can be used to tighten up the curvature")
    use_topology_distance : BoolProperty(name="Topology Distance", default=False , description="Use the edge count instead of edge lengths for distance measure") 

    @classmethod
    def poll(cls, context):
        if (context.space_data.type == 'VIEW_3D'
            and context.active_object is not None
            and context.active_object.type == "MESH"
            and context.active_object.mode == 'EDIT'):

            mesh_select_mode = context.scene.tool_settings.mesh_select_mode[:3]
            return mesh_select_mode == (True, False, False)
        else:
            return False

    def get_bm(self, me):
        bm = bmesh.from_edit_mesh(me)
        bm.verts.ensure_lookup_table()
        return bm

    def get_selected(self, bm):        
        maybe_selected = [elem.index for elem in bm.select_history if isinstance(
            elem, bmesh.types.BMVert)]

        selected = list(filter(lambda x: bm.verts[x].select, maybe_selected))
        return selected

    def store_vert_path(self, bm, selected):
        vert_path = collect_vert_path(bm, selected, self.use_topology_distance)

        self.original_positions = []
        for vert in vert_path:
            position = vert.co.copy()
            position = position.freeze()
            self.original_positions.append(position)

    def update_mesh(self, bm, vert_path):
        need_normal_update = set()
        for vert in vert_path:
            for face in vert.link_faces:
                need_normal_update.add(face)
                
        bmesh.ops.recalc_face_normals(bm, faces=list(need_normal_update))
        bmesh.update_edit_mesh(self.obj.data, loop_triangles=True)

    def invoke(self, context, event):
        # print ("-" * 66)
       
        if event and not event.alt:       
            self.tension = 0
            self.use_topology_distance = False
                    
        self.obj = context.object               
        return self.execute(context)

    def execute(self, context):       
        bm = self.get_bm(self.obj.data)
        selected = self.get_selected(bm)      

        if len(selected) < 2:
            self.report({'WARNING'}, f"Align vertex curve: Please select 2, 3 or more vertices")
            return {'CANCELLED'}
        # print ("#" * 66)
               
        vert_path = collect_vert_path(bm, selected, self.use_topology_distance)

        tension = self.tension / 100.0
        
        if len(selected) == 2:            
            result, msg = circle_2_points(bm, selected, vert_path, tension)
        elif len(selected) == 3:
            result, msg = circle_3_points(bm, selected, vert_path, tension)
        else:           
            result, msg = curve_hermite(bm, selected, vert_path, tension)

        if result > 0:
            self.report({'INFO'}, msg)

        self.update_mesh(bm, vert_path)

        return {'FINISHED'}