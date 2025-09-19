import bpy
import jx.export
import jx.addon
import jx.project
import jx.types
import jx.custom_prop
import jx.export
import jx.util

class JX_MT_MainMenu_Development(bpy.types.Menu):
	bl_idname = 'JX_MT_MainMenu_Development'
	bl_label = 'Development'

	def draw(self, context):
		self.layout.operator(jx.addon.OP_Reload.bl_idname)
		self.layout.operator("wm.console_toggle")


class JX_MT_MainMenu(jx.types.Menu):
	bl_idname = "JX_MT_MainMenu"
	bl_label = "JxBlender"

	def draw(self, context):
		self.layout.menu(jx.export.ExportToFbx.JX_MT_MainMenu_ExportToFbx.bl_idname)
		self.layout.menu(jx.project.JX_MT_MainMenu_Project.bl_idname)
		self.layout.menu(jx.custom_prop.JX_MT_MainMenu_CustomProp.bl_idname)
		self.layout.separator()
		self.layout.menu(JX_MT_MainMenu_Development.bl_idname)

def menu_func(self, context):
	layout = self.layout
	layout.menu(JX_MT_MainMenu.bl_idname)

addon_keymaps = []

def register():
	bpy.types.TOPBAR_MT_editor_menus.append(menu_func)

	# Add the hotkey
	## !TODO - remove when unregister
	# wm = bpy.context.window_manager
	# kc = wm.keyconfigs.addon
	# if kc:
	# 	km = wm.keyconfigs.addon.keymaps.new(name='3D View', space_type='VIEW_3D')
	# 	kmi = km.keymap_items.new(JxCoreMainMenu.bl_idname, type='T', value='PRESS', ctrl=True)
	# 	addon_keymaps.append((km, kmi))

def unregister():
	bpy.types.TOPBAR_MT_editor_menus.remove(menu_func)