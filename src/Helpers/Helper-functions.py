"""
General python utility methods, functions, and classes
"""

def withAllSubclasses(aClass):
	"""
	Return a list with aClass and all its subclasses
	"""
	
	subs = [].append(aClass)
	try:
		subs.extend([x for x in aClass.__subclasses__()])
	return subs 