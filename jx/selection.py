from numpy import isin
import bpy

def deselect_all():
	bpy.context.view_layer.objects.active = None
	bpy.ops.object.select_all(action='DESELECT')

def add(obj):
	if obj is None:
		return

	if isinstance(obj, str):
		if obj not in bpy.context.view_layer.objects:
			print(f"object {obj} not found")
			return
		add(bpy.context.view_layer.objects[obj])
		return

	if isinstance(obj, list) \
	or isinstance(obj, set) \
	or isinstance(obj, bpy.types.bpy_prop_collection):
		for o in obj:
			add(o)
		return

	obj.select_set(True)

def select(obj):
	deselect_all()
	add(obj)