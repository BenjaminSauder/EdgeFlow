import bpy
from bpy.props import BoolProperty, FloatProperty, EnumProperty
import bmesh

from . import util
from . import op_set_edge_flow


class SetEdgeLinearOP(bpy.types.Operator, op_set_edge_flow.SetEdgeLoopBase):
    bl_idname = "mesh.set_edge_linear"
    bl_label = "Set edge linear"
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = "makes edge loops linear"

    space_evenly : BoolProperty(name="Space evenly", default=False)
    distance : FloatProperty(name="Distance", default=1.0, min=0)

    def draw(self, context):
        layout = self.layout
        column = layout.column()
        if self.do_straighten():
            column.prop(self, "distance")
        else:
            column.prop(self, "space_evenly")

    def invoke(self, context, event):
        print("--------------------")
        result = super(SetEdgeLinearOP, self).invoke(context)

        if "CANCELLED" in result:
            return result

        if self.do_straighten():
            distance = 0
            for edgeloop in self.edgeloops:
                distance += edgeloop.get_average_distance()
            distance /= len(self.edgeloops)

            self.distance = distance * 0.35

        return self.execute(context)

    def do_straighten(self):
        for edgeloop in self.edgeloops:
            if len(edgeloop.edges) != 1:
                return False

        return True

    def execute(self, context):
        print("execute")
        bpy.ops.object.mode_set(mode='OBJECT')

        self.revert()

        for edgeloop in self.edgeloops:
            if self.do_straighten():
                edgeloop.straighten(self.distance)
            else:
                edgeloop.set_linear(self.space_evenly)

        self.bm.to_mesh(self.obj.data)
        bpy.ops.object.mode_set(mode='EDIT')
        return {'FINISHED'}
