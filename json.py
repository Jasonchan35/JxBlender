import json
import bpy
import jx.debug

def saveToFile(obj, filename:str):
	print(f"save json file \"{filename}\"")

	jsonStr = json.JSONEncoder(indent=2).encode(obj)
	with open(filename, "w") as file:
		file.write(jsonStr)
		file.close()

def loadFromFile(filename:str):
	print(f"load json file \"{filename}\"")
	str = ""
	with open(filename, "r") as file:
		str = file.read()
		file.close()

	obj = json.JSONDecoder().decode(str)
	#print(f"json str={obj}")
	return obj

def toValue(v):
	if isinstance(v, (int, float, bool, str)):
		return v

	if isinstance(v, bpy.types.bpy_prop_array):
		return tuple(v)

	jx.debug.dump(v)

	raise RuntimeError(f"unsupported type to json value class={v.__class__}")

