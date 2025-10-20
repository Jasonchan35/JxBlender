import bpy
import re
import jx.custom_prop

def show_all_lod_levels(bShow):
	for obj in bpy.context.scene.objects:
		if re.search(r"_LOD\d+$", obj.name):
			obj.hide_set(not bShow)

def show_lod_level(show_level):
	for obj in bpy.context.scene.objects:
		if re.search(r"_LOD\d+$", obj.name):
			name_parts = obj.name.split("_LOD")
			if (len(name_parts) < 2):
				continue
			try:
				lv = (int)(name_parts[-1])
				obj.hide_set(lv != show_level)
			except:
				continue

def object_add_fbx_lod_grop_custom_prop(obj):
	if obj == None: return
	jx.custom_prop.add_if_not_exists(obj, "fbx_type", "LodGroup")

class OP_add_fbx_lod_group_custom_prop(jx.types.Operator):
	bl_idname = "object.jx_add_fbx_lod_group_custom_prop"
	bl_label  = "Add FBX LOD Group Custom Propertie"
	bl_options = {"REGISTER", "UNDO"}

	def execute(self, context):
		for obj in bpy.context.selected_objects:
			object_add_fbx_lod_grop_custom_prop(obj)
		return {'FINISHED'}	

class OP_show_lod_level(jx.types.Operator):
	bl_idname = "object.jx_show_lod_level"
	bl_label  = "Show LOD Level"
	bl_options = {"REGISTER", "UNDO"}

	show_level: bpy.props.IntProperty(
		name="ShowLevel",
		description="",
		default=0
	)

	def execute(self, context):
		show_lod_level(self.show_level)
		return {'FINISHED'}	


class OP_show_all_lod_levels(jx.types.Operator):
	bl_idname = "object.jx_show_all_lod_levels"
	bl_label  = "Show All LOD"
	bl_options = {"REGISTER", "UNDO"}

	bShow: bpy.props.BoolProperty(
		name="Show",
		description="",
		default=True
	)

	def execute(self, context):
		show_all_lod_levels(self.bShow)
		return {'FINISHED'}	

class JX_MT_LOD(jx.types.Menu):
	bl_idname = 'JX_MT_LOD'
	bl_label = 'LOD'

	def draw(self, context):
		self.layout.operator(OP_add_fbx_lod_group_custom_prop.bl_idname)

class ExportPanel(jx.types.Panel):
	bl_idname = "JX_PT_LOD_PANEL"
	bl_label = "(JX) LODs"
	bl_order = 2000
	bl_space_type = "VIEW_3D"
	bl_region_type = "UI"
	bl_category = "JxBlender"

	def draw(self, context):
		col = self.layout.column(align=True)

		row = col.row(align=True)
		row.operator(OP_show_all_lod_levels.bl_idname, text="Show All").bShow = True
		row.operator(OP_show_all_lod_levels.bl_idname, text="Hide All").bShow = False

		row = col.row(align=True)
		row.operator(OP_show_lod_level.bl_idname, text="0").show_level = 0
		row.operator(OP_show_lod_level.bl_idname, text="1").show_level = 1
		row.operator(OP_show_lod_level.bl_idname, text="2").show_level = 2
		row.operator(OP_show_lod_level.bl_idname, text="3").show_level = 3
		row.operator(OP_show_lod_level.bl_idname, text="4").show_level = 4

		col.label(text="Custom Props")
		row = col.row(align=True)
		row.operator(OP_add_fbx_lod_group_custom_prop.bl_idname, text="Add LodGroup Prop")
