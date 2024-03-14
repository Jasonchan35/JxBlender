import bpy

from . import (
	graph,
	nla,
	retarget,
	rig,
	rigify,
)

def evaluateAnimation():
	bpy.context.scene.frame_set(bpy.context.scene.frame_current)
	# bpy.context.scene.update()