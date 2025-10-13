import bpy
import os
import jx.types
import bpy.props
import re

def set_collider_parent():
	bpy.ops.object.mode_set(mode='OBJECT')
	selected_objects = bpy.context.selected_objects

	for obj in selected_objects:
		if obj.type == 'MESH' and obj.name.startswith('UCX_'):
			parent_name = obj.name.replace('UCX_', '')
			parent_obj = bpy.context.scene.objects.get(parent_name)
			if parent_obj:
				obj.parent = None
				obj.parent = parent_obj
				obj.matrix_parent_inverse = parent_obj.matrix_world.inverted()
	bpy.context.view_layer.update()

def hide_unreal_colliders(bHide):
	bpy.ops.object.mode_set(mode='OBJECT')
	all_objects = bpy.context.scene.objects
	for obj in all_objects:
		if obj.name.startswith('UCX_'):
			# obj.hide_viewport = bHide
			# obj.hide_render = bHide
			obj.hide_set(bHide)
	bpy.context.view_layer.update()

def set_unreal_colliders_display_type(displayType):
	bpy.ops.object.mode_set(mode='OBJECT')
	all_objects = bpy.context.scene.objects
	for obj in all_objects:
		if obj.name.startswith('UCX_'):
			obj.display_type = displayType
	bpy.context.view_layer.update()

def lineup_selected_objects(distance = 10, objects_per_row = 10):
	bpy.ops.object.mode_set(mode='OBJECT')

	selected_objects = bpy.context.selected_objects
	for i, obj in enumerate(selected_objects):
		row = i // objects_per_row
		col = i % objects_per_row
		obj.location = (
			col * distance,  # X-axis position
			row * distance,  # Y-axis position
			0.0              # Z-axis position
		)
	bpy.context.view_layer.update()

def rename_objects_and_meshes():
	"""Rename objects and meshes ending with xxx_<digit> to xxx<digit>."""
	bpy.ops.object.mode_set(mode='OBJECT')
	pattern = r"_(\d+)$"
	all_objects = bpy.context.scene.objects

	for obj in all_objects:
		match = re.search(pattern, obj.name)
		if match:
			digit = match.group(1)
			new_name = re.sub(r"_\d+$", f"{digit}", obj.name)
			obj.name = new_name

			if obj.type == 'MESH' and obj.data:
				obj.data.name = new_name

			if obj.data.materials:
				mat = obj.data.materials[0]
				if mat:
					material_match = re.search(pattern, mat.name)
					if material_match:
						new_material_name = re.sub(r"_\d+$", f"{digit}", mat.name)
						mat.name = new_material_name

	# Update the scene
	bpy.context.view_layer.update()

def assign_textures_to_selected(texture_path="//Textures"):
	"""Assign color and normal textures to the first material of selected objects."""
	# Switch to object mode
	bpy.ops.object.mode_set(mode='OBJECT')

	# Get selected objects
	selected_objects = bpy.context.selected_objects

	for obj in selected_objects:
		if obj.type != 'MESH':
			continue

		# Check if object has materials; if not, create one
		if not obj.data.materials:
			mat = bpy.data.materials.new(name=f"MI_{obj.name}_material")
			mat.use_nodes = True
			obj.data.materials.append(mat)
		else:
			# Use the first material
			mat = obj.data.materials[0]
			if not mat.use_nodes:
				mat.use_nodes = True

		# Get the material's node tree
		nodes = mat.node_tree.nodes
		links = mat.node_tree.links

		# Clear existing nodes
		nodes.clear()

		# Create Principled BSDF shader
		shader = nodes.new(type='ShaderNodeBsdfPrincipled')
		shader.location = (0, 0)

		# Create Output node
		output = nodes.new(type='ShaderNodeOutputMaterial')
		output.location = (300, 0)

		# Link shader to output
		links.new(shader.outputs['BSDF'], output.inputs['Surface'])

		# Create texture nodes
		color_tex = nodes.new(type='ShaderNodeTexImage')
		color_tex.location = (-300, 100)
		normal_tex = nodes.new(type='ShaderNodeTexImage')
		normal_tex.location = (-300, -200)

		# Create normal map node
		normal_map = nodes.new(type='ShaderNodeNormalMap')
		normal_map.location = (-100, -200)

		obj_basename = obj.name
		if obj_basename.startswith("SM_"):
			obj_basename = obj_basename[3:]

		# Set texture file paths (relative to blend file)
		color_file  = os.path.join(texture_path, f"T_{obj_basename}_Color.png")
		normal_file = os.path.join(texture_path, f"T_{obj_basename}_Normal.png")

		# Convert to relative path and load textures if files exist
		color_file_abs = bpy.path.abspath(color_file)
		normal_file_abs = bpy.path.abspath(normal_file)
		if os.path.exists(color_file_abs):
			color_file_rel = bpy.path.relpath(color_file_abs)
			color_tex.image = bpy.data.images.load(color_file_abs, check_existing=True)
			color_tex.image.filepath = color_file_rel  # Ensure relative path is stored
		if os.path.exists(normal_file_abs):
			normal_file_rel = bpy.path.relpath(normal_file_abs)
			normal_tex.image = bpy.data.images.load(normal_file_abs, check_existing=True)
			normal_tex.image.filepath = normal_file_rel  # Ensure relative path is stored
			normal_tex.image.colorspace_settings.name = 'Non-Color'  # Set normal map to Non-Color

		# Link textures to shader
		links.new(color_tex.outputs['Color'], shader.inputs['Base Color'])
		links.new(normal_tex.outputs['Color'], normal_map.inputs['Color'])
		links.new(normal_map.outputs['Normal'], shader.inputs['Normal'])

	# Update the scene
	bpy.context.view_layer.update()	

class OP_unreal_show_all_colliders(jx.types.Operator):
	bl_idname = "object.jx_unreal_show_all_colliders"
	bl_label = "Show - All Unreal Colliders"
	bl_options = {"REGISTER", "UNDO"}

	def execute(self, context):
		hide_unreal_colliders(False)
		return {'FINISHED'}

class OP_unreal_hide_all_colliders(jx.types.Operator):
	bl_idname = "object.jx_unreal_hide_all_colliders"
	bl_label = "Hide - All Unreal Colliders"
	bl_options = {"REGISTER", "UNDO"}

	def execute(self, context):
		hide_unreal_colliders(True)
		return {'FINISHED'}

class OP_unreal_set_all_colliders_display_type_to_wire(jx.types.Operator):
	bl_idname = "object.jx_unreal_set_all_colliders_display_type"
	bl_label = "Set All Unreal Colliders Display Type - WIRE"
	bl_options = {"REGISTER", "UNDO"}

	def execute(self, context):
		set_unreal_colliders_display_type('WIRE')
		return {'FINISHED'}

class OP_unreal_fix_collider_parent(jx.types.Operator):
	bl_idname = "object.jx_unreal_set_collider_parent"
	bl_label = "Fix Unreal Collider Parent"
	bl_options = {"REGISTER", "UNDO"}

	def execute(self, context):
		set_collider_parent()
		return {'FINISHED'}
	
class OP_unreal_lineup_selected_objects(jx.types.Operator):
	bl_idname = "object.jx_unreal_lineup_selected_objects"
	bl_label = "Lineup Selected Objects"
	bl_options = {"REGISTER", "UNDO"}

	distance: bpy.props.FloatProperty(
		name="Distance",
		description="Distance between objects",
		default=100.0
	)

	objects_per_row: bpy.props.IntProperty(
		name="Objects Per Row",
		description="Number of objects per row",
		default=10
	)

	def execute(self, context):
		lineup_selected_objects(self.distance, self.objects_per_row)
		return {'FINISHED'}
	
class OP_unreal_rename_objects_and_meshes(jx.types.Operator):
	bl_idname = "object.jx_unreal_rename_objects_and_meshes"
	bl_label = "Rename objects and meshes"
	bl_options = {"REGISTER", "UNDO"}

	def execute(self, context):
		rename_objects_and_meshes()
		return {'FINISHED'}

class OP_unreal_assign_textures_to_selected(jx.types.Operator):
	bl_idname = "object.jx_unreal_assign_textures_to_selected"
	bl_label = "Assign textures to Selected"
	bl_options = {"REGISTER", "UNDO"}

	def execute(self, context):
		assign_textures_to_selected()
		return {'FINISHED'}

class JX_MT_Unreal(bpy.types.Menu):
	bl_idname = 'JX_MT_Unreal'
	bl_label = 'Unreal'

	def draw(self, context):
		self.layout.operator(OP_unreal_show_all_colliders.bl_idname)
		self.layout.operator(OP_unreal_hide_all_colliders.bl_idname)
		self.layout.separator()
		self.layout.operator(OP_unreal_fix_collider_parent.bl_idname)
		self.layout.separator()
		self.layout.operator(OP_unreal_lineup_selected_objects.bl_idname)
		self.layout.operator(OP_unreal_set_all_colliders_display_type_to_wire.bl_idname)
		self.layout.operator(OP_unreal_rename_objects_and_meshes.bl_idname)
		self.layout.operator(OP_unreal_assign_textures_to_selected.bl_idname)
