import bpy

def alertBox(layout, text):
	col = layout.box().column()
	col.alert = True
	col.label(text=text, icon="ERROR")
