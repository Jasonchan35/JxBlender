import shutil
import bpy
import os
import os.path
import jx.path

def currentBlenderFilename():
	return jx.path.to_unix(bpy.data.filepath)

def revertBlenderFile():
	bpy.ops.wm.revert_mainfile()

def exists(p:str):
	return jx.path.exists(p) and os.path.isfile(p)

def last_modify_time(filename:str):
	return os.path.getmtime(filename)

def copy(original:str, target:str):
	print(f"jx.file.copy '{original}'->'{target}'")
	
	if not exists(original):
		raise RuntimeError(f"copy file error: original file doesn't exists {original}")

	os.makedirs(jx.path.dirname(target), exist_ok=True)
	shutil.copy(original, target)

def copy_if_newer(original:str, target:str):
	if not exists(original):
		raise RuntimeError(f"copy file error: original file doesn't exists {original}")

	if exists(target):
		if last_modify_time(target) > last_modify_time(original):
			return

	print(f"jx.file.copy_if_newer '{original}'->'{target}'")
	os.makedirs(jx.path.dirname(target), exist_ok=True)
	shutil.copy(original, target)
