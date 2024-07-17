import math
import time
import bpy
from bpy.props import IntProperty, FloatProperty, EnumProperty
import bmesh
from . import util

class SetEdgeLoopBase():

    mix: FloatProperty(name="Mix", default=1.0, min=0.0, max=1.0, subtype='FACTOR', description="Interpolate between inital position and the calculated end position")

    def __init__(self):
        self.is_invoked = False

        self.last_mix = self.mix
        
        self.intial_vert_positions = {}
        self.final_vert_positions = {}

    def get_bm(self, obj):        
        bm = bmesh.from_edit_mesh(obj.data)
        bm.verts.ensure_lookup_table()
        return bm

    def revert_to_intial_positions(self):        
        for obj in self.objects:
            for index, pos in self.intial_vert_positions[obj].items():
                vert = self.bm[obj].verts[index]
                vert.co = pos

    def store_final_positions(self):        
        self.final_vert_positions = {}
        for obj in self.objects:
            self.final_vert_positions[obj] = {}
            for index in self.intial_vert_positions[obj].keys():
                v = self.bm[obj].verts[index]
                p = v.co.copy()            
                self.final_vert_positions[obj][v.index] = p

    def apply_mix(self):             
        if self.mix < 1.0 or (self.mix == 1.0 and self.last_mix < 1.0):
            for obj in self.objects:
                for edgeloop in self.edgeloops[obj]:
                    for vert in edgeloop.verts:
                        a = self.intial_vert_positions[obj][vert.index]
                        b = self.final_vert_positions[obj][vert.index]
                        vert.co = a.lerp(b, self.mix)            
         

    @classmethod
    def poll(cls, context):
        return (
            context.space_data.type == 'VIEW_3D'
            and context.active_object is not None
            and context.active_object.type == "MESH"
            and context.active_object.mode == 'EDIT')

    '''
    The base invoke stores affected objects, bmesh and intial vertex positions.
    The 'redo' calls by the undo system makes the bm invalid - so i have to look it up again...
    The storing of the intial vertex positions should only happen on the intial code path.  
    '''
    def invoke(self, context):
        self.is_invoked = True

        self.objects = set(context.selected_editable_objects) if context.selected_editable_objects else set([context.object])
        self.bm = {}
        self.edgeloops = {}
                
        store_intial_positions = not self.intial_vert_positions

        ignore = set()
        for obj in self.objects:
            if obj.mode != 'EDIT':
                ignore.add(obj)
                continue

            bm = self.get_bm(obj)
            edges = [e for e in bm.edges if e.select]
            if len(edges) == 0:
                ignore.add(obj)
                continue

            self.bm[obj] = bm
            edge_loops = util.get_edgeloops(bm, edges)
            self.edgeloops[obj] = edge_loops

            if store_intial_positions:
                self.intial_vert_positions[obj] = {}
                for e in edges:
                    for v in e.verts:
                        if v.index not in self.intial_vert_positions[obj]:
                            p = v.co.copy()
                            p = p.freeze()
                            self.intial_vert_positions[obj][v.index] = p

        self.objects = self.objects - ignore


class SetEdgeFlowOP(bpy.types.Operator, SetEdgeLoopBase):

    bl_idname = "mesh.set_edge_flow"
    bl_label = "Set Edge Flow"
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = "Adjust curvature to match surface defined by edges crossing the edgeloop\nALT: reuse last settings"

    blend_mode = (
        ("ABSOLUTE", "Absolute", "", 1),
        ("FACTOR", "Factor", "", 2),
    )

    blend_type = (
        ("LINEAR", "Linear", ""),
        ("SMOOTH", "Smooth", ""),
    )   
    
    tension: IntProperty(name="Tension", default=180, min=-500, max=500, description="Tension can be used to tighten up the curvature")    
    iterations: IntProperty(name="Iterations", default=8, min=1, soft_max=32, description="How often the curveature operation is repeated")
    
    blend_mode: bpy.props.EnumProperty(name="Blend Mode", items=blend_mode, description="Switch blend mode between absolute vertex counts and a factor of the whole edgeloop")
    blend_start_int: bpy.props.IntProperty(name="Blend Start", default=0, min=0, description="The number of vertices from the start of the loop used to blend to the adjusted loop position")
    blend_end_int: bpy.props.IntProperty(name="Blend End", default=0, min=0, description="The number of vertices from the end of the loop used to blend to the adjusted loop position")
    blend_start_float: bpy.props.FloatProperty(name="Blend Start", default=0.0, min=0.0, max=1.0, subtype='FACTOR', description="Loop fraction from the start of the loop used to blend to the adjusted loop position")
    blend_end_float: bpy.props.FloatProperty(name="Blend End", default=0.0, min=0.0, max=1.0, subtype='FACTOR', description="Loop fraction from the end of the loop used to blend to the adjusted loop position")
    blend_type: bpy.props.EnumProperty(name="Blend Curve", items=blend_type, description="The interpolation used to blend between the adjusted loop position and the unaffected start and/or end points")
    
    min_angle : IntProperty(name="Min Angle", default=0, min=0, max=180, subtype='FACTOR', description="After which angle the edgeloop curvature is ignored")


    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True 
        column = layout.column(align=True)
        
        column.prop(self, "mix")
        column.prop(self, "tension")
        column.prop(self, "iterations")
        column.prop(self, "min_angle")
        column.separator()

        row = column.row()
        row.prop(self, "blend_mode", expand=True)
        
        if self.blend_mode == 'ABSOLUTE':
            column.prop(self, "blend_start_int")
            column.prop(self, "blend_end_int")
        else:
            column.prop(self, "blend_start_float")
            column.prop(self, "blend_end_float")

        row = column.row()
        row.prop(self, "blend_type", expand=True)
             

    def execute(self, context):
     
        if not self.is_invoked:             
            return self.invoke(context, None)

        refresh_positions = self.mix == self.last_mix
        
        if refresh_positions:  
            for obj in self.objects:
                for i in range(self.iterations):
                    for edgeloop in self.edgeloops[obj]:
                        edgeloop.set_flow(tension=self.tension / 100.0,
                                        min_angle=math.radians(self.min_angle))

                for edgeloop in self.edgeloops[obj]:
                    if self.blend_mode == 'ABSOLUTE':
                        start = self.blend_start_int
                        end = self.blend_end_int
                    else:
                        count = len(edgeloop.verts)
                        start = round(count * self.blend_start_float)
                        end = round(count * self.blend_end_float)
                
                edgeloop.blend_start_end(blend_start=start, blend_end=end, blend_type=self.blend_type)
        
            self.store_final_positions()

        self.apply_mix()

        for obj in self.objects:
            self.bm[obj].normal_update()
            bmesh.update_edit_mesh(obj.data)

        self.last_mix = self.mix
        self.is_invoked = False
        return {'FINISHED'}


    def invoke(self, context, event):
        super(SetEdgeFlowOP, self).invoke(context)
          
        if event and not event.alt:     
            self.mix = 1.0
            self.tension = 180
            self.iterations = 16           
            self.min_angle = 0
            self.blend_start_int = 0
            self.blend_end_int = 0
            self.blend_start_float = 0
            self.blend_end_float = 0

        return self.execute(context)



