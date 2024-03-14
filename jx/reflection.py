def classname(obj):
	cls = obj.__class__
	return f"{cls.__module__}.{cls.__name__}"
