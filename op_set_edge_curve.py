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

    rail_mode = (
        ("ABSOLUTE", "Absolute", "", 1),
        ("FACTOR", "Factor", "", 2),
    )

    mix: FloatProperty(name="Mix", default=1.0, min=0.0, max=1.0, subtype='FACTOR', description="Interpolate between inital position and the calculated end position")
    tension : IntProperty(name="Tension", default=100, soft_min=-500, soft_max=500, description="Tension can be used to tighten up the curvature")

    use_rail : BoolProperty(name="Use Rail", default=False, description="Customize the interpolation by using the first and last edge of the edgeloop to control the curvature")
    rail_mode: bpy.props.EnumProperty(name="Rail Mode", items=rail_mode, default=2, description="Switch rail mode between using absolute units or a factor of the length of the edge")
    rail_start_width : FloatProperty(name="Rail Start", default=1.0, subtype='DISTANCE', description="Choose how long the rail is at the start")
    rail_end_width : FloatProperty(name="Rail End", default=1.0, subtype='DISTANCE', description="Choose how long the rail is at the end")
    rail_start_factor : FloatProperty(name="Rail Start", default=1.0, soft_min=0.0, soft_max=1.5, subtype='FACTOR', description="Choose how long the rail is at the start")
    rail_end_factor : FloatProperty(name="Rail End", default=1.0, soft_min=0.0, soft_max=1.5, subtype='FACTOR', description="Choose how long the rail is at the end")
   
    def execute(self, context):
        if not self.is_invoked:        
            return self.invoke(context, None)
        else:
            self.revert_to_intial_positions()

        refresh_positions = self.mix == self.last_mix

        if refresh_positions:
            for obj in self.objects:            
                for edgeloop in self.edgeloops[obj]:
                    if self.rail_mode == 'ABSOLUTE':
                        rail_start = self.rail_start_width    
                        rail_end = self.rail_end_width
                    else:
                        rail_start = self.rail_start_factor
                        rail_end = self.rail_end_factor

                    edgeloop.set_curve_flow(self.tension / 100.0, self.use_rail, self.rail_mode, rail_start, rail_end)
                
                self.store_final_positions()

        self.apply_mix()

        for obj in self.objects:            
            self.bm[obj].normal_update()
            bmesh.update_edit_mesh(obj.data)

        self.last_mix = self.mix
        self.is_invoked = False
        return {'FINISHED'}

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True 
        column = layout.column(align=True)
        
        column.prop(self, "mix")
        column.prop(self, "tension")
        column.separator()

        column.prop(self, "use_rail")

        # Create a sub layout so that we can grey-out this if use_rail is unchecked
        sub_column = column.column(align=True)
        row = sub_column.row()
        row.prop(self, "rail_mode", expand=True)

        if self.rail_mode == 'ABSOLUTE':
            sub_column.prop(self, "rail_start_width", slider=False)
            sub_column.prop(self, "rail_end_width", slider=False)
        else:
            sub_column.prop(self, "rail_start_factor")
            sub_column.prop(self, "rail_end_factor")
        
        sub_column.enabled = self.use_rail

    def invoke(self, context, event):
        super(SetEdgeCurveOP, self).invoke(context)
     
        if event and not event.alt:
            self.tension = 100
            self.mix = 1.0

        return self.execute(context)