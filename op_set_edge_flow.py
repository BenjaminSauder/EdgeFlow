import math
import bpy
from bpy.props import IntProperty, FloatProperty, EnumProperty
import bmesh
from . import util


class SetEdgeLoopBase():

    def get_bm(self, obj):
        bm = bmesh.new()
        bm.from_mesh(obj.data)
        bm.normal_update()
        bm.verts.ensure_lookup_table()
        return bm

    def revert(self):
        # print("reverting vertex positions")
        for vert, pos in self.vert_positions.items():
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
        print("base invoke")
        self.obj = context.active_object

        bpy.ops.object.mode_set(mode='OBJECT')
        self.bm = self.get_bm(self.obj)

        edges = [e for e in self.bm.edges if e.select]

        if len(edges) == 0:
            print("no edges selected")
            bpy.ops.object.mode_set(mode='EDIT')
            return {'CANCELLED'}

        self.edges = edges

        self.vert_positions = {}
        for e in edges:
            for v in e.verts:
                if v not in self.vert_positions:
                    # print("storing: %s " % v.co)
                    p = v.co.copy()
                    p = p.freeze()
                    self.vert_positions[v] = p

        self.edgeloops = util.get_edgeloops(self.bm, self.edges)

        return {'PASS_THROUGH'}



class SetEdgeFlowOP(bpy.types.Operator, SetEdgeLoopBase):

    bl_idname = "mesh.set_edge_flow"
    bl_label = "Set edge flow"
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = "adjust edge loops to curvature"

    tension : IntProperty(name="Tension", default=180, min=-500, max=500)
    iterations : IntProperty(name="Iterations", default=1, min=1, max=32)
    #bias = IntProperty(name="Bias", default=0, min=-100, max=100)
    min_angle : IntProperty(name="Min Angle", default=0, min=0, max=180, subtype='FACTOR' )


    def execute(self, context):
        #print ("execute")
        bpy.ops.object.mode_set(mode='OBJECT')

        self.revert()

        for i in range(self.iterations):
            for edgeloop in self.edgeloops:
                edgeloop.set_flow(self.tension / 100.0, math.radians(self.min_angle) )

        self.bm.to_mesh(self.obj.data)
        bpy.ops.object.mode_set(mode='EDIT')

        return {'FINISHED'}

    def invoke(self, context, event):
        #print("invoke")

        self.tension = 180
        self.iterations = 1
        self.bias = 0
        #self.min_angle = 0

        result = super(SetEdgeFlowOP, self).invoke(context)

        if "CANCELLED" in result:
            return  result

        return self.execute(context)



