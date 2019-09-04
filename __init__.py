bl_info = {
    "name": "EdgeFlow",
    "category": "Mesh",
    "author": "Benjamin Sauder",
    "description": "helps adjusting edge loops",
    "version": (0, 5),
    "location": "Mesh > Edge > Set Edge Flow",
    "blender": (2, 80, 0),
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
else:

    from . import (
        prefs,
        util,
        interpolate,
        edgeloop,
        op_set_edge_flow,
        op_set_edge_linear,
    )

import bpy
from bpy.app.handlers import persistent

# stuff which needs to be registered in blender
classes = [
    op_set_edge_flow.SetEdgeFlowOP,
    op_set_edge_linear.SetEdgeLinearOP,
]


@persistent
def scene_update_post_handler(dummy):
    pass

def menu_func(self, context):
    layout = self.layout
    layout.separator()

    layout.operator_context = "INVOKE_DEFAULT"

    layout.operator(op_set_edge_flow.SetEdgeFlowOP.bl_idname, text='Set Flow')
    layout.operator(op_set_edge_linear.SetEdgeLinearOP.bl_idname, text='Set Linear')


def register():
    if prefs.isDebug:
        print("register")

    for c in classes:
        bpy.utils.register_class(c)

    bpy.types.VIEW3D_MT_edit_mesh_edges.append(menu_func)
    bpy.types.VIEW3D_MT_edit_mesh_context_menu.append(menu_func)

def unregister():
    if prefs.isDebug:
        print("unregister")

    for c in classes:
        bpy.utils.unregister_class(c)

    bpy.types.VIEW3D_MT_edit_mesh_edges.remove(menu_func)
    bpy.types.VIEW3D_MT_edit_mesh_context_menu.remove(menu_func)


