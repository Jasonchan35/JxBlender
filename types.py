import bpy

class Menu(bpy.types.Menu):
	pass

class Operator(bpy.types.Operator):
	def reportError(self, msg):
		self.report({"ERROR"}, msg)

	def reportWarning(self, msg):
		self.report({"WARNING"}, msg)

	def reportInfo(self, msg):
		self.report({"INFO"}, msg)

	def reportDebug(self, msg):
		self.report({"DEBUG"}, msg)

class Panel(bpy.types.Panel):
	pass

class PropertyGroup(bpy.types.PropertyGroup):
	pass

class UIList(bpy.types.UIList):
	pass