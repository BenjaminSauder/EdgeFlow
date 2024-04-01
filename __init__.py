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

    importlib.reload(prefs)
    importlib.reload(util)
    importlib.reload(edgeloop)
    importlib.reload(interpolate)
    importlib.reload(op_set_edge_flow)
    importlib.reload(op_set_edge_linear)
    importlib.reload(op_set_edge_curve)
    importlib.reload(op_set_vertex_curve)
else:
    from . import (
        prefs,
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


class VIEW3D_MT_edit_mesh_edge_flow(Menu):
    bl_label = "Edge Flow"

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

    mesh_select_mode = context.scene.tool_settings.mesh_select_mode[:3]    
    if mesh_select_mode == (True, False, False) or mesh_select_mode == (False, True, False):
        self.layout.menu("VIEW3D_MT_edit_mesh_edge_flow")
        self.layout.separator()


# stuff which needs to be registered in blender
classes = [
    op_set_edge_flow.SetEdgeFlowOP,
    op_set_edge_linear.SetEdgeLinearOP,
    op_set_edge_curve.SetEdgeCurveOP,
    op_set_vertex_curve.SetVertexCurveOp,
    VIEW3D_MT_edit_mesh_edge_flow,
]

def register():
    if prefs.isDebug:
        print("register")

    for c in classes:
        bpy.utils.register_class(c)

    bpy.types.VIEW3D_MT_edit_mesh_edges.append(menu_func_edges)
    bpy.types.VIEW3D_MT_edit_mesh_vertices.append(menu_func_vertices)

    bpy.types.VIEW3D_MT_edit_mesh_context_menu.prepend(menu_func_context_menu)

def unregister():
    if prefs.isDebug:
        print("unregister")

    for c in classes:
        bpy.utils.unregister_class(c)

    bpy.types.VIEW3D_MT_edit_mesh_edges.remove(menu_func_edges)
    bpy.types.VIEW3D_MT_edit_mesh_vertices.remove(menu_func_vertices)

    bpy.types.VIEW3D_MT_edit_mesh_context_menu.remove(menu_func_context_menu)


