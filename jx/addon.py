import bpy

def get_module_classes(module):
	list = []
	for key in dir(module):
		v = getattr(module, key)
		if isinstance(v, type):
			list.append(v)
	return list

_registered_classes_list = []

def register_class(cls):
	# msg = f"jx:   register_class {cls.__module__}.{cls.__name__}"
	# if hasattr(cls, "bl_idname"):
	# 	msg += f" bl_idname={cls.bl_idname}"
	# print(msg)
	_registered_classes_list.append(cls)
	bpy.utils.register_class(cls)

def register_classes_in_module(module, baseClass):
	for cls in get_module_classes(module):
		if not issubclass(cls, baseClass): continue
		register_class(cls)

def unregister_all_classes():
	for cls in _registered_classes_list:
		#print(f"jx:   unregister_class {cls.__module__}.{cls.__name__}")
		bpy.utils.unregister_class(cls)
	_registered_classes_list.clear()

class OP_Reload(bpy.types.Operator):
	bl_idname = 'ui.jx_addon_reload'
	bl_label = 'Reload Jx'

	def execute(self, context):
		print("======== JxBlender OP_Reload ======")
		import addon_utils
		addon_utils.disable("jx")
		addon_utils.enable("jx")
		return {'FINISHED'}

class AddonPanel(bpy.types.Panel):
	bl_idname = "JX_PT_ADDON_PANEL"
	bl_label = "(JX) Development"
	bl_order = 39000
	bl_space_type = "VIEW_3D"
	bl_region_type = "UI"
	bl_category = "JxBlender"
#	bl_options = {'DEFAULT_CLOSED'}

	def draw(self, context):
		self.layout.operator(OP_Reload.bl_idname)
		self.layout.operator("wm.console_toggle")
