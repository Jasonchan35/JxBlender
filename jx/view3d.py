import bpy
import jx.util

from math import radians
from math import degrees

from mathutils import Euler
from mathutils import Vector
from mathutils import Matrix

def getActivePoseBone():
	obj = bpy.context.object
	if bpy.context.mode != 'POSE': return None
	if not obj or not obj.type == "ARMATURE": return None

	bone = obj.data.bones.active
	if not bone: return None

	return obj.pose.bones[bone.name]

class OP_FixView3dClipStartEnd(jx.types.Operator):
	bl_idname = "scene.jx_fix_view3d_clip_start_end"
	bl_label = "Fix View Clip Start End"
	bl_options = {"REGISTER", "UNDO"}

	def execute(self, context):
		scale_length = bpy.context.scene.unit_settings.scale_length
		if not jx.math.almost_eq0(scale_length):
			s = context.space_data
			if s and s.type == 'VIEW_3D':
				s.clip_start = 0.01 / scale_length
				s.clip_end   = 1000 / scale_length

		return {'FINISHED'}


class OP_QuickTransform(jx.types.Operator):
	bl_idname = "object.jx_quick_transform"
	bl_label = "Quick Transform"
	bl_options = {"REGISTER", "UNDO"}

	mode: bpy.props.StringProperty()

	def execute(self, context):
		if self.mode.startswith("WORLD_RZ:"):
			value = float(self.mode.split(':', 1)[1])
			bpy.ops.transform.rotate(value=-radians(value), orient_axis='Z', orient_type='GLOBAL')
		return {'FINISHED'}
	
class ItemTrasnformPanel(jx.types.Panel):
	bl_idname = "JX_PT_ITEM_TRANSFORM_PANEL"
	bl_label = "(JX) Transform"
	bl_order = 1000
	bl_space_type = "VIEW_3D"
	bl_region_type = "UI"
	bl_category = "Item"
	# bl_options = {'DEFAULT_CLOSED'}

	def drawTransform(self, context):
		target = context.object # bpy.context.object
		poseBone = getActivePoseBone()
		if poseBone:
			target = poseBone

		col = self.layout.column(align=True)
		row = col.row(align=True)
		row.label(text="Loc")

		if poseBone: op = "pose.loc_clear"
		else: 		 op = "object.location_clear"
		row.operator(op, icon="LOOP_BACK", text="")

		row = col.row(align=True)
		row.prop(target, "location", index=0, text="")
		row.prop(target, "location", index=1, text="")
		row.prop(target, "location", index=2, text="")

		col.separator()
		row = col.row(align=True)
		row.label(text="Rotation")

		row.prop(target, "rotation_mode", text="")

		if poseBone: op = "pose.rot_clear"
		else: 		 op = "object.rotation_clear"
		row.operator(op, icon="LOOP_BACK", text="")

		vertical_rot = False

		row = col.row(align=True)

		if target.rotation_mode == "QUATERNION":
			row.prop(target, "rotation_quaternion", index=0, text="")
			row.prop(target, "rotation_quaternion", index=1, text="")
			row.prop(target, "rotation_quaternion", index=2, text="")
			row.prop(target, "rotation_quaternion", index=3, text="")
		elif target.rotation_mode == "AXIS_ANGLE":
			row.prop(target, "rotation_axis_angle", index=0, text="")
			row.prop(target, "rotation_axis_angle", index=1, text="")
			row.prop(target, "rotation_axis_angle", index=2, text="")
			row.prop(target, "rotation_axis_angle", index=3, text="")
		else:
			row.prop(target, "rotation_euler", index=0, text="")
			row.prop(target, "rotation_euler", index=1, text="")
			row.prop(target, "rotation_euler", index=2, text="")

		col.separator()
		row = col.row(align=True)
		row.label(text="Scale")

		if poseBone: op = "pose.scale_clear"
		else: 		 op = "object.scale_clear"
		row.operator(op, icon="LOOP_BACK", text="")

		row = col.row(align=True)
		row.prop(target, "scale", index=0, text="")
		row.prop(target, "scale", index=1, text="")
		row.prop(target, "scale", index=2, text="")


	def draw(self, context):
		if context.object == None: return

		self.drawTransform(context)

class ItemTrasnformToolPanel(jx.types.Panel):
	bl_idname = "JX_PT_ITEM_TRANSFORM_TOOL_PANEL"
	bl_label = "(JX) Transform Tool"
	bl_order = 1005
	bl_space_type = "VIEW_3D"
	bl_region_type = "UI"
	bl_category = "Item"
	bl_options = {'DEFAULT_CLOSED'}

	def draw(self, context):
		if context.object == None: return

		col = self.layout.column(align=True)

		col.label(text="Snap")
		row = col.row(align=True)
		row.operator("view3d.snap_cursor_to_selected", text="Cursor To Selected")
		# row.operator("view3d.snap_cursor_to_center", text="Zero")
		row.operator("view3d.snap_cursor_to_grid",   text="", icon="SNAP_GRID")

		row = col.row(align=True)
		row.operator("view3d.snap_selected_to_cursor", text="Selected To Cursor")
		# row.operator("view3d.snap_selected_to_cursor", text="Offset").use_offset = False
		row.operator("view3d.snap_selected_to_grid",   text="", icon="SNAP_GRID")

		col.label(text="Rotate Z (World)")
		row = col.row(align=True)
		row.operator(OP_QuickTransform.bl_idname, text="-15").mode = "WORLD_RZ:-15"
		row.operator(OP_QuickTransform.bl_idname, text="-30").mode = "WORLD_RZ:-30"
		row.operator(OP_QuickTransform.bl_idname, text="-45").mode = "WORLD_RZ:-45"
		row.operator(OP_QuickTransform.bl_idname, text="-60").mode = "WORLD_RZ:-60"
		row.operator(OP_QuickTransform.bl_idname, text="-90").mode = "WORLD_RZ:-90"
		row = col.row(align=True)
		row.operator(OP_QuickTransform.bl_idname, text="+15").mode = "WORLD_RZ:+15"
		row.operator(OP_QuickTransform.bl_idname, text="+30").mode = "WORLD_RZ:+30"
		row.operator(OP_QuickTransform.bl_idname, text="+45").mode = "WORLD_RZ:+45"
		row.operator(OP_QuickTransform.bl_idname, text="+60").mode = "WORLD_RZ:+60"
		row.operator(OP_QuickTransform.bl_idname, text="+90").mode = "WORLD_RZ:+90"



class InfoPanel(jx.types.Panel):
	bl_idname = "JX_PT_VIEW3D_INFO_PANEL"
	bl_label = "(JX) Info"
	bl_order = 2000
	bl_space_type = "VIEW_3D"
	bl_region_type = "UI"
	bl_category = "Item"
	bl_options = {'DEFAULT_CLOSED'}
	# bl_options = {'DEFAULT_CLOSED'}

	def drawItem(self, layout, label, text):
		row = layout.split(factor=0.2, align=True)
		row.alignment = "RIGHT"
		row.label(text=label)
		row.alignment = "LEFT"
		row.label(text=text)

	def drawTransformInfo(self, matrix, text=""):
		col = self.layout.column()
		if text:
			col.label(text=text)

		col2 = col.box().column(align=True)

		loc = matrix.to_translation()
		self.drawItem(col2, "Loc:", f"({loc.x:0.3f}, {loc.y:0.3f}, {loc.z:0.3f})")

		euler = matrix.to_euler()
		self.drawItem(col2, "Rot:", f"({degrees(euler.x):0.3f}, {degrees(euler.y):0.3f}, {degrees(euler.z):0.3f})")

		scale = matrix.to_scale()
		self.drawItem(col2, "Scale:", f"({scale.x:0.3f}, {scale.y:0.3f}, {scale.z:0.3f})")

	def draw(self, context):
		if context.object == None: return
		
		obj = bpy.context.object
		if not obj: return

		name = obj.name
		matrix_local = obj.matrix_local
		matrix_world = obj.matrix_world

		poseBone = getActivePoseBone()
		if poseBone:
			name = poseBone.name
			matrix_local = poseBone.matrix
			matrix_world = matrix_world @ poseBone.matrix

		self.layout.label(text=f"name = {name}")

		self.drawTransformInfo(matrix_local, text="Final Local Transform:")
		self.drawTransformInfo(matrix_world, text="Final World Transform:")

class View3dPanel(jx.types.Panel):
	bl_idname = "JX_PT_VIEW3D_PANEL"
	bl_label = "(JX) View 3D"
	bl_order = 9000
	bl_space_type = "VIEW_3D"
	bl_region_type = "UI"
	bl_category = "JX"
	bl_options = {'DEFAULT_CLOSED'}

	def draw(self, context):
		overlay = context.space_data.overlay
		col = self.layout.column(align=True)
		col.use_property_split = True

		col.prop(overlay, "show_stats")
		col.prop(overlay, "show_wireframes")
		col.prop(overlay, "show_face_orientation")

		view3d = bpy.context.space_data
		if view3d.type == 'VIEW_3D':
			col.separator()

			col.prop(view3d, "clip_start", text="Clip Start")
			col.prop(view3d, "clip_end",   text="End")

			col.separator()
			col.operator(OP_FixView3dClipStartEnd.bl_idname, text="Fit Clip to Unit Scale")

