import bpy

@property
def isDebug():
    # return True
    return bpy.app.debug_value != 0