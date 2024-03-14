import bpy
import jx.types
import jx.util
import jx.anim.rig

from mathutils import Euler
from mathutils import Vector
from mathutils import Matrix

g_rootMotionBoneName = "JX-RootMotion"

ikHandlerBones = [
	"hand_ik.L",
	"hand_ik.R",
	"foot_ik.L",
	"foot_ik.R",
	"foot_heel_ik.L",
	"foot_heel_ik.R",
	"thigh_ik_target.L",
	"thigh_ik_target.R",
]

heelToeFoots = [
	"MCH-thigh_ik_target.L",
	"MCH-thigh_ik_target.R",
]

def getParentDeformBone(deformRig, bone):
	p = bone.parent
	while p != None:
		if p.use_deform:
			return p, True

		# get DEF-<bone> from ORG-<bone>
		if p.name.startswith("ORG-"):
			def_bone_name = "DEF-" + p.name[4:]
			if def_bone_name != bone.name and def_bone_name in deformRig.data.edit_bones:
				def_bone = deformRig.data.edit_bones[def_bone_name]
				#print(f"{bone.name} {p.name} -> {def_bone_name}")
				if def_bone.use_deform:
					return def_bone, False

		p = p.parent

	return None, False

def setBoneIkMode(rig, boneName, mode):
	if not rig or rig.type != 'ARMATURE': return
	if boneName not in rig.pose.bones: return
	bone = rig.pose.bones[boneName]
	# jx.debug.dump(bone)
	# jx.anim.evaluateAnimation()


def removeAllIkStretch(rig):
	if not rig or rig.type != 'ARMATURE':
		return

	for poseBone in rig.pose.bones:
		if "IK_Stretch" not in poseBone:
			continue
		poseBone["IK_Stretch"] = 0

	jx.anim.evaluateAnimation()

def isMetarig(obj):
	if not (obj and obj.data and obj.type == 'ARMATURE'):
		return False
	if 'rig_id' in obj.data:
		return False
	for b in obj.pose.bones:
		if b.rigify_type != "":
			return True
	return False

def getMetaRig(rig):
	controlRig = getControlRig(rig)
	
	for obj in bpy.context.scene.objects:
		if not isMetarig(obj): continue
		if "rigify_target_rig" not in obj.data: continue
		if obj.data.rigify_target_rig == controlRig:
			return obj
		
	return None

def getOrAddBone(rig, name):
	bone = rig.data.edit_bones.get(name)
	if not bone:
		# print(f"create bone {name}")
		bone = rig.data.edit_bones.new(name=name)
		bone.head = (0,0,0)
		bone.tail = (0,0,1)	
	return bone

def cloneBone(targetRig, srcBone):
	newBone = getOrAddBone(targetRig, srcBone.name)
	newBone.head = srcBone.head
	newBone.tail = srcBone.tail
	newBone.roll = srcBone.roll
	newBone.use_deform = srcBone.use_deform
	return newBone

def cloneBoneUpward(targetRig, srcBone):
	src = srcBone
	dst = None

	while src:
		p = cloneBone(targetRig, src)
		if dst: dst.parent = p
		dst = p
		src = src.parent

def getOrAddBoneConstraint(bone, name):
	con = bone.constraints.get(name)
	if not con:
		con = bone.constraints.new('COPY_TRANSFORMS')
		con.name = name
	return con

def setBoneCollection(rig, bone, collectionName):
	for c in bone.collections:
		c.unassign(bone)
	rig.data.collections[collectionName].assign(bone)

def addRootMotionBone(rig):
	bpy.ops.object.mode_set(mode='OBJECT')

	rig.select_set(True)
	bpy.ops.object.mode_set(mode='EDIT')

	rootMotionBone = getOrAddBone(rig, g_rootMotionBoneName)
	rootMotionBone.use_deform = False
	rootMotionBone.head = (0,0,0)
	rootMotionBone.tail = (0,80,0)
	setBoneCollection(rig, rootMotionBone, "Root")

	rootParentBone = getOrAddBone(rig, "JX-MCH-root.parent")
	rootParentBone.use_deform = False
	rootParentBone.head = (0,0,0)
	rootParentBone.tail = (0,50,0)
	rootParentBone.hide = True
	setBoneCollection(rig, rootParentBone, "MCH")

	rootBone = rig.data.edit_bones.get("root")
	rootBone.parent = rootParentBone

	# ---- POSE MODE -----
	bpy.ops.object.mode_set(mode='POSE')
	rootPoseBone = rig.pose.bones["root"]
	rootPoseBone.custom_shape_scale_xyz = (0.7, 0.7, 0.7)

	rootMotionPoseBone = rig.pose.bones[g_rootMotionBoneName]
	rootMotionPoseBone.custom_shape = rootPoseBone.custom_shape

	rootParentPoseBone = rig.pose.bones["JX-MCH-root.parent"]
	con = getOrAddBoneConstraint(rootParentPoseBone, "JX_COPY_TRANSFORM")
	con.target = rig
	con.subtarget = g_rootMotionBoneName
	
	for t in rig.pose.bones["MCH-torso.parent"].constraints["SWITCH_PARENT"].targets:
		if t.subtarget == "root":
			t.subtarget = g_rootMotionBoneName
			break

def createDeformRig(rig):
	#--- call rigify to generate rig
	if isMetarig(rig):
		bpy.ops.pose.rigify_generate()
		if not rig.data.rigify_target_rig:
			raise RuntimeError("error to generate control rig from meta rig")

		rig = rig.data.rigify_target_rig
	#-------

	if rig.name.startswith("DeformRig-"):
		deformRig = rig
		rig = getControlRig(rig)
	else:
		deformRigName = "DeformRig-" + rig.name
		bpy.ops.object.mode_set(mode='OBJECT')

		if deformRigName in bpy.context.view_layer.objects:
			deformRig = bpy.context.view_layer.objects[deformRigName]
			bpy.context.view_layer.objects.active = deformRig
		else:
			bpy.ops.object.armature_add(enter_editmode=False)
			deformRig = bpy.context.view_layer.objects.active
			deformRig.name = deformRigName
			deformRig.data.name = deformRigName

	if not rig:
		raise RuntimeError('no rig source')

	print(f"createDeformRig ControlRig'{rig.name}' -> DeformRig'{deformRig.name}'")
	# deformRig is Object Type
	# deformRig.data is Armature Type

	metaRig = getMetaRig(rig)
	if not metaRig:
		print(f"metaRig not found rig={rig.name}")

	deformRig.hide_set(False)

	jx.util.resetTransform(deformRig)
	jx.util.clearPropCollection(deformRig.constraints)

	old_mode = bpy.context.mode
	bpy.ops.object.mode_set(mode='OBJECT')
	bpy.context.view_layer.objects.active = rig

	addRootMotionBone(rig)

	bpy.ops.object.mode_set(mode='OBJECT')
	bpy.context.view_layer.objects.active = deformRig
	
	bpy.ops.object.mode_set(mode='POSE')
	jx.anim.rig.removeAllConstraints(deformRig)

	bpy.ops.object.mode_set(mode='EDIT')
	jx.anim.rig.removeAllCurves(deformRig)
	jx.anim.rig.removeAllBones(deformRig)

	# create all bones first	 
	deformRootBone = getOrAddBone(deformRig, "root")
	deformRootBone.use_deform = False

	for src in rig.data.edit_bones:
		if src.use_deform:
			cloneBone(deformRig, src)

		if src.name in  ikHandlerBones:
			cloneBone(deformRig, src)

		poseBone = rig.pose.bones[src.name]
		# IK Bones
		for con in poseBone.constraints:
			if con.type != "IK": continue
			newIkBone = cloneBone(deformRig, src)
			newIkBone['jx_ik_chain'] = con.chain_count

			leafBone = getOrAddBone(deformRig, "ik_leaf_" + src.name)
			newIkBone['jk_ik_leaf'] = leafBone.name
			leafBone.use_deform = False
			leafBone.parent = newIkBone
			leafBone.use_connect = True
			leafBone.head = newIkBone.tail
			leafBone.tail = Vector((0, 20, 0)) + newIkBone.tail

			# clone IK chain
			srcParentBone = src.parent
			dstChildBone = newIkBone

			for i in range(con.chain_count):
				if not srcParentBone: break
				p = cloneBone(deformRig, srcParentBone)
				dstChildBone.parent = p
				dstChildBone.use_connect = True
				dstChildBone = p
				srcParentBone = srcParentBone.parent

			if con.subtarget: 
				cloneBone(deformRig, rig.data.edit_bones[con.subtarget])
				newIkBone['jx_ik_subtarget'] = con.subtarget

			if con.pole_subtarget:
				cloneBone(deformRig, rig.data.edit_bones[con.pole_subtarget])
				newIkBone['jx_ik_pole_subtarget'] = con.pole_subtarget

	for boneName in heelToeFoots:
		src = rig.data.edit_bones.get(boneName)
		if not src: continue
		cloneBoneUpward(deformRig, src)

	# set bone props
	for src in rig.data.edit_bones:
		if src.use_deform or src.name in ikHandlerBones:
			dst = deformRig.data.edit_bones[src.name]

			parentBone, connected = getParentDeformBone(deformRig, src)
			if parentBone == None:
				dst.parent = deformRootBone
			else:
				dst.parent = deformRig.data.edit_bones[parentBone.name]
				dst.use_connect = connected

			# copy envelope from meta rig
			# metaBoneName = src.name.split("-", 1)[1] # remove DEF-XXX
			# if metaRig:
			# 	# print(f" metaBone = {metaBoneName}")
			# 	if metaBoneName in metaRig.data.bones:
			# 		metaBone = metaRig.data.bones[metaBoneName]
			# 		dst.head_radius = metaBone.head_radius
			# 		dst.tail_radius = metaBone.tail_radius

	addDeformRigConstraints(rig)
	removeAllIkStretch(rig)
	bpy.ops.object.mode_set(mode="OBJECT")

def getDeformRig(rig):
	if rig.name.startswith("DeformRig-"):
		return rig

	deformRigName = "DeformRig-" + rig.name
	if deformRigName not in bpy.context.view_layer.objects:
		print(f"cannot find deform rig '{deformRigName}'")
		return None

	return bpy.context.view_layer.objects[deformRigName]

def getControlRig(rig):
	if not rig.name.startswith("DeformRig-"):
		return rig

	sourceRigName = rig.name.split("-", 1)[1]

	if sourceRigName not in bpy.context.view_layer.objects:
		print(f"cannot find deform source rig '{sourceRigName}'")
		return None

	return bpy.context.view_layer.objects[sourceRigName]

def addDeformRigConstraints(rig):
	deformRig = getDeformRig(rig)
	if deformRig == None:
		raise RuntimeError("no deform rig found")

	rig = getControlRig(rig)
	if rig == None:
		raise RuntimeError("no deform source rig found")

	bpy.ops.object.mode_set(mode='OBJECT')
	bpy.context.view_layer.objects.active = deformRig
	bpy.ops.object.mode_set(mode='POSE')

	for dst in deformRig.pose.bones:
		if dst.bone.use_deform or dst.name in ikHandlerBones:
			con = dst.constraints.new('COPY_TRANSFORMS')
			con.name = "JX_DEFORM_RIG_COPY_TRANSFORMS"
			con.target = rig
			con.subtarget = dst.name

	# copy control rig root bone transform to deformRig object
	rootCon = deformRig.constraints.new('COPY_TRANSFORMS')
	rootCon.name = "JX_DEFORM_RIG_COPY_TRANSFORMS"
	rootCon.target = rig
	rootCon.subtarget = g_rootMotionBoneName

def removeBakedDeformRig(rig):
	deformRig = getDeformRig(rig)
	if deformRig != None:
		jx.anim.rig.removeAllCurves(deformRig)
		jx.util.clearPropCollection(deformRig.constraints)
		jx.anim.rig.removeAllConstraints(deformRig)
		addDeformRigConstraints(deformRig)

def simplifyCurves():
	C = bpy.context
	old_area_type = C.area.type
	C.area.type = 'GRAPH_EDITOR'
	bpy.ops.graph.decimate(mode='RATIO', factor=0.75)
	C.area.type = old_area_type

def bakeDeformRig(rig):
	deformRig = getDeformRig(rig)
	if deformRig != None:
		removeBakedDeformRig(deformRig)
		jx.anim.rig.bakeRig(deformRig)
		# simplifyCurves()
			
class OP_CreateDeformRig(jx.types.Operator):
	bl_idname = 'armature.jx_rigify_create_deform_rig'
	bl_label = 'Create Deform Rig'
	bl_options = {"REGISTER", "UNDO"}
	
	def execute(self, context):
		rig = bpy.context.object
		createDeformRig(rig)
		return {'FINISHED'}

class OP_BakeDeformRig(jx.types.Operator):
	bl_idname = 'armature.jx_rigify_bake_deform_rig'
	bl_label = 'Bake'
	bl_options = {"REGISTER", "UNDO"}
	
	def execute(self, context):
		rig = bpy.context.object
		bakeDeformRig(rig)
		return {'FINISHED'}

class OP_RemoveBakedDeformRig(jx.types.Operator):
	bl_idname = 'armature.jx_rigify_remove_baked_deform_rig'
	bl_label = 'Remove Bake'
	bl_options = {"REGISTER", "UNDO"}
	
	def execute(self, context):
		rig = bpy.context.object
		removeBakedDeformRig(rig)
		return {'FINISHED'}
	
class OP_RemoveAllIkStretch(jx.types.Operator):
	bl_idname = 'armature.jx_rigify_remove_all_ik_stretch'
	bl_label = 'Remove All IK Stretch'
	bl_options = {"REGISTER", "UNDO"}

	def execute(self, context):
		for obj in bpy.context.selected_objects:
			removeAllIkStretch(obj)

		return {'FINISHED'}
	
class OP_DeformRigBindSkin(jx.types.Operator):
	bl_idname = 'armature.jx_rigify_deform_rig_bind_skin'
	bl_label = 'Deform Rig Bind Skin'
	bl_options = {"REGISTER", "UNDO"}

	def execute(self, context):
		rig = bpy.context.object
		deformRig = getDeformRig(rig)
		if deformRig != None:
			bpy.ops.object.parent_set(type='ARMATURE_AUTO')
			for obj in bpy.context.selected_objects:
				if obj != deformRig:
					jx.anim.rig.removeNonDeformBoneWeight(rig, obj)
			
		return {'FINISHED'}
	
class OP_SetBoneProp(jx.types.Operator):
	bl_idname = 'object.jx_set_bone_prop'
	bl_label = 'OP_SetBoneProp'
	bl_options = {"REGISTER", "UNDO"}

	poseBoneName : bpy.props.StringProperty()
	propName : bpy.props.StringProperty()
	dataPath : bpy.props.StringProperty()
	value : bpy.props.FloatProperty()
	insertKey : bpy.props.BoolProperty(default=False)

	def execute(self, context):
		if not self.doExecute(context):
			return {'CANCELLED'}
		return {'FINISHED'}
	
	def doExecute(self, context):
		poseBone = context.object.pose.bones[self.poseBoneName]
		poseBone[self.propName] = self.value
		if self.insertKey:
			poseBone.keyframe_insert(data_path=self.dataPath, group=poseBone.name)

		jx.anim.evaluateAnimation()
		return True

class RigifyPropertyPanel(jx.types.Panel):
	bl_idname = "JX_PT_RIGIFY_PROPERTIES_PANEL"
	bl_label = "(JX) Rigify Properties"
	bl_order = 100
	bl_space_type = "VIEW_3D"
	bl_region_type = "UI"
	bl_category = "JX"
	bl_options = {'DEFAULT_CLOSED'}

	@classmethod
	def poll(cls, context):
		obj = context.object
		if not obj: return False
	  
		if bpy.context.object.mode != "POSE":
			return False
		if obj == None or obj.type != 'ARMATURE':
			return False

		return True

	def addBoneConstraintProp(self, layout, label, rig, boneName, constraintName, propName):
		bone = rig.pose.bones.get(boneName)
		if not bone: return

		con = bone.constraints.get(constraintName)
		if not con: return

		if not hasattr(con, propName): return

		row = layout.row(align=True)
		row.label(text=label)
		row.prop(con, propName, text="")

	def setCustomPropOperator(self, layout, label, poseBoneName, propName, value, depress=False, insertKey=False):
		op = layout.operator(OP_SetBoneProp.bl_idname, text=label, depress=depress)
		op.poseBoneName = poseBoneName
		op.propName = propName
		op.dataPath = f'["{propName}"]'
		op.value = value
		op.insertKey = insertKey

	def drawIkProps(self, layout, label, rig, ik_name, ik_root_name):
		ik_root_bone = rig.pose.bones.get(ik_root_name)
		if not ik_root_bone: return

		value = ik_root_bone['IK_FK']

		row = layout.row(align=True)
		row.label(text=label)
		row2 = row.row(align=True)
		row2.alignment = "LEFT"
		self.setCustomPropOperator(row2, "+",  ik_root_name, 'IK_FK', value, insertKey=True)
		self.setCustomPropOperator(row2, "IK", ik_root_name, 'IK_FK', 0, depress=value==0)
		self.setCustomPropOperator(row2, "FK", ik_root_name, 'IK_FK', 1, depress=value==1)
		row2.prop(ik_root_bone, '["IK_FK"]', text='')


	def draw(self, context):
		rig = context.object
		if rig == None or rig.type != 'ARMATURE':
			return

		# bone = rig.data.bones.active
		# if not bone: return None
		# poseBone = rig.pose.bones[bone.name]

		col = self.layout.column(align=True)
		self.drawIkProps(col, "Hand L", rig, "hand_ik.L", "upper_arm_parent.L")
		self.drawIkProps(col, "Hand R", rig, "hand_ik.R", "upper_arm_parent.R")
		self.drawIkProps(col, "Foot L", rig, "foot_ik.L", "thigh_parent.L")
		self.drawIkProps(col, "Foot R", rig, "foot_ik.R", "thigh_parent.R")
		col.separator()
		self.addBoneConstraintProp(col, "RootMotion Follow", rig, "JX-MCH-root.parent", "JX_COPY_TRANSFORM", "influence")

class RigifyCreatePanel(jx.types.Panel):
	bl_idname = "JX_PT_RIGIFY_CREATE_PANEL"
	bl_label = "(JX) Rigify - Create"
	bl_order = 4000
	bl_space_type = "VIEW_3D"
	bl_region_type = "UI"
	bl_category = "JX"
	bl_options = {'DEFAULT_CLOSED'}

	@classmethod
	def poll(cls, context):
		obj = context.object
		return obj != None and obj.type == 'ARMATURE'

	def draw(self, context):
		if context.object == None: return

		self.layout.operator(OP_CreateDeformRig.bl_idname, text="Deform Rig - Create")
		# self.layout.operator(OP_RemoveAllIkStretch.bl_idname)
		self.layout.operator(OP_DeformRigBindSkin.bl_idname, text="Bind Skin")

		row = self.layout.row(align=True)
		row.operator(OP_BakeDeformRig.bl_idname, icon='NORMALIZE_FCURVES')
		row.operator(OP_RemoveBakedDeformRig.bl_idname, icon='CANCEL')
