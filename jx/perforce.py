import os
import json
import subprocess

import jx
import jx.file
import jx.path

PerUserSettings_instance = None
SettingsFileName = "JxP4_PerUserSettings.json"

class PerUserSettings:
	def __init__(self):
		self.workspace = None
		self._curFile = None

		curFile = jx.file.currentBlenderFilename()
		if not curFile:
			return

		jsonFilename = jx.path.findFileUpward(jx.path.dirname(curFile), SettingsFileName)
		if jsonFilename is None:
			return

		self._loadJson(jsonFilename)
		self._curFile = curFile

	def _loadJson(self, filename):
		print(f"loadJson({filename})")
		with open(filename, 'r') as f:
			data = json.load(f)

		if "workspace" not in data:
			raise RuntimeError(f'missing "workspace" in {SettingsFileName}')

		self.workspace	= data.get('workspace')

def get_PerUserSettings():
	global PerUserSettings_instance
	if not PerUserSettings_instance or PerUserSettings_instance._curFile != jx.file.currentBlenderFilename():
		PerUserSettings_instance = PerUserSettings()

	if PerUserSettings_instance.workspace is None:
		return None
	
	return PerUserSettings_instance

def runP4cmd(*args):
	settings = get_PerUserSettings()
	if settings is None:
		return

	cmd = ['p4','-c', settings.workspace]
	for a in args:
		cmd.append(a)

	env = os.environ.copy()
	env["P4CHARSET"] = "utf8"  # Force UTF-8 for this subprocess

	print(f'runP4cmd {cmd}')

	subprocess.run(
		cmd,
		text=True,
		encoding='utf-8',
		shell=True,
		env=env,
		check=True
	)
	
def checkout(filename):
	runP4cmd('edit', filename)

def checkoutCurrentFile():
	checkout(jx.file.currentBlenderFilename())
