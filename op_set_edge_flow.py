import math
import bpy
from bpy.props import IntProperty, FloatProperty, EnumProperty
import bmesh
from . import util


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
            if  obj in self.vert_positions:
                for vert, pos in self.vert_positions[obj].items():
                    # print("revert: %s -> %s" % (vert.index, pos))
                    vert.co = pos

    @classmethod
    def poll(cls, context):
        return (
            context.space_data.type == 'VIEW_3D'
            and context.active_object is not None
            and context.active_object.type == "MESH"
            and context.active_object.mode == 'EDIT')

    def invoke(self, context):
        # print("base invoke")
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
            
            self.vert_positions[obj] = {}
            for e in edges:
                for v in e.verts:
                    if v not in self.vert_positions[obj]:
                        # print("storing: %s " % v.co)
                        p = v.co.copy()
                        p = p.freeze()
                        self.vert_positions[obj][v] = p

            self.edgeloops[obj] = util.get_edgeloops(self.bm[obj], edges)

        self.objects = self.objects - ignore


class SetEdgeFlowOP(bpy.types.Operator, SetEdgeLoopBase):

    bl_idname = "mesh.set_edge_flow"
    bl_label = "Set edge flow"
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = "adjust edge loops to curvature"

    tension : IntProperty(name="Tension", default=180, min=-500, max=500)
    iterations : IntProperty(name="Iterations", default=1, min=1, soft_max=32)
    #bias = IntProperty(name="Bias", default=0, min=-100, max=100)
    min_angle : IntProperty(name="Min Angle", default=0, min=0, max=180, subtype='FACTOR' )


    def execute(self, context):
        # print ("execute")
        # print(f"Tension:{self.tension} Iterations:{self.iterations}")

        if not self.is_invoked:        
            return self.invoke(context, None)

        bpy.ops.object.mode_set(mode='OBJECT')

        self.revert()

        for obj in self.objects:
            for i in range(self.iterations):
                for edgeloop in self.edgeloops[obj]:
                    edgeloop.set_flow(self.tension / 100.0, math.radians(self.min_angle) )

            self.bm[obj].to_mesh(obj.data)

        bpy.ops.object.mode_set(mode='EDIT')

        return {'FINISHED'}

    def invoke(self, context, event):
        # print("invoke")

        if event:
            self.tension = 180
            self.iterations = 1
            self.bias = 0
            #self.min_angle = 0

        super(SetEdgeFlowOP, self).invoke(context)
       
        return self.execute(context)



