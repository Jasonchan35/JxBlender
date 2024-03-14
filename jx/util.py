import bpy
import jx.types

def clearPropCollection(c: bpy.types.bpy_prop_collection):
	ls = []
	for e in c:
		ls.append(e)

	for e in ls:
		c.remove(e)

def resetTransform(obj):
	obj.location = (0,0,0)
	obj.rotation_quaternion = (1,0,0,0)
	obj.rotation_euler = (0,0,0)
	obj.scale = (1,1,1)

def isLibraryEditable(obj):
	ov = obj.override_library
	if ov and ov.is_system_override: # system_override means non-editable
		return False
	return True

def newObject(name, type):
	obj = bpy.data.objects.new(name, type)
	if obj: bpy.context.scene.collection.objects.link(obj)
	return obj

def deleteObject(obj):
	if not obj: return
	bpy.data.objects.remove(obj, do_unlink=True)

