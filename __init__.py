bl_info = {
    "name": "EdgeFlow",
    "category": "Mesh",
    "author": "Benjamin Sauder",
    "description": "Helps adjusting geometry to curved surfaces",
    "version": (0, 8),
    "location": "Mesh > Edge > Set Edge Flow",
    "blender": (3, 5, 1),
    "tracker_url": "https://github.com/BenjaminSauder/EdgeFlow/issues",
    "wiki_url": "https://github.com/BenjaminSauder/EdgeFlow" ,
}


if "bpy" in locals():
    import importlib

    importlib.reload(util)
    importlib.reload(edgeloop)
    importlib.reload(interpolate)
    importlib.reload(op_set_edge_flow)
    importlib.reload(op_set_edge_linear)
    importlib.reload(op_set_edge_curve)
    importlib.reload(op_set_vertex_curve)
else:
    from . import (
        util,
        interpolate,
        edgeloop,
        op_set_edge_flow,
        op_set_edge_linear,
        op_set_edge_curve,
        op_set_vertex_curve,
    )

    

import bpy
from bpy.types import Menu
from bpy.props import BoolProperty, EnumProperty


def menu_func_edges(self, context):
    layout = self.layout
    layout.separator()
    layout.operator_context = "INVOKE_DEFAULT"

    layout.operator(op_set_edge_flow.SetEdgeFlowOP.bl_idname, text='Set Flow')
    layout.operator(op_set_edge_curve.SetEdgeCurveOP.bl_idname, text='Set Curve')
    layout.operator(op_set_edge_linear.SetEdgeLinearOP.bl_idname, text='Set Linear')

def menu_func_vertices(self, context):
    layout = self.layout
    layout.separator()
    layout.operator_context = "INVOKE_DEFAULT"

    layout.operator(op_set_vertex_curve.SetVertexCurveOp.bl_idname, text='Set Vertex Curve')


list_insertion_options = [
    ("BOTTOM", "Bottom of Menu", "", 1),
    ("TOP", "Top of menu", "", 2),
]

def on_preferences_update(self, context):
    preferences = bpy.context.preferences.addons[__package__].preferences
   
    bpy.types.VIEW3D_MT_edit_mesh_context_menu.remove(menu_func_context_menu)
    
    if preferences.add_to_rightclick_menu:
        if preferences.list_insertion_choice == 'BOTTOM':
            bpy.types.VIEW3D_MT_edit_mesh_context_menu.append(menu_func_context_menu)
        else:
            bpy.types.VIEW3D_MT_edit_mesh_context_menu.prepend(menu_func_context_menu)            
    

class Preferences(bpy.types.AddonPreferences):
    bl_idname = __package__

    add_to_rightclick_menu: BoolProperty(name="Extend rightlick menu", default=True, update=on_preferences_update)
    list_insertion_choice: EnumProperty(name="Add at", items=list_insertion_options, default=2, update=on_preferences_update)
    
    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False  # No animation.
        
        layout.label(text="UI Options")

        col = layout.column(heading="Add commands to rightlick menu")
        col.prop(self, "add_to_rightclick_menu", text="")
       
        row = col.row() 
        row.prop(self, "list_insertion_choice")
        row.enabled = self.add_to_rightclick_menu

class VIEW3D_MT_edit_mesh_set_flow(Menu):
    bl_label = "Set Flow"

    def draw(self, context):
        layout = self.layout

        mesh_select_mode = context.scene.tool_settings.mesh_select_mode[:3]
        if mesh_select_mode == (True, False, False):
          layout.operator(op_set_vertex_curve.SetVertexCurveOp.bl_idname, text='Set Vertex Curve')
        elif mesh_select_mode == (False, True, False):
            layout.operator(op_set_edge_flow.SetEdgeFlowOP.bl_idname, text='Set Flow')
            layout.operator(op_set_edge_curve.SetEdgeCurveOP.bl_idname, text='Set Curve')
            layout.operator(op_set_edge_linear.SetEdgeLinearOP.bl_idname, text='Set Linear')

def menu_func_context_menu(self, context):
    preferences = bpy.context.preferences.addons[__package__].preferences
    
    mesh_select_mode = context.scene.tool_settings.mesh_select_mode[:3]    
    if mesh_select_mode == (True, False, False) or mesh_select_mode == (False, True, False):

        if preferences.list_insertion_choice == 'BOTTOM':
            self.layout.separator()
            
        self.layout.menu("VIEW3D_MT_edit_mesh_set_flow")

        if preferences.list_insertion_choice == 'TOP':
            self.layout.separator()


# stuff which needs to be registered in blender
classes = [
    Preferences,
    op_set_edge_flow.SetEdgeFlowOP,
    op_set_edge_linear.SetEdgeLinearOP,
    op_set_edge_curve.SetEdgeCurveOP,
    op_set_vertex_curve.SetVertexCurveOp,
    VIEW3D_MT_edit_mesh_set_flow,
]

def register():
    for c in classes:
        bpy.utils.register_class(c)

    preferences = bpy.context.preferences.addons[__package__].preferences
    
    bpy.types.VIEW3D_MT_edit_mesh_edges.append(menu_func_edges)
    bpy.types.VIEW3D_MT_edit_mesh_vertices.append(menu_func_vertices)

    if preferences.add_to_rightclick_menu:
        if preferences.list_insertion_choice == 'BOTTOM':
            bpy.types.VIEW3D_MT_edit_mesh_context_menu.append(menu_func_context_menu)
        else:
            bpy.types.VIEW3D_MT_edit_mesh_context_menu.prepend(menu_func_context_menu)

def unregister():
    preferences = bpy.context.preferences.addons[__package__].preferences

    if preferences.add_to_rightclick_menu:
        bpy.types.VIEW3D_MT_edit_mesh_context_menu.remove(menu_func_context_menu)
    
    bpy.types.VIEW3D_MT_edit_mesh_edges.remove(menu_func_edges)
    bpy.types.VIEW3D_MT_edit_mesh_vertices.remove(menu_func_vertices)

    for c in classes:
        bpy.utils.unregister_class(c)




