import bpy
from bpy.props import BoolProperty, FloatProperty, EnumProperty
import bmesh

from . import util
from . import op_set_edge_flow


class SetEdgeLinearOP(bpy.types.Operator, op_set_edge_flow.SetEdgeLoopBase):
    bl_idname = "mesh.set_edge_linear"
    bl_label = "Set Edge Linear"
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = "Makes edge loops linear between start and end vertices"

    space_evenly: BoolProperty(name="Space evenly", default=False,
                               description="Spread the vertices in even distances")

    def invoke(self, context, event):
        super(SetEdgeLinearOP, self).invoke(context)

        if event and not event.alt:
            self.mix = 1.0

        return self.execute(context)

    def can_straighten(self):
        for obj in self.objects:
            for edgeloop in self.edgeloops[obj]:
                if len(edgeloop.edges) != 1:
                    return False

        return True

    def execute(self, context):
        if not self.is_invoked:
            return self.invoke(context, None)
        else:
            self.revert_to_intial_positions()

        refresh_positions = self.mix == self.last_mix

        if refresh_positions:
            for obj in self.objects:
                for edgeloop in self.edgeloops[obj]:
                    edgeloop.set_linear(self.space_evenly)
            self.store_final_positions()

        self.apply_mix()

        for obj in self.objects:
            self.bm[obj].normal_update()
            bmesh.update_edit_mesh(obj.data)

        self.last_mix = self.mix
        self.is_invoked = False
        return {'FINISHED'}
