import os
import os.path

import mathutils
import bpy
import jx
import jx.file
import jx.types
import jx.util
import jx.custom_prop

export_opt_axis_forward = 'X'
export_opt_axis_up = 'Z'
export_opt_use_space_transform = True
export_opt_use_armature_deform_only = False

export_opt_global_scale = 1
export_opt_apply_unit_scale = True
export_opt_apply_scale_options = "FBX_SCALE_ALL" # keep all object's transform scale to 1.0 after export

export_opt_mesh_smooth_type = "EDGE"
export_opt_add_leaf_bones = False # not needed in Unreal / Unity
export_opt_path_mode = "RELATIVE"
export_opt_use_custom_props = True
export_opt_use_metadata = True

my_export_opt_reset_object_transform = True
my_export_opt_fix_invalid_object_name = True

def to_xyz_list(v):
	return [v.x, v.y, v.z]

class OP_Export(jx.types.Operator):
	bl_idname = "scene.jx_export_to_fbx"
	bl_label = "Export to FBX"
	bl_options = {"REGISTER", "UNDO"}

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)

		self.outInfo_materials = {}
		self.outInfo_textures = {}
		self.outInfo_objects = {}
		self.outInfo_animation = {}

		self.exportList_objects = set()
		self.exportList_materials = set()
		self.exportList_textures = set()
		self.exportList_armatures = set()

	def exportObject(self, obj:bpy.types.Object):
		print(f"exportObject \"{obj.name}\"")

		world_matrix = obj.matrix_world
		outInfo_matSlots = []
		outInfo = {
			#"jxProps": jx.custom_prop.get_all_jx_prop(obj),
			"type": obj.type,
			"parent": "",
			#
			"world_location" : to_xyz_list(world_matrix.to_translation()),
			"world_rotation" : to_xyz_list(world_matrix.to_euler()),
			"world_scale"    : to_xyz_list(world_matrix.to_scale()),
			#
			"materialSlots": outInfo_matSlots
		}
		self.outInfo_objects[obj.name] = outInfo

		if obj.parent:
			outInfo["parent"] = obj.parent.name

		for matSlot in obj.material_slots:
			mat = matSlot.material
			if mat == None:
				outInfo_matSlots.append("")
				continue
			outInfo_matSlots.append(mat.name)

			if mat in self.exportList_materials:
				continue
			self.exportList_materials.add(mat)

	def exportTextureInfo(self, tex, outInfo):
		if tex == None: 
			outInfo["#error"] = "tex is None"
			return

		# outInfo["name"] = tex.name
		if tex.image == None:
			outInfo["#error"] = "tex.image == None"
			return

		path = jx.path.to_unix(tex.image.filepath)
		outInfo["path"] = path
		outInfo["colorspace"] = tex.image.colorspace_settings.name
		outInfo["alpha_mode"] = tex.image.alpha_mode

		self.outInfo_textures[path] = outInfo

	def exportTexture(self, tex):
		if tex == None: return
		# print(f"  tex \"{tex.name}\" {tex.__class__}")
		outTexInfo = {}
		self.exportTextureInfo(tex, outTexInfo)

		if tex == None: return
		if "path" not in outTexInfo: return

		path = outTexInfo["path"]
		if path != None and path != "":
			srcDir = jx.path.dirname(jx.file.currentBlenderFilename())
			dstDir = jx.path.dirname(self.outFilename)

			srcPath = jx.path.realpath(f"{srcDir}/{path}")
			dstPath = jx.path.realpath(f"{dstDir}/{path}")

			jx.file.copy_if_newer(srcPath, dstPath)
			#jx.file.copy(srcPath, dstPath)

	def exportMaterialInput(self, input_name, input, outInfo_inputs):
		#print(f"    input {input.name} {input.default_value} {input.__class__}")
		outInfo = {}
		outInfo_inputs[input_name] = outInfo

		if not input.is_linked or len(input.links) <= 0:
			outInfo["value"] = jx.json.toValue(input.default_value)
			return

		inputNode = input.links[0].from_node
		if inputNode.type == "TEX_IMAGE":
			tex = inputNode
			outTexInfo = {}
			self.exportTextureInfo(tex, outTexInfo)
			outInfo["texture"] = outTexInfo
			
			if tex == None: return

			if tex not in self.exportList_textures:
				self.exportList_textures.add(tex)
		elif inputNode.type == "NORMAL_MAP":
			normalMapNode = inputNode
			colorInput = normalMapNode.inputs['Color']
			self.exportMaterialInput(input_name, colorInput, outInfo_inputs)
		else:
			print(f"Unknown texture inputNode.type = {inputNode.type}")

	def exportMaterial(self, mat):
		if mat == None: return
		print(f"--- mat {mat.name} ---")
		# jx.debug.dump(mat)

		outInfo = {
			"name": 		mat.name,
			"jxProps": 		jx.custom_prop.get_all_jx_prop(mat),
		}
		self.outInfo_materials[mat.name] = outInfo

		outputNode = None
		for node in mat.node_tree.nodes:
			print(f"  node {node.bl_idname} type={node.type}")
			# jx.debug.dump(node)
			if node.type == "OUTPUT_MATERIAL":
				outputNode = node
				break
		
		if outputNode == None:
			msg = f"output node is missing in material {mat.name}"
			print(msg)
			outInfo["#error"] = msg
			return

		surfaceInput = outputNode.inputs["Surface"]
		#jx.debug.dump(surfaceInput.links)

		if len(surfaceInput.links) <= 0:
			msg = f"no surface input in material {mat.name}"
			print(msg)
			outInfo["#error"] = msg
			return

		matSurface = surfaceInput.links[0].from_node

		outInfo["matSurface"] = {
			"name":  matSurface.name,
			"label": matSurface.label,
			"type":  matSurface.type,
		}

		outInfo_inputs = {}
		outInfo["inputs"] = outInfo_inputs
		for input in matSurface.inputs:
			self.exportMaterialInput(input.name, input, outInfo_inputs)

	def fix_invalid_name(self, obj):
		if not my_export_opt_fix_invalid_object_name: return
		if not obj: return
		new_name = obj.name.replace(".", "_")
		obj.name = new_name

	def doExportFbx(self):
		if len(self.collection.all_objects) <= 0:
			return

		self.outInfo = {
			"exportSoftware": "blender-" + bpy.app.version_string,
			"sourceFile":	jx.file.currentBlenderFilename(),
			"objects":		self.outInfo_objects,
			"textures":		self.outInfo_textures,
			"materials":	self.outInfo_materials,
		}

		outFileDir = os.path.dirname(self.outFilename)
		os.makedirs(outFileDir, exist_ok=True)

		# convert from bpy.types.Collection to python set()
		for obj in self.collection.all_objects:
			if obj.type == 'ARMATURE':
				self.exportList_armatures.add(obj)
				obj.data.pose_position = 'REST'
			if obj.hide_render: 
				continue

			self.fix_invalid_name(obj)
			self.exportList_objects.add(obj)
		
		for obj in self.exportList_objects:
			self.exportObject(obj)

		for mat in self.exportList_materials:
			self.exportMaterial(mat)

		for tex in self.exportList_textures:
			self.exportTexture(tex)

		# move object to origin, so object pivot will be used in Game Engine
		if my_export_opt_reset_object_transform:
			for obj in self.exportList_objects:
				obj.location              = (0,0,0)
				obj.rotation_euler        = (0,0,0)
				obj.rotation_quaternion   = (1,0,0,0)
				obj.scale                 = (1,1,1)
				# matrix_parent_inverse is not auto updated before export
				obj.matrix_parent_inverse = mathutils.Matrix.Identity(4)

		jx.json.saveToFile(self.outInfo, self.outFilename + ".fbx_jx_info")
		jx.selection.select(self.exportList_objects)

		if True:
			bpy.ops.export_scene.fbx(
					filepath = self.outFilename + ".fbx",
					use_selection = True,

					mesh_smooth_type 	= export_opt_mesh_smooth_type,
					add_leaf_bones 		= export_opt_add_leaf_bones,
					path_mode 			= export_opt_path_mode,
					use_custom_props 	= export_opt_use_custom_props,
					use_metadata 		= export_opt_use_metadata,
					axis_forward 		= export_opt_axis_forward,
					axis_up 			= export_opt_axis_up,
					global_scale 		= export_opt_global_scale,
					apply_unit_scale 	= export_opt_apply_unit_scale,
					apply_scale_options = export_opt_apply_scale_options,
					use_space_transform = export_opt_use_space_transform,
					
					armature_nodetype = 'NULL',
					use_armature_deform_only = export_opt_use_armature_deform_only,
					bake_anim = False,

					# bake_anim_use_all_bones = False,
					# bake_anim_use_nla_strips = False,
					# bake_anim_use_all_actions = False,
					# bake_anim_force_startend_keying = False,
					# bake_anim_simplify_factor = 1.0,
				)

	def doExportAnimToFbx(self, exportRig, animName:str):
		old_hide = exportRig.hide_get()
		old_selected_objects = bpy.context.selected_objects
		old_active_object = bpy.context.view_layer.objects.active
		foo_empty = None

		try:
			# unity need fbx file more than one object, otherwise the Armature became prefab root
			foo_empty = jx.util.newObject("JX_EXPORT_foo_empty", None)

			# if exportRig.hide_select:
			# 	raise RuntimeError(f"cannot export rig {exportRig.name}, because selection is disabled")

			exportRig.hide_set(False) # rig must be shown for export
			exportRig.data.pose_position = "POSE"

			jx.selection.select(exportRig)
			foo_empty.select_set(True)

			outDir = jx.path.dirname(self.outFilename)
			outBasename = jx.path.basename(self.outFilename)

			finalOutFilename = f"{outDir}/{outBasename}@{animName}.fbx"
			os.makedirs(jx.path.dirname(finalOutFilename), exist_ok=True)

			# self.outInfo = {
			# 	"sourceFile":	jx.file.currentBlenderFilename(),
			# 	"animation":	self.outInfo_animation
			# }
			# jx.json.saveToFile(self.outInfo, finalOutFilename + ".json")

			if True:
				bpy.ops.export_scene.fbx(
						filepath = finalOutFilename,
						use_selection = True,

						mesh_smooth_type 	= export_opt_mesh_smooth_type,
						add_leaf_bones 		= export_opt_add_leaf_bones,
						path_mode 			= export_opt_path_mode,
						use_custom_props 	= export_opt_use_custom_props,
						use_metadata 		= export_opt_use_metadata,
						axis_forward 		= export_opt_axis_forward,
						axis_up 			= export_opt_axis_up,
						global_scale 		= export_opt_global_scale,
						apply_unit_scale 	= export_opt_apply_unit_scale,
						apply_scale_options = export_opt_apply_scale_options,
						use_space_transform = export_opt_use_space_transform,

						object_types = {'ARMATURE', 'EMPTY'},
						use_armature_deform_only = export_opt_use_armature_deform_only,
						bake_anim = True,
						bake_anim_use_all_bones = True,
						bake_anim_use_nla_strips = False,
						bake_anim_use_all_actions = False,
						bake_anim_force_startend_keying = True,
						bake_anim_step = 1,
						bake_anim_simplify_factor = 0.0,
					)
		finally:
			jx.util.deleteObject(foo_empty)
			exportRig.hide_set(old_hide)
			jx.selection.select(old_selected_objects)
			bpy.context.view_layer.objects.active = old_active_object

	def doExportAnimTrackToFbx(self, allTracks:bool):
		# convert from bpy.types.Collection to python set()
		controlRig = None
		exportRig  = None

		for obj in self.collection.all_objects:
			if obj.type == 'ARMATURE' and not obj.hide_render:
				if exportRig:
					raise RuntimeError("only support single armature to export")
				exportRig = obj
				controlRig = jx.anim.rigify.getControlRig(exportRig)
				if not controlRig:
					controlRig = exportRig

		if not exportRig:
			raise RuntimeError("no rig to export")
		
		animData = controlRig.animation_data
		if not animData:
			raise RuntimeError(f'export Rig "{exportRig.name}" does not have animation_data')

		old_tweak_mode = animData.use_tweak_mode
		old_active_track = animData.nla_tracks.active
		old_selected_tracks = []
		old_muted_tracks = []
		old_solo_track = None

		for track in animData.nla_tracks:
			if track.select: old_selected_tracks.append(track)
			if track.mute:   old_muted_tracks.append(track)
			if track.is_solo: old_solo_track = track

		activeParentTrack = jx.anim.nla.getActiveParentTrack(controlRig)

		if not allTracks and not activeParentTrack:
			raise RuntimeError("no active animation track")

		try:
			for track in animData.nla_tracks:
				if not allTracks and track != activeParentTrack:
					continue

				if not track.name.startswith("OUT-"): continue

				subTrack = jx.anim.nla.getSubTrackNameSuffix(track.name)
				if subTrack: continue

				animName = track.name.split("-", 1)[1]
				if len(animName) <= 0:
					raise RuntimeError(f"invalid track name '{track.name}'")

				jx.anim.nla.setActiveTrackByName(controlRig, track.name)

				skipRootMotion = True
				if track.name.startswith("OUT-RM_"):
					skipRootMotion = False

				print(f"skipRootMotion = {skipRootMotion}")
				# mute control rig
				controlRig.animation_data.use_tweak_mode = True
				jx.anim.nla.muteRootMotion(controlRig, skipRootMotion)

				controlRig.animation_data.use_tweak_mode = False
				self.doExportAnimToFbx(exportRig, animName)

				# un-mute control rig
				controlRig.animation_data.use_tweak_mode = True
				jx.anim.nla.muteRootMotion(controlRig, False)

		finally:
			if allTracks and activeParentTrack:
				jx.anim.nla.setActiveTrackByName(controlRig, activeParentTrack.name)

			for track in old_selected_tracks:
				track.select = True
			for track in old_muted_tracks:
				track.mute = True
			if old_solo_track:
				old_solo_track.is_solo = True
			if old_active_track:
				animData.nla_tracks.active = old_active_track

			controlRig.animation_data.use_tweak_mode = old_tweak_mode

	def exportMeshToFbx(self):
		if bpy.data.is_dirty:
			raise RuntimeError("please save file before export")
		try:
			self.doExportFbx()
		except:
			jx.file.revertBlenderFile()
			raise
		jx.file.revertBlenderFile()

	def exportAnimTrackToFbx(self, allTracks:bool):
		try:
			# if bpy.data.is_dirty:
			# 	raise RuntimeError("please save file before export")
			self.doExportAnimTrackToFbx(allTracks)
		finally:
			# jx.file.revertBlenderFile()
			pass
		
class OP_ExportAnimTrackToFbx(OP_Export):
	bl_idname = "scene.jx_export_to_fbx_anim_track"
	bl_label = "Export Anim Track"
	bl_options = {"REGISTER", "UNDO"}

	allTracks : bpy.props.BoolProperty(default=False)

	def doExport(self, context):
		if "JX_EXPORT" not in bpy.data.collections:
			raise RuntimeError("Error Export: Collection 'JX_EXPORT' ` not found")

		proj = jx.project.get()
		print(f"project.exportRoot = {proj.rawDataExportDir()}")

		self.collection = bpy.data.collections["JX_EXPORT"]
		self.outFilename = proj.exportFilename()

		self.exportAnimTrackToFbx(allTracks=self.allTracks)
		print(f"-------- Export Anim FINISHED --------\n")

	def execute(self, context):
		self.doExport(context)
		return {'FINISHED'}
	
class OP_ExportMeshToFbx(OP_Export):
	bl_idname = "scene.jx_export_to_fbx_mesh"
	bl_label = "Export Mesh"
	bl_options = {"REGISTER", "UNDO"}

	def doExport(self):
		if "JX_EXPORT" not in bpy.data.collections:
			raise RuntimeError("Error Export: Collection 'JX_EXPORT' ` not found")

		proj = jx.project.get()
		self.collection = bpy.data.collections["JX_EXPORT"]
		self.outFilename = proj.exportFilename()

		print(f"project.rawDataExportDir = {proj.rawDataExportDir()}")
		print(f"outFilename = {self.outFilename}")

		self.exportMeshToFbx()
		print(f"-------- Export FINISHED --------\n")

	def execute(self, context):
		# print(f"\n\n==== {self.__class__.__module__}.{self.__class__.__name__} ====")
		self.doExport()
		return {'FINISHED'}

class JX_MT_ExportToFbx(jx.types.Menu):
	bl_idname = 'JX_MT_ExportToFbx'
	bl_label = 'Export To Fbx'

	def draw(self, context):
		self.layout.operator(OP_ExportMeshToFbx.bl_idname)
		self.layout.operator(OP_ExportAnimTrackToFbx.bl_idname, text='Export Animation - Selected').allTracks = False
		self.layout.operator(OP_ExportAnimTrackToFbx.bl_idname, text='Export Animation - All').allTracks = True

class OP_FixSceneUnit(jx.types.Operator):
	bl_idname = "scene.jx_export_to_fbx_fix_scene_unit"
	bl_label = "Fix Scene Unit"
	bl_options = {"REGISTER", "UNDO"}

	mode: bpy.props.StringProperty()

	def execute(self, context):
		proj 				= jx.project.get(False)
		requireFps 			= proj.requireFps()
		requireUnitSystem	= proj.requireUnitSystem()
		requireScaleLength	= proj.requireScaleLength()
		requireLengthUnit	= proj.requireLengthUnit()
				
		if self.mode == "FPS":
			bpy.context.scene.render.fps = requireFps
		elif self.mode == "UNIT_SYSTEM":
			bpy.context.scene.unit_settings.system = requireUnitSystem

		elif self.mode == "LENGTH_UNIT":
			bpy.context.scene.unit_settings.length_unit = requireLengthUnit

		elif self.mode == "SCALE_LENGTH":
			if jx.math.almost_eq0(requireScaleLength):
				raise RuntimeError("Cannot set unt scale length to zero !!")
			bpy.context.scene.unit_settings.scale_length = requireScaleLength
			
			s = context.space_data
			if s and s.type == 'VIEW_3D':
				s.clip_start = 0.01 / requireScaleLength
				s.clip_end   = 1000 / requireScaleLength

		return {'FINISHED'}


class ExportPanel(jx.types.Panel):
	bl_idname = "JX_PT_EXPORT_PANEL"
	bl_label = "(JX) Export To Fbx"
	bl_order = 2000
	bl_space_type = "VIEW_3D"
	bl_region_type = "UI"
	bl_category = "JxBlender"

	def drawFixSceneUnit(self, context):
		proj 				= jx.project.get(False)
		requireFps 			= proj.requireFps()
		requireUnitSystem	= proj.requireUnitSystem()
		requireScaleLength	= proj.requireScaleLength()
		requireLengthUnit	= proj.requireLengthUnit()

		if requireFps:
			current_fps = context.scene.render.fps
			if requireFps != current_fps:
				col = self.layout.box().column()
				col.alert = True
				col.label(icon="ERROR", text="Invalid FPS")
				col.label(text=f"Current: {current_fps}")
				col.label(text=f"Require: {requireFps}")
				col.operator(OP_FixSceneUnit.bl_idname, text="Fix Now" ).mode = "FPS"

		if requireUnitSystem:
			current_unit_system = context.scene.unit_settings.system
			if requireUnitSystem != current_unit_system:
				col = self.layout.box().column()
				col.alert = True
				col.label(icon="ERROR", text="Invalid Unit System")
				col.label(text=f"Current: {current_unit_system}")
				col.label(text=f"Require: {requireUnitSystem}")
				col.operator(OP_FixSceneUnit.bl_idname, text="Fix Now" ).mode = "UNIT_SYSTEM"

		if requireLengthUnit:
			current_length_unit = context.scene.unit_settings.length_unit
			if requireLengthUnit != current_length_unit:
				col = self.layout.box().column()
				col.alert = True
				col.label(icon="ERROR", text="Invalid Length Unit")
				col.label(text=f"Current: {current_length_unit}")
				col.label(text=f"Require: {requireLengthUnit}")
				col.operator(OP_FixSceneUnit.bl_idname, text="Fix Now" ).mode = "LENGTH_UNIT"

		if requireScaleLength:
			current_scale_length = context.scene.unit_settings.scale_length
			if not jx.math.almost_eq(requireScaleLength, current_scale_length):
				col = self.layout.box().column()
				col.alert = True
				col.label(icon="ERROR", text="Invalid Unit Scale (Scale Length)")
				col.label(text=f"Current: {current_scale_length}")
				col.label(text=f"Require: {requireScaleLength}")
				col.operator(OP_FixSceneUnit.bl_idname, text="Fix Now" ).mode = "SCALE_LENGTH"

	def draw(self, context):
		self.drawFixSceneUnit(context)

		col = self.layout.column(align=True)
		col.operator(OP_ExportMeshToFbx.bl_idname, text="Export Mesh")

		row = col.row(align=True)
		row.operator(OP_ExportAnimTrackToFbx.bl_idname, text="Selected Track").allTracks = False
		row.operator(OP_ExportAnimTrackToFbx.bl_idname, text="All Tracks").allTracks = True

		col = self.layout.column(align=True)
		col.label(text="Open Folder")
		row = col.row(align=True)
		row.operator(jx.project.OP_open_file_in_file_explorer.bl_idname, text="This File")
		row.operator(jx.project.OP_open_export_folder.bl_idname, text="Export Folder")
