import os
import bpy
import json

import jx
import jx.file

_instance = None

class Project:
	def __init__(self):
		self._name = None
		self._root = None
		self._curFile = None
		self._relPath = None
		self._rawDataPath = None
		self._rawDataExportDir = None

		curFile = jx.file.currentBlenderFilename()
		if not curFile:
			raise RuntimeError("no path for current file, please save file is not yet saved")

		root = jx.path.dirname(curFile)

		while True:
			projectFilename = jx.path.realpath(root + "/JxProject.json")
			# print("  try read " + projectFilename)
			parent = jx.path.dirname(root)
			if parent == root:
				raise RuntimeError("cannot find JxProject.json in parent folders")
			if jx.path.exists(projectFilename):
				break
			root = parent

		self._root = root
		self._rawDataPath = root + "/RawData"
		self._loadJson(projectFilename)
		self._curFile = curFile
		self._curFileRelPath = jx.path.relpath(curFile, self._rawDataPath)

	def name(self):
		return self._name
	
	def root(self):
		return self._root

	def curFile(self):
		return self._curFile

	def curFileRelPath(self):
		return self._curFileRelPath

	def rawDataExportDir(self):
		return jx.path.realpath(self._root + "/" + self._rawDataExportDir)

	def exportFilename(self):
		p = f"{self.rawDataExportDir()}/{self._curFileRelPath}"
		return jx.path.realpath(jx.path.remove_ext(p))

	def exportUnrealContentFolder(self):
		p = f"{self.root()}/Unreal/{self._curFileRelPath}"
		p = jx.path.remove_ext(p)
		return jx.path.realpath(p)

	def _loadJson(self, filename):
		print(f"loadJson({filename})")
		with open(filename, 'r') as f:
			data = json.load(f)

		if "rawDataExportDir" not in data:
			raise RuntimeError('missing "rawDataExportDir" in JxProject.json')
		self._rawDataExportDir = data['rawDataExportDir']

def get():
	global _instance
	if not _instance or _instance._curFile != bpy.data.filepath:
		_instance = Project()
	return _instance

class OP_open_file_in_file_explorer(jx.types.Operator):
	bl_idname = "ui.jx_open_file_in_file_explorer"
	bl_label  = "Open in File Explorer"

	def execute(self, context):
		file = bpy.data.filepath
		if file == None:
			return

		path = os.path.dirname(file)
		print(f"Open in Explorer \"{path}\"")
		os.startfile(path)
		return {'FINISHED'}

class OP_open_export_folder(jx.types.Operator):
	bl_idname = "ui.jx_open_export_folder"
	bl_label  = "Open Export folder"

	def execute(self, context):
		proj = get()
		path = os.path.dirname(proj.exportFilename())
		print(f"Open in Explorer \"{path}\"")
		os.startfile(path)
		return {'FINISHED'}

class OP_open_unreal_content_folder(jx.types.Operator):
	bl_idname = "ui.jx_open_unreal_content_folder"
	bl_label  = "Open Unreal Content folder"

	def execute(self, context):
		proj = get()
		path = os.path.dirname(proj.exportUnrealContentFolder())
		print(f"Open in Explorer \"{path}\"")
		os.startfile(path)
		return {'FINISHED'}


class JX_MT_MainMenu_Project(bpy.types.Menu):
	bl_idname = 'JX_MT_MainMenu_Project'
	bl_label = 'Project'

	def draw(self, context):
		self.layout.operator(OP_open_file_in_file_explorer.bl_idname)
		self.layout.separator()
		self.layout.operator(OP_open_export_folder.bl_idname)
		self.layout.operator(OP_open_unreal_content_folder.bl_idname)