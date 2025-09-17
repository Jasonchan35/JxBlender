# Open this file in Blender Script Editor for qui3ck test
# Debug Console - Main Menu > Window > Toggle System Console

import bpy
import os
import jx.anim.rigify

os.system("cls")

def reload_addon(name):
    import addon_utils
    addon_utils.disable(name)
    addon_utils.enable(name)
reload_addon("jx")

#---------------------

def gen_rig():
    metarig = bpy.context.view_layer.objects["metarig"]
    bpy.context.view_layer.objects.active = metarig
    bpy.ops.pose.rigify_generate()
        
def test_create_deform_rig():
    rig = bpy.context.view_layer.objects["rig"]    
    jx.anim.rigify.create_deform_rig(rig)

#gen_rig()
#test_create_deform_rig()
#bpy.ops.jx.export_to_fbx_all_anim_tracks()
