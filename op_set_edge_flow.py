import math
import time
import bpy
from bpy.props import IntProperty, FloatProperty, EnumProperty
import bmesh
from . import util

RESET_TO_DEFAULTS_DURATION = 15.0
time_last_called = time.time()

class SetEdgeLoopBase():

    def __init__(self):
        self.is_invoked = False
        

    def get_bm(self, obj):
        bm = bmesh.new()
        bm.from_mesh(obj.data)
        bm.normal_update()
        bm.verts.ensure_lookup_table()
        return bm

    def revert(self):
        # print("reverting vertex positions")
        for obj in self.objects:
            for edgeloop in self.edgeloops[obj]:
                for i, vert in enumerate(edgeloop.verts):
                    vert.co = edgeloop.initial_vert_positions[i]      

    @classmethod
    def poll(cls, context):
        return (
            context.space_data.type == 'VIEW_3D'
            and context.active_object is not None
            and context.active_object.type == "MESH"
            and context.active_object.mode == 'EDIT')

    def invoke(self, context):
        #print("base invoke")
        self.is_invoked = True

        self.objects = set(context.selected_editable_objects) if context.selected_editable_objects else set([context.object])
        self.bm = {}
        self.edgeloops = {}
        self.vert_positions = {}

        bpy.ops.object.mode_set(mode='OBJECT')

        ignore = set()

        for obj in self.objects:
            self.bm[obj] = self.get_bm(obj)

            edges = [e for e in self.bm[obj].edges if e.select]
            if len(edges) == 0:
                ignore.add(obj)
                continue
          
            self.edgeloops[obj] = util.get_edgeloops(self.bm[obj], edges)

        self.objects = self.objects - ignore


class SetEdgeFlowOP(bpy.types.Operator, SetEdgeLoopBase):

    bl_idname = "mesh.set_edge_flow"
    bl_label = "Set edge flow"
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = "Adjust edge loops to match surface curvature\nALT: reuse last settings"

    enum_blend = (
        ("LINEAR", "Linear", ""),
        ("SMOOTH", "Smooth", ""),
        )

    mix: FloatProperty(name="Mix", default=1.0, min=0.0, max=1.0, subtype='FACTOR', description="Interpolate between inital position and the calculated end position")
    
    tension: IntProperty(name="Tension", default=180, min=-500, max=500, description="Tension can be used to tighten up the curvature")
    #bias: IntProperty(name="Bias", default=0, min=-100, max=100)
    iterations: IntProperty(name="Iterations", default=1, min=1, soft_max=32, description="How often the curveature operation is repeated")
    
    blend_start: bpy.props.FloatProperty(name="Blend Start", default=0.0, min=0.0, max=1.0, subtype='FACTOR', description="Loop fraction from the start of the loop used to blend to the adjusted loop position")
    blend_end: bpy.props.FloatProperty(name="Blend End", default=0.0, min=0.0, max=1.0, subtype='FACTOR', description="Loop fraction from the end of the loop used to blend to the adjusted loop position")
    blend_type: bpy.props.EnumProperty(name="Blend Curve", items=enum_blend, description="The interpolation used to blend between the adjusted loop position and the unaffected start and/or end points")
    
    min_angle : IntProperty(name="Min Angle", default=0, min=0, max=180, subtype='FACTOR', description="After which angle the edgeloop curvature is ignored")


    def execute(self, context):
        # print ("execute")
     
        if not self.is_invoked:        
            return self.invoke(context, None)

        bpy.ops.object.mode_set(mode='OBJECT')

        self.revert()

        for obj in self.objects:
            for i in range(self.iterations):
                for edgeloop in self.edgeloops[obj]:
                    edgeloop.set_flow(tension=self.tension / 100.0,
                                      min_angle=math.radians(self.min_angle))

            for edgeloop in self.edgeloops[obj]:
                edgeloop.blend_start_end(blend_start=self.blend_start, blend_end=self.blend_end, blend_type=self.blend_type)

                if self.mix < 1.0:
                    for i, vert in enumerate(edgeloop.verts):
                        vert.co = edgeloop.initial_vert_positions[i].lerp(vert.co, self.mix)

            self.bm[obj].to_mesh(obj.data)

        bpy.ops.object.mode_set(mode='EDIT')

        self.is_invoked = False

        return {'FINISHED'}

    def invoke(self, context, event):
        # print("invoke")

        super(SetEdgeFlowOP, self).invoke(context)
          
        if event and not event.alt:            
            self.tension = 180
            self.iterations = 1           
            self.mix = 1.0
            self.min_angle = 0
            self.blend_start = 0
            self.blend_end = 0

        return self.execute(context)



