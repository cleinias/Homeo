"""
General python utility methods, functions, and classes
"""

def withAllSubClasses(aClass):
	"""
	Return a list with aClass and all its subclasses
	"""
	
	subs = []
	subs.append(1)	
	subs.append(aClass)
	subs.extend([x for x in aClass.__subclasses__()])
	return subs 
	
def iden(a):
	return a
