import bpy
from bpy.props import BoolProperty, FloatProperty, EnumProperty
import bmesh

from . import util
from . import op_set_edge_flow


class SetEdgeLinearOP(bpy.types.Operator, op_set_edge_flow.SetEdgeLoopBase):
    bl_idname = "mesh.set_edge_linear"
    bl_label = "Set edge linear"
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = "Makes edge loops linear between start and end vertices"

    space_evenly : BoolProperty(name="Space evenly", default=False, description="Spread the vertices in even distances")
   
    def invoke(self, context, event):
       
        super(SetEdgeLinearOP, self).invoke(context)
        return self.execute(context)

    def can_straighten(self):
        for obj in self.objects:
            for edgeloop in self.edgeloops[obj]:
                if len(edgeloop.edges) != 1:
                    return False

        return True

    def execute(self, context):
        #print("execute")
      
        if not self.is_invoked:        
            return self.invoke(context, None)

        bpy.ops.object.mode_set(mode='OBJECT')

        self.revert()

        for obj in self.objects:
            for edgeloop in self.edgeloops[obj]:               
                edgeloop.set_linear(self.space_evenly)

            self.bm[obj].to_mesh(obj.data)

        bpy.ops.object.mode_set(mode='EDIT')
        self.is_invoked = False
        return {'FINISHED'}
