
import bpy
import jx.types

def get_all(obj):
	o = {}
	for key in obj.keys():
		o[key] = obj[key]
	return o

def get_all_jx_prop(obj):
	o = {}
	for key in obj.keys():
		if key.startswith("jx_"):
			o[key] = obj[key]
	return o

def get_value(obj, name):
	return obj[name]

def set_value(obj, name, value):
	obj[name] = value

def add_if_not_exists(obj, name, value):
	if hasattr(obj, name): return
	obj[name] = value

def remove(obj, name):
	del obj[name]

def material_add_jx_custom_props(mat):
	add_if_not_exists(mat, "jx_mat_test", "")

def object_add_jx_custom_props(obj):
	if obj == None: return
	add_if_not_exists(obj, "jx_test", "")
	for slot in obj.material_slots:
		mat = slot.material
		if mat == None: continue
		material_add_jx_custom_props(mat)

class OP_add_jx_custom_props(jx.types.Operator):
	bl_idname = "object.jx_add_jx_custom_props"
	bl_label  = "Add Jx Custom Properties"
	bl_options = {"REGISTER", "UNDO"}

	def execute(self, context):
		for obj in bpy.context.selected_objects:
			object_add_jx_custom_props(obj)
		return {'FINISHED'}

class JX_MT_CustomProp(bpy.types.Menu):
	bl_idname = 'JX_MT_CustomProp'
	bl_label = 'Custom Prop'

	def draw(self, context):
		self.layout.operator(OP_add_jx_custom_props.bl_idname)
