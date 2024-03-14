import bpy
import jx.util

def safeSetPropValue(target, propName, value):
	if propName in target:
		target[propName] = value

def resetAllBonesTransforms(rig):
	if not rig or rig.type != 'ARMATURE': return
	for poseBone in rig.pose.bones:
		poseBone.location = (0,0,0)
		poseBone.rotation_quaternion = (1,0,0,0)
		poseBone.rotation_euler = (0,0,0)
		poseBone.scale = (1,1,1)

		safeSetPropValue(poseBone, "neck_follow", 0.5)
		safeSetPropValue(poseBone, "head_follow", 0)
		safeSetPropValue(poseBone, "rubber_tweak", 0)

		safeSetPropValue(poseBone, "FK_limb_follow", 0)
		safeSetPropValue(poseBone, "IK_parent",  1)
		safeSetPropValue(poseBone, "IK_Stretch", 0)
		safeSetPropValue(poseBone, "IK_FK", 0)
		safeSetPropValue(poseBone, "pole_vector", 0)

		if poseBone.name.startswith("upper_arm_parent."):
			safeSetPropValue(poseBone, "pole_parent", 3)
		elif poseBone.name.startswith("thigh_parent."):
			safeSetPropValue(poseBone, "pole_parent", 6)
	

	jx.anim.evaluateAnimation()

def hasTrack(rig, trackName):
	for t in rig.animation_data.nla_tracks:
		if t.name == trackName:
			return True
	return False

def animationRange(rig):
	start = float("inf")
	end   = float("-inf")

	anim = rig.animation_data
	if anim != None and anim.action != None:
		for fcu in anim.action.fcurves:
			n = len(fcu.keyframe_points)
			if n <= 0: continue
			first = fcu.keyframe_points[0]
			last  = fcu.keyframe_points[n - 1]

			start = min(start, first.co.x)
			end   = max(end,   first.co.x)

			start = min(start, last.co.x)
			end   = max(end,   last.co.x)
	
	return start, end

def bakeRig(rig, clear_constraints = True):
	bpy.context.view_layer.objects.active = rig	
	bpy.ops.object.mode_set(mode='POSE')
	bpy.ops.pose.select_all(action='DESELECT')

	frame_start, frame_end = animationRange(rig)

	for poseBone in rig.pose.bones:
		poseBone.bone.select = True

	bpy.ops.nla.bake(
		frame_start = bpy.context.scene.frame_start,
		frame_end   = bpy.context.scene.frame_end,
		step = 1,
		visual_keying = True,
		clean_curves = True,
		clear_constraints = clear_constraints,
		bake_types = {'POSE'}
	)

def removeAllBones(rig):
	jx.util.clearPropCollection(rig.data.edit_bones)

def removeAllConstraints(rig):
	for poseBone in rig.pose.bones:
		jx.util.clearPropCollection(poseBone.constraints)

def removeAllCurves(rig):
	anim = rig.animation_data
	if anim != None and anim.action != None:
		jx.util.clearPropCollection(anim.action.fcurves)

def removeBoneWeight(boneName, skin):
	if boneName in skin.vertex_groups:
		g = skin.vertex_groups[boneName]
		skin.vertex_groups.remove(g)

def removeNonDeformBoneWeight(rig, skin):
	for bone in rig.data.bones:
		if bone.use_deform: continue
		removeBoneWeight(bone.name, skin)
