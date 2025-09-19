import bpy
import inspect
import os.path

import jx
import jx.reflection

class ReportErrorOperator(jx.types.Operator):
	bl_idname = "jx.debug_report_error"
	bl_label = "jx.debug_report_error"

	msg: bpy.props.StringProperty()

	def execute(self, context):
		#this is where I send the message
		self.report({'ERROR'}, self.msg)
		return {'CANCELLED'}

def reportError(msg):
	bpy.ops.jx.debug_report_error('INVOKE_DEFAULT', msg=msg)

def dump(obj):
	info = inspect.getframeinfo(inspect.stack()[1][0])
	print(f"---- jx.debug.dump cls={obj.__class__} file={os.path.basename(info.filename)}, line={info.lineno}, function={info.function} ----")
	print(obj)
	for attr in dir(obj):
		v = getattr(obj, attr)
		print(f"  .{attr} ({jx.reflection.classname(v)}) = {v}")

def deepPrint(obj, lv=0):
	print(obj)
	if isinstance(obj, dict):
		for k,v in obj.items():
			print(f"\n{k} {v.__class__}")
			deepPrint(v)

