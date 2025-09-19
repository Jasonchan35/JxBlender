import bpy
import jx.util

from mathutils import Vector
from mathutils import Matrix

def copyKeyframeValueAndHandle(dst, src):
	deltaX = dst.co.x - src.co.x
	deltaVec = Vector((deltaX, 0))

	dst.co.y 				= src.co.y
	dst.easing 				= src.easing
	dst.handle_left 		= src.handle_left  + deltaVec

	dst.handle_left_type 	= src.handle_left_type
	dst.handle_right 		= src.handle_right + deltaVec
	dst.handle_right_type 	= src.handle_right_type
	dst.interpolation		= src.interpolation

def copyFirstKeyToLast(curve):
	n = len(curve.keyframe_points)
	if n < 2: return
	print("copyFirstKeyToLast")
	copyKeyframeValueAndHandle(curve.keyframe_points[n-1], curve.keyframe_points[0])

def copyLastKeyToFirst(curve):
	n = len(curve.keyframe_points)
	if n < 2: return
	print("copyLastKeyToFirst")
	copyKeyframeValueAndHandle(curve.keyframe_points[0], curve.keyframe_points[n-1])

def findCurveModifierByType(curve, modifierTypeName):
	for m in curve.modifiers:
		if m.type == modifierTypeName:
			return m
	return None

def findOrAddCurveModifierByType(curve, modifierTypeName):
	m = findCurveModifierByType(curve, modifierTypeName)
	if not m:
		m = curve.modifiers.new(modifierTypeName)
	return m

def removeCurveModifierByType(curve, modifierTypeName):
	m = findCurveModifierByType(curve, modifierTypeName)
	if m:
		curve.modifiers.remove(m)

class OP_InsertKeyframe(jx.types.Operator):
	bl_idname = 'graph.jx_insert_keyframe'
	bl_label = 'Insert Key'
	bl_options = {"REGISTER", "UNDO"}

	inDataPath : bpy.props.StringProperty()

	def execute(self, context):
		self.doExecute(context)
		return {'FINISHED'}

	def insertKeyToSelectedCurves(self):
		for curve in bpy.context.selected_editable_fcurves:
			frame = bpy.context.scene.frame_current
			value = curve.evaluate(frame)
			curve.keyframe_points.insert(frame, value, options={"NEEDED"})

	def insertKeyToSelectedPoseBones(self):
		for poseBone in bpy.context.selected_pose_bones:
			data_path = self.inDataPath
			if data_path == "rotation":
				if poseBone.rotation_mode == "QUATERNION":
					data_path = "rotation_quaternion"
				elif poseBone.rotation_mode == "AXIS_ANGLE":
					data_path = "rotation_axis_angle"
				else:
					data_path = "rotation_euler"
			poseBone.keyframe_insert(data_path=data_path, group=poseBone.name)

	def doExecute(self, context):
		if self.inDataPath == "<SELECTED>":
			self.insertKeyToSelectedCurves()
		elif bpy.context.mode == 'POSE':
			self.insertKeyToSelectedPoseBones()
		return True

class OP_StepFrame(jx.types.Operator):
	bl_idname = 'graph.jx_anim_step_frame'
	bl_label = 'Step Frame'
	bl_options = {"REGISTER", "UNDO"}

	inStep : bpy.props.FloatProperty()

	def execute(self, context):
		f = bpy.context.scene.frame_current_final + self.inStep
		# f = round(f * 10) / 10
		jx.anim.frame_set_float(f)
		return {'FINISHED'}

class OP_SetHandleType(jx.types.Operator):
	bl_idname = 'graph.jx_anim_set_handle_type'
	bl_label = 'SetKeyframeEasingType'
	bl_options = {"REGISTER", "UNDO"}

	inType : bpy.props.StringProperty()

	@classmethod
	def poll(cls, context):
		if len(bpy.context.selected_editable_keyframes) <= 0:
			return False
		return True
	
	def execute(self, context):
		if not self.doExecute(context):
			return {'CANCELLED'}
		return {'FINISHED'}
	
	def doExecute(self, context):
		interpolation = None
		easing = None
		handle_type = None

		tokens = self.inType.split("-")
		interpolation = tokens[0]

		if interpolation == "CONSTANT":
			pass
		elif interpolation == "LINEAR":
			pass

		elif interpolation == "BEZIER":
			handle_type = tokens[1]

		elif interpolation == "SINE":
			easing = tokens[1]
		elif interpolation == "QUAD":
			easing = tokens[1]
		elif interpolation == "CUBIC":
			easing = tokens[1]
		elif interpolation == "QUART":
			easing = tokens[1]
		elif interpolation == "QUINT":
			easing = tokens[1]
		elif interpolation == "EXPO":
			easing = tokens[1]
		elif interpolation == "CIRC":
			easing = tokens[1]

		for keyframe in bpy.context.selected_editable_keyframes:
			if interpolation:
				keyframe.interpolation = interpolation
			if easing:
				keyframe.easing = easing
			if handle_type:
				keyframe.handle_left_type = handle_type
				keyframe.handle_right_type = handle_type

		for fcurve in bpy.context.selected_editable_fcurves:
			fcurve.keyframe_points.handles_recalc()

		return True

class OP_SetChannelExtrapolation(jx.types.Operator):
	bl_idname = 'graph._jx_anim_set_channel_extrapolation'
	bl_label = 'SetChannelExtrapolation'
	bl_options = {"REGISTER", "UNDO"}

	inType : bpy.props.StringProperty()

	@classmethod
	def poll(cls, context):
		if len(bpy.context.selected_editable_fcurves) <= 0:
			return False
		return True

	def execute(self, context):
		if not self.doExecute(context):
			return {'CANCELLED'}
		return {'FINISHED'}
	
	def addCycleModifier(self, curve, mode):
		m = findOrAddCurveModifierByType(curve, "CYCLES")
		m.mode_before = mode
		m.mode_after  = mode
		m.cycles_before = 0 # 0 = infinite
		m.cycles_after  = 0 # 0 = infinite

	def doExecute(self, context):
		for curve in bpy.context.selected_editable_fcurves:
			if self.inType == "CONSTANT" or self.inType == "LINEAR":
				curve.extrapolation = self.inType
				removeCurveModifierByType(curve, "CYCLES")
			elif self.inType == "CYCLIC":
				self.addCycleModifier(curve, "REPEAT")
			elif self.inType == "CYCLIC_OFFSET":
				self.addCycleModifier(curve, "REPEAT_OFFSET")
			elif self.inType == "CYCLIC_MIRROR":
				self.addCycleModifier(curve, "MIRROR")
		return True

class OP_CopyFirstKeyframeToLast(jx.types.Operator):
	bl_idname = 'graph.jx_anim_copy_first_keyframe_to_last'
	bl_label = 'Copy First Key To Last'
	bl_options = {"REGISTER", "UNDO"}

	lastKeyToFirst : bpy.props.BoolProperty(default=False)

	@classmethod
	def poll(cls, context):
		if len(bpy.context.selected_editable_fcurves) <= 0:
			return False
		return True

	def execute(self, context):
		if not self.doExecute(context):
			return {'CANCELLED'}
		return {'FINISHED'}
	
	def doExecute(self, context):
		for curve in bpy.context.selected_editable_fcurves:
			if self.lastKeyToFirst:
				copyLastKeyToFirst(curve)
			else:
				copyFirstKeyToLast(curve)
		return True

class OP_MoveKeyframes(jx.types.Operator):
	bl_idname = 'graph.jx_anim_move_key'
	bl_label = 'Move Keyframes'
	bl_options = {"REGISTER", "UNDO"}

	inType : bpy.props.StringProperty()

	@classmethod
	def poll(cls, context):
		if len(bpy.context.selected_editable_fcurves) <= 0:
			return False
		return True

	def execute(self, context):
		if not self.doExecute(context):
			return {'CANCELLED'}
		return {'FINISHED'}

	def moveKeyframe(self, kf, offset):
		kf.co.x += offset
		kf.handle_left.x += offset
		kf.handle_right.x += offset

	def moveSelectedKeyframes(self, offset : float):
		for kf in  bpy.context.selected_editable_keyframes:
			self.moveKeyframe(kf, offset)

		for curve in bpy.context.selected_editable_fcurves:
			curve.keyframe_points.sort()
			curve.keyframe_points.deduplicate()
			curve.update()

	def moveHalfCycle(self):
		frame_start = bpy.context.scene.frame_start
		frame_end   = bpy.context.scene.frame_end
		frame_range = frame_end - frame_start

		for curve in bpy.context.selected_editable_fcurves:
			copyFirstKeyToLast(curve)

			for kf in curve.keyframe_points:
				self.moveKeyframe(kf, -frame_range / 2)

			value = curve.evaluate(frame_start)
			curve.keyframe_points.insert(frame_start, value, options={"NEEDED"})
			curve.keyframe_points.insert(frame_end,   value, options={"NEEDED"})

			print(len(curve.keyframe_points))

			for kf in curve.keyframe_points:
				if kf.co.x < frame_start:
					self.moveKeyframe(kf, frame_range)

			curve.keyframe_points.sort()
			curve.keyframe_points.deduplicate()

			copyFirstKeyToLast(curve)
			curve.update()

	def doExecute(self, context):
		if self.inType == "-1": self.moveSelectedKeyframes(-1)
		if self.inType == "+1": self.moveSelectedKeyframes(1)
		if self.inType == "WRAP_HALF_CYCLE": self.moveHalfCycle()

		return True


class OP_ShowCurves(jx.types.Operator):
	bl_idname = 'graph.jx_anim_show_curves'
	bl_label = 'Show Curves'

	inType : bpy.props.StringProperty()

	def execute(self, context):
		# old_selected_fcurves = context.selected_editable_fcurves
		self.doExecute(context)
		# restore selection
		# for c in context.selected_editable_fcurves:
		# 	c.select = False
		# for c in old_selected_fcurves:
		# 	c.select = True
		return {'FINISHED'}

	def doExecute(self, context):
		if self.inType == "ALL":
			bpy.ops.graph.reveal()
			return True

		if self.inType == "SELECTED":
			for curve in context.visible_fcurves:
				curve.hide = not curve.select
			return True

		if self.inType.startswith("LOCATION"):
			bpy.ops.graph.reveal()
			for curve in context.visible_fcurves:
				if curve.data_path.endswith(".location"):
					if self.inType == "LOCATION": continue
					if self.inType == "LOCATION.X" and curve.array_index == 0: continue
					if self.inType == "LOCATION.Y" and curve.array_index == 1: continue
					if self.inType == "LOCATION.Z" and curve.array_index == 2: continue
				curve.hide = True
			return True

		if self.inType.startswith("ROTATION"):
			bpy.ops.graph.reveal()
			for curve in context.visible_fcurves:
				if curve.data_path.endswith(".rotation_quaternion") \
				or curve.data_path.endswith(".rotation_axis_angle"):
					if self.inType == "ROTATION": continue
					if self.inType == "ROTATION.W" and curve.array_index == 0: continue
					if self.inType == "ROTATION.X" and curve.array_index == 1: continue
					if self.inType == "ROTATION.Y" and curve.array_index == 2: continue
					if self.inType == "ROTATION.Z" and curve.array_index == 3: continue

				if curve.data_path.endswith(".rotation_euler"):
					if self.inType == "ROTATION": continue
					if self.inType == "ROTATION.X" and curve.array_index == 0: continue
					if self.inType == "ROTATION.Y" and curve.array_index == 1: continue
					if self.inType == "ROTATION.Z" and curve.array_index == 2: continue

				curve.hide = True
			return True

		if self.inType.startswith("SCALE"):
			bpy.ops.graph.reveal()
			for curve in context.visible_fcurves:
				if curve.data_path.endswith(".scale"):
					if self.inType == "SCALE": continue
					if self.inType == "SCALE.X" and curve.array_index == 0: continue
					if self.inType == "SCALE.Y" and curve.array_index == 1: continue
					if self.inType == "SCALE.Z" and curve.array_index == 2: continue
				curve.hide = True
			return True

		raise RuntimeError(f"Unknow inType {self.inType}")
		return False

class AnimGraphEditorShowChannelsPanel(jx.types.Panel):
	bl_idname = "JX_PT_ANIM_GRAPH_EDITOR_SHOW_CHANNEL_PANEL"
	bl_label = "(JX) Show Channels"
	bl_order = 1000
	bl_space_type = "GRAPH_EDITOR"
	bl_region_type = "UI"
	bl_category = "JxBlender"

	def draw(self, context):
		col = self.layout.column(align=True)
		row = col.row(align=True)

		row2 = row.row(align=True)
		row2.operator(OP_InsertKeyframe.bl_idname, text="", icon="ADD").inDataPath = "<SELECTED>"
		row2.operator(OP_ShowCurves.bl_idname, text="Selected").inType = "SELECTED"
		row2.operator(OP_ShowCurves.bl_idname, text="All").inType = "ALL"

		row = col.row(align=True)
		row.operator(OP_InsertKeyframe.bl_idname, text="", icon="ADD").inDataPath = "location"
		
		row2 = row.split(factor=0.5, align=True)
		row2.operator(OP_ShowCurves.bl_idname, text="Loc").inType = "LOCATION"

		row3 = row2.row(align=True)
		row3.operator(OP_ShowCurves.bl_idname, text="X").inType = "LOCATION.X"
		row3.operator(OP_ShowCurves.bl_idname, text="Y").inType = "LOCATION.Y"
		row3.operator(OP_ShowCurves.bl_idname, text="Z").inType = "LOCATION.Z"
		row3.label(text="")

		row = col.row(align=True)
		row.operator(OP_InsertKeyframe.bl_idname, text="", icon="ADD").inDataPath = "rotation"

		row2 = row.split(factor=0.5, align=True)
		row2.operator(OP_ShowCurves.bl_idname, text="Rot").inType = "ROTATION"

		row3 = row2.row(align=True)
		row3.operator(OP_ShowCurves.bl_idname, text="X").inType = "ROTATION.X"
		row3.operator(OP_ShowCurves.bl_idname, text="Y").inType = "ROTATION.Y"
		row3.operator(OP_ShowCurves.bl_idname, text="Z").inType = "ROTATION.Z"
		row3.operator(OP_ShowCurves.bl_idname, text="W").inType = "ROTATION.W"

		row = col.row(align=True)
		row.operator(OP_InsertKeyframe.bl_idname, text="", icon="ADD").inDataPath = "scale"

		row2 = row.split(factor=0.5, align=True)
		row2.operator(OP_ShowCurves.bl_idname, text="Scale").inType = "SCALE"

		row3 = row2.row(align=True)
		row3.operator(OP_ShowCurves.bl_idname, text="X").inType = "SCALE.X"
		row3.operator(OP_ShowCurves.bl_idname, text="Y").inType = "SCALE.Y"
		row3.operator(OP_ShowCurves.bl_idname, text="Z").inType = "SCALE.Z"
		row3.label(text="")

		col.separator()
		row = col.row(align=True)
		row.operator("pose.paths_calculate", text="Motion Path")
		row.operator("object.paths_update_visible", text="Update")
		row.operator("pose.paths_clear", text="Clear")

		col.separator()
		row = col.split(factor=0.8, align=True)
		row.prop(bpy.context.scene, "frame_float")
		row2 = row.row(align=True)
		row2.operator(OP_StepFrame.bl_idname, text="<").inStep = -0.25
		row2.operator(OP_StepFrame.bl_idname, text=">").inStep =  0.25


class AnimGraphEditorKeyframePanel(jx.types.Panel):
	bl_idname = "JX_PT_ANIM_GRAPH_EDITOR_KEYFRAME_PANEL"
	bl_label = "(JX) Keyframe"
	bl_order = 2000
	bl_space_type = "GRAPH_EDITOR"
	bl_region_type = "UI"
	bl_category = "JxBlender"

	def draw(self, context):
		col = self.layout.column(align=True)
		singleKeyframe = None
		minValue = None
		maxValue = None

		minFrame = None
		maxFrame = None

		if len(context.selected_editable_keyframes) == 1:
			singleKeyframe = context.selected_editable_keyframes[0]
		else:
			for kf in context.selected_editable_keyframes:
				f = kf.co.x
				if minFrame is None or f < minFrame: minFrame = f
				if maxFrame is None or f > maxFrame: maxFrame = f
				v = kf.co.y
				if minValue is None or v < minValue: minValue = v
				if maxValue is None or v > maxValue: maxValue = v

		#---- Frame
		row = col.row(align=True).split(factor=0.2, align=True)
		row.label(text="Frame:")

		if singleKeyframe:
			row.prop(singleKeyframe, "co", index=0, text="")
		elif minFrame is not None and maxFrame is not None:
			if minFrame == maxFrame:
				row.label(text=f"{minFrame:.3f}")
			else:
				row = row.split(factor=0.5, align=True)
				row.label(text=f"Min: {minFrame:.3f}")
				row.label(text=f"Max: {maxFrame:.3f}")

		#---- Value
		row = col.row(align=True).split(factor=0.2, align=True)
		row.label(text="Value:")

		if singleKeyframe:
			row.prop(singleKeyframe, "co", index=1, text="")
		elif minValue is not None and maxValue is not None:
			if minValue == maxValue:
				row.label(text=f"{minValue:.3f}")
			else:
				row = row.split(factor=0.5, align=True)
				row.label(text=f"Min: {minValue:.3f}")
				row.label(text=f"Max: {maxValue:.3f}")

		#---- Buttons
		col.separator()

		row = col.row(align=True).split(factor=0.5, align=True)
		row2 = row.row(align=True)
		row2.alignment = "CENTER"
		row2.operator(OP_MoveKeyframes.bl_idname, text="<<").inType = "-1"
		row2.operator(OP_MoveKeyframes.bl_idname, text=">>").inType = "+1"
		row2.alignment = "EXPAND"

		row.operator(OP_MoveKeyframes.bl_idname, text="Wrap Half Cycle").inType = "WRAP_HALF_CYCLE"

		row = col.row(align=True)
		row2 = row.row(align=True)
		row2.operator(OP_CopyFirstKeyframeToLast.bl_idname, text="First Key to Last").lastKeyToFirst = False
		row2.operator(OP_CopyFirstKeyframeToLast.bl_idname, text="Last Key to First").lastKeyToFirst = True
		# self.layout.operator("graph.keyframe_insert", text="Insert New", icon='ADD').type="SEL"


class AnimGraphEditorHandleTypePanel(jx.types.Panel):
	bl_idname = "JX_PT_ANIM_GRAPH_EDITOR_HANDLE_TYPE_PANEL"
	bl_label = "(JX) Handle Type"
	bl_order = 5000
	bl_space_type = "GRAPH_EDITOR"
	bl_region_type = "UI"
	bl_category = "JxBlender"

	def drawEasing(self, layout, currentType, label, easing):
		row = layout.column(align=True).split(factor=0.25, align=True)
		row.label(text=label)
		row.operator(OP_SetHandleType.bl_idname, depress=currentType==  "SINE-" + easing, text='1').inType =  "SINE-" + easing
		row.operator(OP_SetHandleType.bl_idname, depress=currentType==  "QUAD-" + easing, text='2').inType =  "QUAD-" + easing
		row.operator(OP_SetHandleType.bl_idname, depress=currentType== "CUBIC-" + easing, text='3').inType = "CUBIC-" + easing
		row.operator(OP_SetHandleType.bl_idname, depress=currentType== "QUART-" + easing, text='4').inType = "QUART-" + easing
		row.operator(OP_SetHandleType.bl_idname, depress=currentType== "QUINT-" + easing, text='5').inType = "QUINT-" + easing
		row.operator(OP_SetHandleType.bl_idname, depress=currentType==  "EXPO-" + easing, text='6').inType =  "EXPO-" + easing
		row.operator(OP_SetHandleType.bl_idname, depress=currentType==  "CIRC-" + easing, text='C').inType =  "CIRC-" + easing

	def draw(self, context):
		currentType = None
		if len(context.selected_editable_keyframes) == 1:
			kf = context.selected_editable_keyframes[0]
			currentType = kf.interpolation
			if   kf.interpolation == "BEZIER":	currentType += "-" + kf.handle_right_type
			elif kf.interpolation == 'SINE':	currentType += "-" + kf.easing
			elif kf.interpolation == 'QUAD':	currentType += "-" + kf.easing
			elif kf.interpolation == 'CUBIC':	currentType += "-" + kf.easing
			elif kf.interpolation == 'QUART':	currentType += "-" + kf.easing
			elif kf.interpolation == 'QUINT':	currentType += "-" + kf.easing
			elif kf.interpolation == 'EXPO':	currentType += "-" + kf.easing
			elif kf.interpolation == 'CIRC':	currentType += "-" + kf.easing

		col = self.layout.column(align=True)
		# col.label(text="Bezier")

		row = col.row(align=True)
		row.operator(OP_SetHandleType.bl_idname, text='Linear'  , depress=currentType=="LINEAR"  , icon="IPO_LINEAR"  ).inType = "LINEAR"
		row.operator(OP_SetHandleType.bl_idname, text='Constant', depress=currentType=="CONSTANT", icon="IPO_CONSTANT").inType = "CONSTANT"

		row = col.row(align=True).split(factor=0.5, align=True)
		row.operator(OP_SetHandleType.bl_idname, text='Vector'      , depress=currentType=="BEZIER-VECTOR"      , icon="HANDLE_VECTOR"     ).inType = "BEZIER-VECTOR"
		row.operator(OP_SetHandleType.bl_idname, text='Free'   , depress=currentType=="BEZIER-FREE"   , icon="HANDLE_FREE"   ).inType = "BEZIER-FREE"
		row.operator(OP_SetHandleType.bl_idname, text='Auto'   , depress=currentType=="BEZIER-AUTO"   , icon="HANDLE_AUTO"   ).inType = "BEZIER-AUTO"
		row = col.row(align=True)
		row.operator(OP_SetHandleType.bl_idname, text='Auto Clamped', depress=currentType=="BEZIER-AUTO_CLAMPED", icon="HANDLE_AUTOCLAMPED").inType = "BEZIER-AUTO_CLAMPED"
		row.operator(OP_SetHandleType.bl_idname, text='Aligned', depress=currentType=="BEZIER-ALIGNED", icon="HANDLE_ALIGNED").inType = "BEZIER-ALIGNED"

		# col.label(text="Easing")
		col = col.column(align=True)
		self.drawEasing(col, currentType, "InOut", "EASE_IN_OUT")
		self.drawEasing(col, currentType, "In",    "EASE_IN")
		self.drawEasing(col, currentType, "Out",   "EASE_OUT")
		self.drawEasing(col, currentType, "Auto",  "AUTO")
		
		# layout.label(text="Dynamic Effects")
		# row = layout.row(align=True)
		# row.operator(OP_SetHandleType.bl_idname, text='Back'   , icon="IPO_BACK"   ).inType = "BACK"
		# row.operator(OP_SetHandleType.bl_idname, text='Bounce' , icon="IPO_BOUNCE" ).inType = "BOUNCE"
		# row.operator(OP_SetHandleType.bl_idname, text='Elastic', icon="IPO_ELASTIC").inType = "ELASTIC"


class AnimGraphEditorCurveExtrapolationPanel(jx.types.Panel):
	bl_idname = "JX_PT_ANIM_GRAPH_EDITOR_CURVE_EXTRAPOLATION_PANEL"
	bl_label = "(JX) Curve Extrapolation"
	bl_order = 6000
	bl_space_type = "GRAPH_EDITOR"
	bl_region_type = "UI"
	bl_category = "JxBlender"

	def draw(self, context):
		currentType = None
		if len(context.selected_visible_fcurves) == 1:
			curve = context.selected_visible_fcurves[0]
			m = findCurveModifierByType(curve, "CYCLES")
			if m:
				if   m.mode_after == "REPEAT":			currentType = "CYCLIC"
				elif m.mode_after == "REPEAT_OFFSET":	currentType = "CYCLIC_OFFSET"
				elif m.mode_after == "MIRROR":			currentType = "CYCLIC_MIRROR"
			else:
				if   curve.extrapolation == "CONSTANT":	currentType = "CONSTANT"
				elif curve.extrapolation == "LINEAR":	currentType = "LINEAR"

		col = self.layout.column(align=True)
		row = col.row(align=True)
		row.operator(OP_SetChannelExtrapolation.bl_idname, text="Linear",   depress=currentType=="LINEAR"  ).inType="LINEAR"
		row.operator(OP_SetChannelExtrapolation.bl_idname, text="Constant", depress=currentType=="CONSTANT").inType="CONSTANT"
		row = col.row(align=True)
		row.operator(OP_SetChannelExtrapolation.bl_idname, text="Repeat", depress=currentType=="CYCLIC"       ).inType="CYCLIC"
		row.operator(OP_SetChannelExtrapolation.bl_idname, text="Offset", depress=currentType=="CYCLIC_OFFSET").inType="CYCLIC_OFFSET"
		row.operator(OP_SetChannelExtrapolation.bl_idname, text="Mirror", depress=currentType=="CYCLIC_MIRROR").inType="CYCLIC_MIRROR"


