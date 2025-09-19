import bpy
import jx.util

g_subTrackNameDelimit = '++'

def getEditingTrack():
	rig = bpy.context.active_object
	if not rig: return None

	animData = rig.animation_data
	if not animData: return None
	# if not animData.use_tweak_mode: return None

	activeTrack = animData.nla_tracks.active
	return activeTrack

def getActiveTrack(rig):
	if not rig: return None
	return rig.animation_data.nla_tracks.active

def getActiveParentTrack(rig):
	activeTrack = getActiveTrack(rig)
	if not activeTrack: return None

	parentTrackName = getParentTrackName(activeTrack.name)
	parentTrack = rig.animation_data.nla_tracks.get(parentTrackName)
	return parentTrack

def getActiveSubTrack(rig):
	activeTrack = getActiveTrack(rig)
	if not activeTrack: return None
	if not getSubTrackNameSuffix(activeTrack.name):
		return None
	return activeTrack

def getSceneGlobalTrackAction(rig):
	if not rig or rig.type != 'ARMATURE': return None
	animData = rig.animation_data
	if not animData: return

	if animData.use_tweak_mode:
		return animData.action_tweak_storage
	else:
		return animData.action
	

def setActiveTrackByName(rig, trackName):
	if not rig: return None

	subTrackPrefix = f"{trackName}{g_subTrackNameDelimit}"
	targetTrack = None

	for track in rig.animation_data.nla_tracks:
		track.is_solo = False
		track.mute = True
		track.select = False
		
		for strip in track.strips:
			strip.select = False # deselect all strips
		
		if track.name == trackName:
			targetTrack = track

		if track.name == trackName or track.name.startswith(subTrackPrefix):
			track.mute = False
			track.select = True

	jx.anim.rig.resetAllBonesTransforms(rig)

	rig.animation_data.nla_tracks.active = targetTrack

	if not targetTrack: return

	frame_start, frame_end = getTrackFrameRange(targetTrack)
	bpy.context.scene.frame_start = int(frame_start)
	bpy.context.scene.frame_end   = int(frame_end)

	stripsIndex = 0
	for s in targetTrack.strips:
		b = stripsIndex == 0
		s.select = b
		stripsIndex += 1

def getSelectedTracks(rig):
	o = []
	for track in rig.animation_data.nla_tracks:
		if track.select: o.append(track)

	return o

def deselectAllTracks(rig):
	for track in rig.animation_data.nla_tracks:
		for strip in track.strips:
			strip.select = False
		track.select = False
		track.is_solo = False
		track.mute = True

	rig.animation_data.nla_tracks.active = None

def getTrackFrameRange(track):
	frame_start = 0
	frame_end   = 0
	for strip in track.strips:
		if strip.frame_start < frame_start:
			frame_start = strip.frame_start
		if strip.frame_end > frame_end:
			frame_end = strip.frame_end
	
	return (frame_start, frame_end)

def getParentTrackName(name):
	if g_subTrackNameDelimit not in name:
		return name
	firstPart = name.split(g_subTrackNameDelimit, 1)[0]
	return firstPart

def getSubTrackNameSuffix(name):
	if g_subTrackNameDelimit not in name:
		return None
	secondPart = name.split(g_subTrackNameDelimit, 1)[1]
	return secondPart

def renameTrackStripsToTrackName(track):
	if not track: return
	idx = 0
	for strip in track.strips:
		if idx == 0:
			strip.name = track.name
		else:
			strip.name = f"{track.name}.{idx:03d}"
		idx += 1

def renameTrack(rig, track, newName):
	if not track:
		raise RuntimeError("No track selected")
	
	if "." in newName:
		raise RuntimeError("new name '{newName}' should not contains dot '.' ")

	oldSubTrackNamePrefix = f"{track.name}{g_subTrackNameDelimit}"
	newSubTrackNamePrefix = f"{newName}{g_subTrackNameDelimit}"

	track.name = newName
	renameTrackStripsToTrackName(track)

	# rename sub tracks too
	for subTrack in rig.animation_data.nla_tracks:
		if subTrack.name.startswith(oldSubTrackNamePrefix):
			suffix = getSubTrackNameSuffix(subTrack.name)
			subTrack.name =  newSubTrackNamePrefix + suffix
			renameTrackStripsToTrackName(subTrack)

def createNewTrack(rig, newTrackName, prevTrack=None, actionToAdd=None):
	if not rig or rig.type != 'ARMATURE':
		raise RuntimeError('rig is null')

	newTrackName = newTrackName.strip()
	if not newTrackName or len(newTrackName) <= 0:
		return

	if jx.anim.rig.hasTrack(rig, newTrackName):
		raise RuntimeError(f'Cannot create new track with duplicate name {newTrackName}')

	animData = rig.animation_data
	if not animData:
		raise RuntimeError(f'Armature has no animation data')
	
	newTrack = animData.nla_tracks.new(prev=prevTrack)
	newTrack.name = newTrackName

	if actionToAdd:
		print(f"actionToAdd {actionToAdd} id_root = {actionToAdd.id_root}")

	if not actionToAdd:
		actionToAdd = bpy.data.actions.new(name=newTrack.name)
		actionToAdd.id_root = "OBJECT"

		# rootMotionBoneName = jx.anim.rigify.g_rootMotionBoneName
		# rootMotionBone = rig.pose.bones.get(rootMotionBoneName)
		# if rootMotionBone:
			# curve = actionToAdd.fcurves.new(data_path=f'pose.bones["{rootMotionBoneName}"].location', index=0, action_group=rootMotionBoneName)
			# curve.keyframe_points.insert(bpy.context.scene.frame_start, 0)
			# curve.keyframe_points.insert(bpy.context.scene.frame_end,   0)

	newStrip = newTrack.strips.new(name=newTrack.name, start=0, action=actionToAdd)
	newStrip.blend_type = 'COMBINE'

	sortTracksByName()
	return newTrack

def enterEditTrackMode(rig, trackName):
	if not rig or rig.type != 'ARMATURE': return
	
	animData = rig.animation_data
	animData.use_tweak_mode = False
	setActiveTrackByName(rig, trackName)
	animData.use_tweak_mode = True

	bpy.ops.object.mode_set(mode='POSE')
	jx.anim.evaluateAnimation()

def exitEditTrackMode(rig):
	if not rig or rig.type != 'ARMATURE': return
	rig.animation_data.use_tweak_mode = False

class OP_NlaNewSubTrack(jx.types.Operator):
	bl_idname = "nla.jx_new_sub_track"
	bl_label = "New Sub Track"
	bl_options = {"REGISTER", "UNDO"}

	newStripActionName : bpy.props.StringProperty()

	def doExecute(self, context):
		rig = bpy.context.view_layer.objects.active
		if not rig or rig.type != 'ARMATURE':
			raise RuntimeError("No Rig selected")

		parentTrack = getActiveParentTrack(rig)
		if not parentTrack:
			raise RuntimeError("Error get parent track")

		newSubTrackName = None
		index = 1
		while True:
			newSubTrackName = f'{parentTrack.name}{g_subTrackNameDelimit}{index:03d}'
			if jx.anim.rig.hasTrack(rig, newSubTrackName):
				index += 1
				continue
			break

		if not newSubTrackName:
			raise RuntimeError("Error generate sub track name")

		newStripAction = None
		if self.newStripActionName != "":
			newStripAction = bpy.data.actions.get(self.newStripActionName)

		newSubTrack = createNewTrack(rig, newSubTrackName, prevTrack=parentTrack, actionToAdd=newStripAction)
		newSubTrackName = newSubTrack.name

		enterEditTrackMode(rig, newSubTrackName)
		#bpy.ops.anim.channels_move(direction='DOWN')

	def execute(self, context):
		if self.doExecute(context):
			return {'CANCELLED'}
		return {'FINISHED'}

	def invoke(self, context, event):
		self.newStripAction = ""
		return context.window_manager.invoke_props_dialog(self)

	def draw(self, context):
		self.layout.label(text="Select Action (Empty: Create New)")
		self.layout.prop_search(self, "newStripActionName", bpy.data, "actions", text="")

def getSingleSelectedStrip():
	s = bpy.context.selected_nla_strips
	if len(s) != 1: return None
	return s[0]


def isMuteRootMotion(rig):
	if not rig or rig.type != 'ARMATURE': return False
	action = rig.animation_data.action
	if not action: return False
	
	for group in action.groups:
		if group.name == "JX-RootMotion":
			return group.mute
	return False

def muteActionRootMotion(action, isMute: bool):
	if not action: return
	for group in action.groups:
		if group.name == "JX-RootMotion":
			group.mute = isMute
			break

def muteTrackRootMotion(track, isMute: bool):
	if not track: return
	for strip in track.strips:
		if not strip: continue
		muteActionRootMotion(strip.action, isMute)

def muteRootMotion(rig, isMute: bool):
	if not rig or rig.type != 'ARMATURE':
		return

	parentTrack = jx.anim.nla.getActiveParentTrack(rig)
	if parentTrack:
		for track in rig.animation_data.nla_tracks:
			if parentTrack.name == jx.anim.nla.getParentTrackName(track.name):
				muteTrackRootMotion(track, isMute)

	if isMute:
		for poseBone in rig.pose.bones:
			if poseBone.name == "JX-RootMotion":
				poseBone.location = (0,0,0)
				poseBone.rotation_euler = (0,0,0)
				poseBone.rotation_quaternion = (1,0,0,0)
				poseBone.scale = (1,1,1)
				break

	jx.anim.evaluateAnimation()

class OP_MuteRootMotion(jx.types.Operator):
	bl_idname = 'graph.jx_anim_graph_mute_root_motion'
	bl_label = 'Mute Root Motion'
	bl_options = {"REGISTER", "UNDO"}

	isMute : bpy.props.BoolProperty()

	def execute(self, context):
		rig = bpy.context.view_layer.objects.active
		muteRootMotion(rig, self.isMute)
		return {'FINISHED'}

class OP_ResetAllBonesTransform(jx.types.Operator):
	bl_idname = 'armature.jx_rig_reset_all_bones_transform'
	bl_label = 'Reset All Bones'
	bl_options = {"REGISTER", "UNDO"}

	def execute(self, context):
		jx.anim.rig.resetAllBonesTransforms(bpy.context.view_layer.objects.active)
		return {'FINISHED'}

class OP_NlaRenameTrack(jx.types.Operator):
	bl_idname = "nla.jx_rename_track"
	bl_label = "Rename Track"
	bl_options = {"REGISTER", "UNDO"}

	newName : bpy.props.StringProperty(name="New Name")

	def execute(self, context):
		if not self.doExecute(context):
			return {'CANCELLED'}
		return {'FINISHED'}

	def doExecute(self, context):
		rig = bpy.context.view_layer.objects.active
		if not rig or rig.type != 'ARMATURE':
			raise RuntimeError("No Rig selected")

		track = getActiveParentTrack(rig)

		if track.name != self.newName: # same track, but rename strips
			if jx.anim.rig.hasTrack(rig, self.newName):
				raise RuntimeError("Duplicated Track Name")

		renameTrack(rig, track, self.newName)
		return True
	
	def invoke(self, context, event):
		rig = bpy.context.view_layer.objects.active
		if not rig or rig.type != 'ARMATURE':
			return None

		track = getActiveParentTrack(rig)
		if not track:
			return None
		
		self.newName = track.name
		return context.window_manager.invoke_props_dialog(self)
	
	def draw(self, context):
		self.layout.activate_init = True # set textbox input focus
		self.layout.label(text="All Strips name will be CHANGED too", icon="INFO")
		self.layout.prop(self, "newName")
		self.layout.separator()

class OP_NlaRenameSubTrack(jx.types.Operator):
	bl_idname = "nla.jx_rename_sub_track"
	bl_label = "Rename Sub Track"
	bl_options = {"REGISTER", "UNDO"}

	newName : bpy.props.StringProperty(name="New Name")

	def execute(self, context):
		if not self.doExecute(context):
			return {'CANCELLED'}
		return {'FINISHED'}

	def doExecute(self, context):
		rig = bpy.context.view_layer.objects.active
		if not rig or rig.type != 'ARMATURE':
			raise RuntimeError("No Rig selected")

		track = getActiveTrack(rig)
		if not track:
			raise RuntimeError("No active sub track")

		subTrackSuffix = getSubTrackNameSuffix(track.name)
		if not subTrackSuffix:
			raise RuntimeError("active track is not sub track")

		parentTrackName = getParentTrackName(track.name)
		newTrackName = f"{parentTrackName}{g_subTrackNameDelimit}{self.newName}"

		if track.name != newTrackName: # same track, but rename strips
			if jx.anim.rig.hasTrack(rig, newTrackName):
				raise RuntimeError("Duplicated Track Name")

		renameTrack(rig, track, newTrackName)
		return True
	
	def invoke(self, context, event):
		rig = bpy.context.view_layer.objects.active
		if not rig or rig.type != 'ARMATURE':
			return None

		track = getActiveTrack(rig)
		if not track: return None
		
		subTrackSuffix = getSubTrackNameSuffix(track.name)
		if not subTrackSuffix: return None

		self.newName = subTrackSuffix
		return context.window_manager.invoke_props_dialog(self)
	
	def draw(self, context):
		self.layout.activate_init = True # set textbox input focus
		self.layout.label(text="All Strips name will be CHANGED too", icon="INFO")
		self.layout.prop(self, "newName")
		self.layout.separator()

class OP_NlaRenameStripAction(jx.types.Operator):
	bl_idname = "nla.jx_rename_strip_action"
	bl_label = "Rename Strip Action"
	bl_options = {"REGISTER", "UNDO"}

	newName : bpy.props.StringProperty(name="New Name")
	actionName : bpy.props.StringProperty(name="Action Name")
	
	def execute(self, context):
		if not self.doExecute(context):
			return {'CANCELLED'}
		return {'FINISHED'}

	def doExecute(self, context):
		action = bpy.data.actions.get(self.actionName)
		if not action: return False

		action.name = self.newName
		return True

	def invoke(self, context, event):
		strip = getSingleSelectedStrip()
		if not strip: return False
		if not strip.action: return False
		self.actionName = strip.action.name
		self.newName = self.actionName
		return context.window_manager.invoke_props_dialog(self)
	
	def draw(self, context):
		self.layout.activate_init = True # set textbox input focus
		self.layout.prop(self, "newName")

# def getTestTrackList(self, context):
# 	items = [("<None>", "<None>", "")]
# 	for track in context.object.animation_data.nla_tracks:
# 		t = track.name
# 		if g_subTrackNameDelimit in t: continue
# 		items.append((t, t, ""))
# 	return items

# class OP_NlaTrackSelectTest(jx.types.Operator):
# 	bl_idname = "object.search_enum_operator"
# 	bl_label = "Search Enum Operator"
#	bl_options = {"REGISTER", "UNDO"}
# 	bl_property = "my_search"

# 	my_search: bpy.props.EnumProperty(items=getTeestTrackList)

# 	def execute(self, context):
# 		self.report({'INFO'}, "Selected:" + self.my_search)
# 		return {'FINISHED'}


# 	def invoke(self, context, event):
# 		context.window_manager.invoke_search_popup(self)
# 		return {'RUNNING_MODAL'}

class OP_NlaTrackMenuSelected(jx.types.Operator):
	bl_idname = "nla.jx_track_menu_selected"
	bl_label = "NLA Track Selected"
	bl_options = {"REGISTER", "UNDO"}

	trackName : bpy.props.StringProperty()

	def execute(self, context):
		rig = context.object
		if not rig or rig.type != 'ARMATURE':
			return

		if self.trackName == "":
			exitEditTrackMode(rig)
			deselectAllTracks(rig)
			jx.anim.rig.resetAllBonesTransforms(rig)
			return {'FINISHED'}
		
		enterEditTrackMode(rig, self.trackName)
		return {'FINISHED'}
	
class OP_NlaNewTrack(jx.types.Operator):
	bl_idname = "nla.jx_new_track"
	bl_label = "New Track"
	bl_options = {"REGISTER", "UNDO"}

	newName : bpy.props.StringProperty(name="New Name")
	
	def execute(self, context):
		self.newName = self.newName.strip()
		if len(self.newName) <= 0:
			return {'CANCELLED'}

		rig = bpy.context.view_layer.objects.active
		if not rig or rig.type != 'ARMATURE':
			self.report({'ERROR'}, "No Rig selected")
			return {'CANCELLED'}

		if jx.anim.rig.hasTrack(rig, self.newName):
			self.report({'ERROR'}, "Duplicated Track Name")
			return {'CANCELLED'}

		createNewTrack(rig, self.newName)
		enterEditTrackMode(rig, self.newName)
		return {'FINISHED'}
	
	def invoke(self, context, event):
		self.newName = ""
		rig = bpy.context.view_layer.objects.active
		if not rig or rig.type != 'ARMATURE':
			return None

		return context.window_manager.invoke_props_dialog(self)
	
	def draw(self, context):
		self.layout.activate_init = True # set textbox input focus
		self.layout.prop(self, "newName")

class JX_MT_NlaTrackMenu(jx.types.Menu):
	bl_idname = "JX_MT_NlaTrackMenu"
	bl_label = "Select Edit Track"
	bl_options = {"SEARCH_ON_KEY_PRESS"}
	
	def draw(self, context):
		self.layout.operator(OP_NlaTrackMenuSelected.bl_idname, text="<No Track>").trackName = ""
		self.layout.separator()

		animData = context.object.animation_data
		if not animData: return
		
		tracks = animData.nla_tracks
		for track in reversed(tracks):
			if g_subTrackNameDelimit in track.name: continue
			self.layout.operator(OP_NlaTrackMenuSelected.bl_idname, text=track.name).trackName = track.name

class JX_MT_NlaSubTrackMenu(jx.types.Menu):
	bl_idname = "JX_MT_NlaSubTrackMenu"
	bl_label = "Select Edit SubTrack"
	bl_options = {"SEARCH_ON_KEY_PRESS"}
	
	def draw(self, context):
		parentTrackName = "<No SubTrack>"
		editTrack = getEditingTrack()
		if editTrack:
			parentTrackName = getParentTrackName(editTrack.name)

		op = OP_NlaTrackMenuSelected

		self.layout.operator(op.bl_idname, text="<No SubTrack>").trackName = parentTrackName
		self.layout.separator()

		animData = context.object.animation_data
		if not animData: return
		
		prefix = f'{parentTrackName}{g_subTrackNameDelimit}'

		tracks = animData.nla_tracks
		for subTrack in reversed(tracks):
			if subTrack.name.startswith(prefix):
				suffix = getSubTrackNameSuffix(subTrack.name)
				self.layout.operator(op.bl_idname, text=suffix).trackName = subTrack.name

def sortTracksByName():
	rig = bpy.context.object
	if not rig or not rig.type == 'ARMATURE':
		return False
	
	animData = rig.animation_data
	if not animData: return False

	tracks = animData.nla_tracks.values()

	for t in tracks:
		t.select = False

	# bubble sort
	n = len(tracks)
	for j in range(n):
		for i in range(1, n - j):
			a = tracks[i-1]
			b = tracks[i]
			if a.name < b.name:
				# swap tracks
				tracks[i-1], tracks[i] = b, a
				b.select = True
				bpy.ops.anim.channels_move(direction='DOWN')
				b.select = False

	return True

class OP_NlaSortTracksByName(jx.types.Operator):
	bl_idname = 'nla.jx_sort_track_by_name'
	bl_label = 'Sort Tracks by Name'
	bl_options = {"REGISTER", "UNDO"}

	def execute(self, context):
		sortTracksByName()
		return {'FINISHED'}

class OP_NlaExitTweakMode(jx.types.Operator):
	bl_idname = 'nla.jx_exit_tweak_mode'
	bl_label = 'Exit Tweak Mode'
	bl_options = {"REGISTER", "UNDO"}

	def execute(self, context):
		if self.doExecute(context):
			return {'CANCELLED'}
		return {'FINISHED'}
	
	def doExecute(self, context):
		rig = context.object
		if not rig or not rig.type == 'ARMATURE':
			return False
		if not rig.animation_data:
			return False
		rig.animation_data.use_tweak_mode = False
		return True

class NlaPanel(jx.types.Panel):
	bl_idname = "JX_PT_NLA_PANEL"
	bl_label = "(JX) NLA"
	bl_order = 4000
	bl_space_type = "NLA_EDITOR"
	bl_region_type = "UI"
	bl_category = "JxBlender"

	def draw(self, context):
		rig = context.object
		if not rig or not rig.type == 'ARMATURE':
			self.layout.box().label(text="<No Armature Selected>")
			return
		
		animData = rig.animation_data
		if not animData: return

		sceneGlobalAction = getSceneGlobalTrackAction(rig)
		if sceneGlobalAction:
			n = len(sceneGlobalAction.fcurves)
			if n > 0:
				jx.ui.alertBox(self.layout, text=f"Scene or ActionEditor contains {n} curves")

		activeParentTrackName = "<No Track>"
		activeSubTrackSuffix  = "<No SubTrack>"
		activeTrackName = ""

		activeTrack = getEditingTrack()
		if activeTrack:
			activeTrackName = activeTrack.name
			activeParentTrackName = getParentTrackName(activeTrack.name)
			subTrackNamePrefix = f"{activeParentTrackName}{g_subTrackNameDelimit}"
			# only show sub track for this parent track
			if activeTrack.name.startswith(subTrackNamePrefix):
				activeSubTrackSuffix = getSubTrackNameSuffix(activeTrack.name)

		col = self.layout.column(align=True)

		isMute = isMuteRootMotion(rig)

		row = col.row(align=True)
		row.operator(OP_MuteRootMotion.bl_idname, text='Mute Root', depress=isMute).isMute = not isMute
		row.operator(OP_ResetAllBonesTransform.bl_idname)

		col.separator()

		row = col.row(align=True)
		col.operator(OP_NlaSortTracksByName.bl_idname)
		col.operator(OP_NlaTrackMenuSelected.bl_idname, text='Deselect All Tracks').trackName = ""

		col.separator()
		col.label(text="Selected Track:")
		col.menu(JX_MT_NlaTrackMenu.bl_idname, text=activeParentTrackName)

#		col.operator(OP_NlaTrackSelectTest.bl_idname)

		row = col.row(align=True).split(factor=0.5, align=True)

		if animData.use_tweak_mode and activeTrackName == activeParentTrackName:
			row.operator(OP_NlaExitTweakMode.bl_idname, text='Edit', depress = True)
		else:
			row.operator(OP_NlaTrackMenuSelected.bl_idname, text='Edit').trackName = activeParentTrackName

		row.operator(OP_NlaNewTrack.bl_idname, text='New')
		row.operator(OP_NlaRenameTrack.bl_idname, text='Rename')

		col.separator()
		col.label(text="Sub Track:")
		col.menu(JX_MT_NlaSubTrackMenu.bl_idname, text=activeSubTrackSuffix)

		row = col.row(align=True).split(factor=0.5, align=True)

		if animData.use_tweak_mode and activeTrackName != activeParentTrackName:
			row.operator(OP_NlaExitTweakMode.bl_idname, text='Edit', depress = True)
		else:
			row.operator(OP_NlaTrackMenuSelected.bl_idname, text='Edit').trackName = activeTrackName

		row.operator(OP_NlaNewSubTrack.bl_idname, text="New")
		row.operator(OP_NlaRenameSubTrack.bl_idname, text='Rename')

class NlaActiveStripPanel(jx.types.Panel):
	bl_idname = "JX_PT_NLA_ACTIVE_STRIP_PANEL"
	bl_label = "(JX) Active Strip"
	bl_order = 5000
	bl_space_type = "NLA_EDITOR"
	bl_region_type = "UI"
	bl_category = "JxBlender"

	def draw(self, context):
		strip = getSingleSelectedStrip()
		stripName = "----"
		if strip: stripName = strip.name

		col = self.layout.column(align=True)
		# col.use_property_split = True
		if not strip:
			col.label(text="<No Strip>")
		else:
			label_factor = 0.4

			# col.label(text="Selected Strip")
			col.prop(strip, "name", text="")
			col.separator()

			col.label(text="Action")

			row = col.row()
			if context.object and context.object.type == "ARMATURE":
				if context.object.animation_data:
					row.enabled = not context.object.animation_data.use_tweak_mode
			row.prop(strip, "action", text="")

			col.enabled = strip.action is not None
			col.operator(OP_NlaRenameStripAction.bl_idname, text="Rename")

			col.separator()

			row = col.row().split(factor=label_factor, align=True)
			row.alignment = "RIGHT"
			row.label(text="Influence")

			row2 = row.split(factor=0.25, align=True)
			row2.prop(strip, "use_animated_influence", text="")

			row3 = row2.row(align=True)
			row3.enabled = strip.use_animated_influence
			row3.prop(strip, "influence", text="")
			
			def drawItem(label, prop, prop_text=""):
				row = col.row().split(factor=label_factor, align=True)
				row.alignment = "RIGHT"
				row.label(text=label)
				row.prop(strip, prop, text=prop_text)

			drawItem("Extrapolation", "extrapolation")
			drawItem("Blending", "blend_type")
			drawItem("Blend In", "blend_in")
			drawItem("Out", "blend_out")
			drawItem("use_auto_blend", "use_auto_blend", "Auto Blend In/Out")
			col.separator()
			drawItem("Frame Start:", "action_frame_start")
			drawItem("End:", "action_frame_end")

			row = col.row().split(factor=label_factor, align=True)
			row.alignment = "RIGHT"
			row.label(text="Sync Length")
			row2 = row.split(factor=0.2, align=True)
			row2.prop(strip, "use_sync_length", text="")
			row2.operator(bpy.ops.nla.action_sync_length.idname(), text="Sync Now", icon="FILE_REFRESH")

			drawItem("Playback", "use_reverse", "Reversed")
			drawItem("", "use_animated_time_cyclic", "Cyclic Strip Time")
			drawItem("Scale", "scale")
			drawItem("Repeat", "repeat")

def on_app_handlers_load_post():
	# print("=========> NLA on_app_handlers_load_post new file loaded")
	rig = bpy.context.active_object
	if not rig: return

	# blender bug - crash when insert new keyframe, if the file saved with tweak_mode=True
	# because the active strip is not in tweak mode (the color is not green)
	# work around: re-enable tweak mode
	if not rig.animation_data: return
	rig.animation_data.use_tweak_mode = False
	rig.animation_data.use_tweak_mode = True
