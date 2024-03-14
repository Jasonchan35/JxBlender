# -*- coding: utf-8 -*-

bl_info = {
	"name": "jx",
	"author": "",
	"version": (0, 1, 1),
	"blender": (3, 0, 0),
	"description": "JxBlender",
	"warning": "",
	"doc_url": "",
	"wiki_url": "",
	"tracker_url": "",
	"category": "Import-Export",
	}

def print_info():
	info_name = bl_info["name"]
	info_ver  = bl_info["version"]
	print(f"\n\n====== Module: {info_name}, version:{info_ver} ======")
print_info()

import inspect
import os
import sys
import importlib
import bpy

import jx.types
import jx.util

from . import (
	debug,
	addon,
#----
	math,
	path,
	util,
	ui,
	file,
	json,
	types,
	custom_prop,
	project,
	selection,
	view3d,
#-----
	export,
	anim,
	main_menu,
)

def dump(obj):
	jx.debug.dump(obj)

sub_modules = []

def get_submodules(outList, module):
	for attr in dir(module):
		v = getattr(module, attr)
		if inspect.ismodule(v) and v.__name__.startswith("jx."):
			outList.append(v)
			get_submodules(outList, v)

get_submodules(sub_modules, sys.modules[__name__])

@bpy.app.handlers.persistent
def load_post_handler(dummy):
	for m in sub_modules:
		if hasattr(m, 'on_app_handlers_load_post'):
			m.on_app_handlers_load_post()

def register():
	bpy.app.handlers.load_post.append(load_post_handler)

	for m in sub_modules:
		# print(f"jx: register module {m.__name__}")
		if m != addon: # reload.py is exceptional case
			importlib.reload(m)

		if m == types: continue

		addon.register_classes_in_module(m, bpy.types.Operator)
		addon.register_classes_in_module(m, bpy.types.Panel)
		addon.register_classes_in_module(m, bpy.types.Menu)
		addon.register_classes_in_module(m, bpy.types.PropertyGroup)
		addon.register_classes_in_module(m, bpy.types.UIList)
	main_menu.register()

	bpy.types.Object.jx_retarget_settings = bpy.props.PointerProperty(type=jx.anim.retarget.Settings)

def unregister():
	del bpy.types.Object.jx_retarget_settings

	addon.unregister_all_classes()
	main_menu.unregister()

# This allows you to run the script directly from Blender's Text editor
# to test the add-on without having to install it.
if __name__ == "__main__":
	register()