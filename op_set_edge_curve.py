import math
import time
import bpy
from bpy.props import BoolProperty, IntProperty, FloatProperty, EnumProperty
import bmesh

from . import op_set_edge_flow

class SetEdgeCurveOP(bpy.types.Operator, op_set_edge_flow.SetEdgeLoopBase):

    bl_idname = "mesh.set_edge_curve"
    bl_label = "Set Edge Curve"
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = "Adjust curvature along the direction the edgeloop\nALT: reuse last settings"

    mix: FloatProperty(name="Mix", default=1.0, min=0.0, max=1.0, subtype='FACTOR', description="Interpolate between inital position and the calculated end position")
    tension : IntProperty(name="Tension", default=100, soft_min=-500, soft_max=500, description="Tension can be used to tighten up the curvature")
    use_rail : BoolProperty(name="Use Rail", default=False, description="The first and last edge stay in place")
   
    def execute(self, context):
        if not self.is_invoked:        
            return self.invoke(context, None)
        else:
            self.revert_to_intial_positions()

        refresh_positions = self.mix == self.last_mix

        if refresh_positions:
            for obj in self.objects:            
                for edgeloop in self.edgeloops[obj]:
                    edgeloop.set_curve_flow(self.tension / 100.0, self.use_rail)

            self.store_final_positions()

        self.apply_mix()

        for obj in self.objects:            
            self.bm[obj].normal_update()
            bmesh.update_edit_mesh(obj.data)

        self.last_mix = self.mix
        self.is_invoked = False
        return {'FINISHED'}

    def invoke(self, context, event):
        super(SetEdgeCurveOP, self).invoke(context)
     
        if event and not event.alt:
            self.mix = 1.0 
            self.tension = 100

        return self.execute(context)