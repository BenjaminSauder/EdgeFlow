import math
import time
import bpy
from bpy.props import IntProperty, FloatProperty, EnumProperty

from . import op_set_edge_flow

time_last_called = 0

class SetEdgeCurveOP(bpy.types.Operator, op_set_edge_flow.SetEdgeLoopBase):

    bl_idname = "mesh.set_edge_curve"
    bl_label = "Set edge curve"
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = "adjust edge loops to curvature"

    tension : IntProperty(name="Tension", default=100, soft_min=-500, soft_max=500, description="Tension can be used to tighten up the curvature")
    mix: FloatProperty(name="Mix", default=1.0, min=0.0, max=1.0, description="Interpolate between inital position and the calculated end position")

  
    def execute(self, context):
        # print ("execute")

        if not self.is_invoked:        
            return self.invoke(context, None)

        bpy.ops.object.mode_set(mode='OBJECT')

        self.revert()

        for obj in self.objects:            
            for edgeloop in self.edgeloops[obj]:
                edgeloop.set_curve_flow(self.tension / 100.0, self.mix)

            self.bm[obj].to_mesh(obj.data)

        bpy.ops.object.mode_set(mode='EDIT')
        self.is_invoked = False
        return {'FINISHED'}

    def invoke(self, context, event):
        # print("invoke")

        super(SetEdgeCurveOP, self).invoke(context)
     
        global time_last_called

        if time.time() > time_last_called + op_set_edge_flow.RESET_TO_DEFAULTS_DURATION: 
            time_last_called = time.time()
            self.tension = 100
            self.mix = 1.0          


        return self.execute(context)