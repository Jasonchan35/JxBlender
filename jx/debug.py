import bpy
import inspect
import os.path

from jx.reflection import classname

g_error_msg = ""

class ErrorOperator(bpy.types.Operator):
	bl_idname = "jx.error_operator"
	bl_label = "jx.error_operator"

	def execute(self, context):
		global g_error_msg
		#this is where I send the message
		self.report({'ERROR'}, g_error_msg)

		return {'CANCELLED'}

# def error(msg):
# 	global g_error_msg
# 	g_error_msg = msg
# 	bpy.ops.jx.error_operator()

def dump(obj):
	info = inspect.getframeinfo(inspect.stack()[1][0])
	print(f"---- jx.debug.dump cls={obj.__class__} file={os.path.basename(info.filename)}, line={info.lineno}, function={info.function} ----")
	print(obj)
	for attr in dir(obj):
		v = getattr(obj, attr)
		print(f"  .{attr} ({classname(v)}) = {v}")

def deepPrint(obj, lv=0):
	print(obj)
	if isinstance(obj, dict):
		for k,v in obj.items():
			print(f"\n{k} {v.__class__}")
			deepPrint(v)

