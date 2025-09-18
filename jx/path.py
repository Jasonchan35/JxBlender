import os.path

def realpath(p:str):
	return to_unix(os.path.realpath(p))

def relpath(p:str, rel_to:str):
	return os.path.relpath(p, rel_to)

def to_unix(p:str):
	return p.replace("\\", "/")

def to_windows(p:str):
	return p.replace("/", "\\")

def basename(p:str):
	return os.path.basename(p)

def dirname(p:str):
	return os.path.dirname(p)

def exists(p:str):
	return os.path.exists(p)

def remove_ext(p:str):
	return os.path.splitext(p)[0]

def change_ext(p:str, new_ext:str):
	return remove_ext(p) + new_ext

def normpath(p:str):
	return os.path.normpath(p)

def findFileUpward(fromFolder:str, filename:str):
	root = fromFolder

	while True:
		f = realpath(root + "/" + filename)
		parent = dirname(root)
		if parent == root:
			return None
		if exists(f):
			return f
		root = parent

