from optparse import Option
import bpy
import jx.types
import jx.util
import jx.anim.rig

CONSTRAINT_PREFIX = 'JX_RETARGET_'

def getSettings():
	if not hasattr(bpy.context.object, "jx_retarget_settings"):
		bpy.context.object.jx_retarget_settings = bpy.props.PointerProperty(type=Settings)
	return bpy.context.object.jx_retarget_settings

class BoneMapping(bpy.types.PropertyGroup):
	source: bpy.props.StringProperty(name = "Source")
	target: bpy.props.StringProperty(name = "Target")
	type: bpy.props.EnumProperty(
		name = "Type",
		items = [
			('None', 'None', 'None', 0),
			('Root', 'Root', 'Root', 1),
			('FK', 'FK', 'FK', 2),
			('IK', 'IK', 'IK', 3),
		],
		default = 'FK',
	)

	def is_valid(self):
		return (self.source != None 
				and self.target != None 
				and len(self.source) > 0 
				and len(self.target) > 0)

class Settings(jx.types.PropertyGroup):
	sourceRig: bpy.props.PointerProperty(
		type   = bpy.types.Object,
		name   = "Source Rig",
		poll   = lambda self, obj: obj.type == 'ARMATURE' and obj != bpy.context.object,
		update = lambda self, ctx: getSettings().updateSourceRig()
	)

	boneMappings: bpy.props.CollectionProperty(type=BoneMapping)
	activeBoneMapping: bpy.props.IntProperty()

	def updateSourceRig(self):
		pass

	def getSourceRig(self): return self.sourceRig
	def getTargetRig(self): return bpy.context.object

	def getSourceRigArmature(self): return self.sourceRig.data     if self.sourceRig != None else None
	def getTargetRigArmature(self): return bpy.context.object.data if bpy.context.object != None else None

	def saveFile(self, filepath):
		jsonBoneMappings = []
		json = {
			"boneMappings": jsonBoneMappings
		}

		for bm in self.boneMappings:
			jsonBm = {
				"type": bm.type,
				"source": bm.source,
				"target": bm.target,
			}
			jsonBoneMappings.append(jsonBm)

		jx.json.saveToFile(json, filepath)
		pass

	def loadFile(self, filepath):
		json = jx.json.loadFromFile(filepath)

		self.boneMappings.clear()
		for src in json['boneMappings']:
			dst = self.boneMappings.add()
			dst.type   = src["type"]
			dst.source = src["source"]
			dst.target = src["target"]

class JX_UL_BoneMappings_UIList(jx.types.UIList):
	def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index, flt_flag):
		s = getSettings()
		layout.alert = not item.is_valid()
		layout.label(text=item.type, icon='BONE_DATA')
		layout.label(text=item.source)
		layout.label(icon='FORWARD')
		layout.label(text=item.target)

	def draw_filter(self, context, layout):
		pass

	def filter_items(self, context, data, propname):
		flt_flags = []
		flt_neworder = []

		return flt_flags, flt_neworder

class OP_BoneMappings_Add(jx.types.Operator):
	bl_idname = 'armature.jx_retarget_bone_mappings_add'
	bl_label = 'BoneMappings Add'
	bl_description = "Add"
	bl_options = {"REGISTER", "UNDO"}

	def execute(self, context):
		s = getSettings()
		n = len(s.boneMappings)
		active = s.activeBoneMapping
		m = s.boneMappings.add()
		s.boneMappings.move(n, active + 1)
		s.activeBoneMapping = active + 1
		return {'FINISHED'}

class OP_BoneMappings_Remove(jx.types.Operator):
	bl_idname = 'armature.jx_retarget_bone_mappings_remove'
	bl_label = 'BoneMappings Remove'
	bl_description = "Remove"
	bl_options = {"REGISTER", "UNDO"}

	def execute(self, context):
		s = getSettings()
		n = len(s.boneMappings)
		active = s.activeBoneMapping
		if active >= 0 and active < n and n > 0:
			s.boneMappings.remove(active)
			s.activeBoneMapping = min(active, n - 2)
		return {'FINISHED'}

class OP_BoneMappings_MoveUp(jx.types.Operator):
	bl_idname = 'armature.jx_retarget_bone_mappings_move_up'
	bl_label = 'BoneMappings Move Up'
	bl_description = "Move Up"
	bl_options = {"REGISTER", "UNDO"}

	def execute(self, context):
		s = getSettings()
		n = len(s.boneMappings)
		active = s.activeBoneMapping
		if active > 0 and active < n:
			s.boneMappings.move(active, active - 1)
			s.activeBoneMapping = active - 1
		return {'FINISHED'}

class OP_BoneMappings_MoveDown(jx.types.Operator):
	bl_idname = 'armature.jx_retarget_bone_mappings_move_down'
	bl_label = 'BoneMappings Move Down'
	bl_description = "Move Down"
	bl_options = {"REGISTER", "UNDO"}

	def execute(self, context):
		s = getSettings()
		n = len(s.boneMappings)
		active = s.activeBoneMapping
		if active >= 0 and active < n - 1:
			s.boneMappings.move(active, active + 1)
			s.activeBoneMapping = active + 1
		return {'FINISHED'}

class OP_BoneMappings_Duplicate(jx.types.Operator):
	bl_idname = 'armature.jx_retarget_bone_mappings_duplicate'
	bl_label = 'BoneMappings Duplicate'
	bl_description = "Duplicate"
	bl_options = {"REGISTER", "UNDO"}

	def execute(self, context):
		s = getSettings()
		n = len(s.boneMappings)
		active = s.activeBoneMapping
		if active >= 0 and active < n:
			dst = s.boneMappings.add()
			src = s.boneMappings[active]
			for k, v in src.items():
				dst[k] = v

			s.boneMappings.move(n, active + 1)
			s.activeBoneMapping = active + 1
		return {'FINISHED'}

class OP_BoneMappings_MirrorName(jx.types.Operator):
	bl_idname = 'armature.jx_retarget_bone_mappings_mirror_name'
	bl_label = 'BoneMappings Mirror Name'
	bl_description = "Mirror Name"
	bl_options = {"REGISTER", "UNDO"}

	def autoName(self, s:str):
		if s.endswith(".L"): return s[:-2] + ".R"
		if s.endswith(".R"): return s[:-2] + ".L"
		if s.endswith(".l"): return s[:-2] + ".r"
		if s.endswith(".r"): return s[:-2] + ".l"
		if s.endswith("_l"): return s[:-2] + "_r"
		if s.endswith("_r"): return s[:-2] + "_l"
		if s.endswith("_L"): return s[:-2] + "_R"
		if s.endswith("_R"): return s[:-2] + "_L"
		return s

	def execute(self, context):
		s = getSettings()
		n = len(s.boneMappings)
		active = s.activeBoneMapping
		if active >= 0 and active < n:
			item = s.boneMappings[active]
			item.source = self.autoName(item.source)
			item.target = self.autoName(item.target)
		return {'FINISHED'}

class OP_SaveBondMappings(jx.types.Operator):
	bl_idname = 'armature.jx_retarget_save_bone_mappings'
	bl_label = 'Save Bone Mappings'
	bl_options = {"REGISTER", "UNDO"}

	filter_glob: bpy.props.StringProperty(
		default = '*.json',
		options = {'HIDDEN'}
	)

	filepath: bpy.props.StringProperty(subtype="FILE_PATH")
	filename: bpy.props.StringProperty()

	def execute(self, context):
		if not self.filepath.endswith(".json"):
			self.filepath += ".json"
		getSettings().saveFile(self.filepath)
		return {'FINISHED'}

	def invoke(self, context, event):
		self.filename = ""
		bpy.context.window_manager.fileselect_add(self)
		return {'RUNNING_MODAL'}

class OP_LoadBondMappings(jx.types.Operator):
	bl_idname = 'armature.jx_retarget_load_bone_mappings'
	bl_label = 'Load Bone Mappings'
	bl_options = {"REGISTER", "UNDO"}

	filter_glob: bpy.props.StringProperty(
		default = '*.json',
		options = {'HIDDEN'}
	)

	filepath: bpy.props.StringProperty(subtype="FILE_PATH")
	filename: bpy.props.StringProperty()

	def execute(self, context):
		getSettings().loadFile(self.filepath)
		return {'FINISHED'}

	def invoke(self, context, event):
		self.filename = ""
		bpy.context.window_manager.fileselect_add(self)
		return {'RUNNING_MODAL'}

class OP_SetArmaturePosePosition(jx.types.Operator):
	bl_idname = 'armature.jx_retarget_set_armature_pose_position'
	bl_label = 'Set Armature Pose Position'
	bl_options = {"REGISTER", "UNDO"}

	pose_position: bpy.props.StringProperty()

	def execute(self, context):
		s = getSettings()
		targetRig = s.getTargetRig()
		if targetRig != None:
			targetRig.data.pose_position = self.pose_position

		return {'FINISHED'}

class OP_RemoveBakedAnimation(jx.types.Operator):
	bl_idname = 'armature.jx_retarget_remove_baked_animation'
	bl_label = 'Remove Baked'
	bl_options = {"REGISTER", "UNDO"}
	
	def execute(self, context):
		self.doExecute(context)
		return {'FINISHED'}

	def doExecute(self, context):
		s = getSettings()
		targetRig = s.getTargetRig()
		jx.anim.rig.removeAllCurves(targetRig)

class OP_BakeAnimation(jx.types.Operator):
	bl_idname = 'armature.jx_retarget_bake_animation'
	bl_label = 'Bake'
	bl_options = {"REGISTER", "UNDO"}
	
	def execute(self, context):
		self.doExecute(context)
		return {'FINISHED'}

	def doExecute(self, context):
		s = getSettings()
		sourceRig = s.getSourceRig()
		targetRig = s.getTargetRig()

		frame_start, frame_end = jx.anim.rig.animationRange(sourceRig)

		old_mode = bpy.context.mode
		bpy.ops.object.mode_set(mode='POSE')
		bpy.ops.pose.select_all(action='DESELECT')

		for bm in s.boneMappings:
			targetBone = targetRig.data.bones[bm.target]
			targetBone.select = True

		bpy.ops.nla.bake(
			frame_start = int(frame_start),
			frame_end   = int(frame_end),
			step = 1,
			visual_keying = True,
			clean_curves = True,
			bake_types = {'POSE'}
		)

		removeRetarget()
		bpy.ops.objec.mode_set(old_mode)

def removeRetarget():
	s = getSettings()
	targetRig = s.getTargetRig()
	if targetRig == None: return

	for bone in targetRig.pose.bones:
		jx.util.resetTransform(bone)
		list = []
		for c in bone.constraints:
			if c.name.startswith(CONSTRAINT_PREFIX):
				list.append(c)

		for c in reversed(list):
			bone.constraints.remove(c)

class OP_RemoveRetarget(jx.types.Operator):
	bl_idname = 'armature.jx_retarget_remove'
	bl_label = 'Remove Retarget'
	bl_options = {"REGISTER", "UNDO"}
	
	def execute(self, context):
		removeRetarget()
		return {'FINISHED'}
			
class OP_SelectBone(jx.types.Operator):
	bl_idname = 'armature.jx_retarget_select_bone'
	bl_label = 'Select Bone'
	bl_description = 'Select Bone'
	bl_options = {"REGISTER", "UNDO"}

	action: bpy.props.StringProperty()

	def execute(self, context):
		self.doExecute(context)
		return {'FINISHED'}

	def selectBone(self, rig, bone):
		bpy.ops.object.mode_set(mode='POSE')
		bpy.ops.pose.select_all(action='DESELECT')
		#bpy.ops.object.select_all(action='DESELECT')
		#bpy.context.view_layer.objects.active = rig
		#rig.select = True
		bone.select = True
		rig.data.bones.active = bone

	def doExecute(self, context):
		s = getSettings()
		index = s.activeBoneMapping
		n = len(s.boneMappings)
		if index < 0 or index >= n: return
		bm = s.boneMappings[index]

		sourceRig = s.getSourceRig()
		targetRig = s.getTargetRig()

		if self.action == 'SourceBone':
			if sourceRig == None: return
			bone = sourceRig.data.bones[bm.source]
			self.selectBone(sourceRig, bone)

		elif self.action == 'TargetBone':
			if targetRig == None: return
			bone = targetRig.data.bones[bm.target]
			self.selectBone(targetRig, bone)

class OP_Retarget(jx.types.Operator):
	bl_idname = 'armature.jx_retarget'
	bl_label = 'Retarget'
	bl_options = {"REGISTER", "UNDO"}
	
	def execute(self, context):
		self.doExecute(context)
		return {'FINISHED'}

	def retargetBone(self, context, boneMap, targetRig, sourceRig):
		if boneMap.target not in targetRig.pose.bones:
			print(f"target bone '{boneMap.target}' not found")
			return

		if boneMap.source not in sourceRig.pose.bones:
			print(f"source bone '{boneMap.source}' not found")
			return

		targetBone = targetRig.pose.bones[boneMap.target]
		sourceBone = sourceRig.pose.bones[boneMap.source]

		targetRig.data.bones.active = targetBone.bone
		jx.util.resetTransform(targetBone)

		if boneMap.type == 'Root' or boneMap.type == 'IK':
			con = targetBone.constraints.new('COPY_LOCATION')
			con.name = CONSTRAINT_PREFIX + "COPY_LOCATION"
			con.target = sourceRig
			con.subtarget = sourceBone.name
			con.target_space = 'WORLD'
			con.owner_space  = 'WORLD'

		if boneMap.type == 'Root' or boneMap.type == 'IK' or boneMap.type == 'FK':
			con = targetBone.constraints.new('COPY_ROTATION')
			con.name = CONSTRAINT_PREFIX + "COPY_ROTATION"
			con.target = sourceRig
			con.subtarget = sourceBone.name
			con.target_space = 'LOCAL_OWNER_ORIENT'
			con.owner_space  = 'LOCAL'

	def doExecute(self, context):
		s = getSettings()
		targetRig = s.getTargetRig()
		if targetRig == None:
			raise RuntimeError("Target Rig is None")

		removeRetarget()

		sourceRig = s.getSourceRig()
		if sourceRig == None: 
			raise RuntimeError("Source Rig is None")

		targetRig.data.pose_position = 'REST'
		sourceRig.data.pose_position = 'REST'
		bpy.ops.object.mode_set(mode='POSE')

		for index, boneMap in enumerate(s.boneMappings):
			if not boneMap.is_valid():
				print(f"Invalid bone map index={index}")
				continue
			self.retargetBone(context, boneMap, targetRig, sourceRig)

		targetRig.data.pose_position = 'POSE'
		sourceRig.data.pose_position = 'POSE'

class RetargetPanel(jx.types.Panel):
	bl_idname = "JX_PT_RETARGET_PANEL"
	bl_label = "(JX) Anim Re-target"
	bl_order = 4001
	bl_space_type = "VIEW_3D"
	bl_region_type = "UI"
	bl_category = "JX"
	bl_options = {'DEFAULT_CLOSED'}

	# @classmethod
	# def poll(cls, context):
	# 	obj = context.object
	# 	return obj != None and obj.type == 'ARMATURE'

	def draw(self, context):
		rig = context.object
		if not rig or not rig.type == 'ARMATURE':
			self.layout.box().label(text="<No Armature Selected>")
			return

		s = getSettings()

		#target rig
		split = self.layout.row().split(factor=0.4)
		split.column().label(text='Target Rig:')
		split.column().label(text=context.object.name, icon='ARMATURE_DATA')
		self.layout.prop(s.getTargetRigArmature(), 'pose_position', expand=True)
		self.layout.operator(OP_RemoveRetarget.bl_idname, icon='CANCEL')
		self.layout.separator()

		self.layout.prop(s, 'sourceRig', icon='ARMATURE_DATA')
		sourceRig = s.getSourceRigArmature()
		if sourceRig == None:
			return

		self.layout.prop(s.getSourceRigArmature(), 'pose_position', expand=True)
		self.layout.separator()

		self.drawBoneMapping(context)
		self.layout.operator(OP_Retarget.bl_idname, icon='FILE_REFRESH')
		self.layout.separator()

		box = self.layout.box()
		box.label(text="Bake Animation")
		row = box.row()
		row.operator(OP_BakeAnimation.bl_idname, icon='NORMALIZE_FCURVES')
		row.operator(OP_RemoveBakedAnimation.bl_idname, icon='CANCEL')

	def drawBoneMapping(self, context):
		s = getSettings()
		if not s:  return

		n = len(s.boneMappings)
		activeIndex = s.activeBoneMapping

		self.layout.label(text='Bone Mappings (%i):' % n, icon='COLLAPSEMENU')

		row = self.layout.row()
		row.operator(OP_LoadBondMappings.bl_idname, icon='IMPORT')
		row.operator(OP_SaveBondMappings.bl_idname, icon='EXPORT')

		row = self.layout.row()
		row.template_list(
			listtype_name='JX_UL_BoneMappings_UIList',
			list_id='',
			dataptr=s,
			propname='boneMappings',
			active_dataptr=s,
			active_propname='activeBoneMapping')

		col = row.column(align=True)
		col.operator(OP_BoneMappings_Add.bl_idname,			icon='ADD',			text='')
		col.operator(OP_BoneMappings_Remove.bl_idname,		icon='REMOVE',		text='')
		col.separator()
		col.operator(OP_BoneMappings_MoveUp.bl_idname,		icon='TRIA_UP',		text='')
		col.operator(OP_BoneMappings_MoveDown.bl_idname,	icon='TRIA_DOWN',	text='')
		col.separator()
		col.operator(OP_BoneMappings_Duplicate.bl_idname,	icon='DUPLICATE',	text='')
		col.separator()
		col.operator(OP_BoneMappings_MirrorName.bl_idname,	icon='MOD_MIRROR',	text='')

		if activeIndex >= 0 and activeIndex < n:
			item = s.boneMappings[activeIndex]

			self.layout.label(text='Bone', icon='BONE_DATA')
			box = self.layout.box()
			box.prop(item, 'type')
			row = box.row()
			row.prop_search(item, 'source', s.getSourceRigArmature(), 'bones', icon='BONE_DATA')
			row.operator(OP_SelectBone.bl_idname, text='', icon='RIGHTARROW').action = 'SourceBone'

			row = box.row()
			row.prop_search(item, 'target', s.getTargetRigArmature(), 'bones', icon='BONE_DATA')
			row.operator(OP_SelectBone.bl_idname, text='', icon='RIGHTARROW').action = 'TargetBone'

