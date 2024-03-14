# JxBlender - addon

[Demo Video](screenshots/JxBlender%20-%202024-03-13_c.mp4)

## Install

1. Download latest jx.zip from https://github.com/Jasonchan35/JxBlender/releases
2. Blender Menu > Edit > Preferences > Add-ons (page)
3. Install button and pick the downloaded jx.zip

For export setting:
1. Add file "JxProject.json" in project root folder, for example "c:\my_porject"
2. with content below
```
{
	"require_fps": 30,
	"require_length_unit": "METERS",
	"require_scale_length": 1,
	"rawDataPath": "RawData",
	"rawDataExportDir": "ExportFolder"
}
```
3. In this case, file will export as below
	- From "c:\MyPorject\RawData\ABC\Mesh.blend"
	- To   "c:\MyProject\ExportFolder\ABC\Mesh.fbx"
	- Animation filename will be "Mesh@anim_name.fbx"

Enjoy !

## Features
- Export to Unreal / Unity
	- Detect fps, length unit in scene file and button for auto correct
	- Export meshes, Material properties and texture with meta data (.json file)
		- Any Mesh in collection "JX_EXPORT" will be exported
	- Export Animation from NLA tracks (support Root montion)
		- Any track name starts with "OUT-" will be exported

- NLA Track managment
- Graphic Editor Tool Panel
	- Quick Show / Hide curves
	- Tool buttons for Keyframe Handle Type, Curve Extrapolation
- Animation Re-targeting
	- FK / IK mappings
	- Load / Save mappings present to file