import math
import time
import bpy
from bpy.props import BoolProperty, IntProperty, FloatProperty, EnumProperty

from . import op_set_edge_flow

class SetEdgeCurveOP(bpy.types.Operator, op_set_edge_flow.SetEdgeLoopBase):

    bl_idname = "mesh.set_edge_curve"
    bl_label = "Set Edge Curve"
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = "Adjust edge loops to loop curvature\nALT: reuse last settings"

    mix: FloatProperty(name="Mix", default=1.0, min=0.0, max=1.0, subtype='FACTOR', description="Interpolate between inital position and the calculated end position")
    tension : IntProperty(name="Tension", default=100, soft_min=-500, soft_max=500, description="Tension can be used to tighten up the curvature")
    use_rail : BoolProperty(name="Use Rail", default=False, description="The first and last edge stay in place")
   
    def execute(self, context):
        # print ("execute")

        if not self.is_invoked:        
            return self.invoke(context, None)

        bpy.ops.object.mode_set(mode='OBJECT')

        self.revert()

        for obj in self.objects:            
            for edgeloop in self.edgeloops[obj]:
                edgeloop.set_curve_flow(self.tension / 100.0, self.use_rail)
            
            if self.mix < 1.0:
                for i, vert in enumerate(edgeloop.verts):
                    vert.co = edgeloop.initial_vert_positions[i].lerp(vert.co, self.mix)

            self.bm[obj].to_mesh(obj.data)

        bpy.ops.object.mode_set(mode='EDIT')
        self.is_invoked = False
        return {'FINISHED'}

    def invoke(self, context, event):
        # print("invoke")

        super(SetEdgeCurveOP, self).invoke(context)
     
        if event and not event.alt:
            self.tension = 100
            self.mix = 1.0          


        return self.execute(context)