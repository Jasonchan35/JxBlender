import os
import bpy
import json

import jx
import jx.file
import jx.path

_instance = None

class Project:
	def __init__(self, reportError):
		self._root = None
		self._curFile = None
		self._curFileRelPath = None
		self._relPath = None
		self._rawDataPath = None
		self._rawDataExportDir = None

		if True: # Unreal
			self._requireFps = None
			self._requireUnitsystem = "METRIC"
			self._requireLengthUnit = "CENTIMETERS"
			self._requireScaleLength = 0.01
		else:
			self._requireFps = None # 24
			self._requireUnitsystem = None
			self._requireLengthUnit = None # "METERS"
			self._requireScaleLength = None # 1

		curFile = jx.file.currentBlenderFilename()
		if not curFile:
			if not reportError: return
			raise RuntimeError("no path for current file, please save file is not yet saved")

		projectFilename = jx.path.findFileUpward(jx.path.dirname(curFile), "JxProject.json")
		if projectFilename is None:
			if not reportError: return
			raise RuntimeError("cannot find JxProject.json in parent folders")

		self._root = jx.path.dirname(projectFilename)
		self._loadJson(projectFilename)
		self._curFile = curFile
		self._curFileRelPath = jx.path.relpath(curFile, self.rawDataPath())

	def root(self):
		return self._root

	def curFile(self):
		return self._curFile

	def curFileRelPath(self):
		return self._curFileRelPath

	def rawDataPath(self):
		if not self._rawDataPath: return self._root
		if os.path.isabs(self._rawDataPath): return self._rawDataPath
		return jx.path.realpath(self._root + "/" + self._rawDataPath)

	def rawDataExportDir(self):
		if not self._rawDataExportDir: return self._root
		if os.path.isabs(self._rawDataExportDir):
			return self._rawDataExportDir
		return jx.path.realpath(self._root + "/" + self._rawDataExportDir)

	def exportFilename(self):
		p = f"{self.rawDataExportDir()}/{self._curFileRelPath}"
		return jx.path.realpath(jx.path.remove_ext(p))

	def exportUnrealContentFolder(self):
		p = f"{self.root()}/Unreal/{self._curFileRelPath}"
		p = jx.path.remove_ext(p)
		return jx.path.realpath(p)
	
	def requireFps(self): return self._requireFps
	def requireUnitSystem(self): return self._requireUnitSystem
	def requireLengthUnit(self): return self._requireLengthUnit
	def requireScaleLength(self): return self._requireScaleLength

	def _loadJson(self, filename):
		print(f"loadJson({filename})")
		with open(filename, 'r') as f:
			data = json.load(f)

		if "rawDataPath" not in data:
			raise RuntimeError('missing "rawDataPath" in JxProject.json')

		if "rawDataExportDir" not in data:
			raise RuntimeError('missing "rawDataExportDir" in JxProject.json')

		self._rawDataPath 			= data.get('rawDataPath')
		self._rawDataExportDir 		= data.get('rawDataExportDir')
		self._requireFps 			= data.get('requireFps')
		self._requireUnitSystem		= data.get('requireUnitSystem')
		self._requireLengthUnit 	= data.get('requireLengthUnit')
		self._requireScaleLength 	= data.get('requireScaleLength')

def get(reportError=True):
	global _instance
	if not _instance or _instance._curFile != jx.file.currentBlenderFilename():
		_instance = Project(reportError)
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