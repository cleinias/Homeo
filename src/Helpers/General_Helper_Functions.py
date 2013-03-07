def withAllSubclasses(aClass):
    """
    Return a list wiith aClass and all its first-level subclasses
    """
    subs = []
    subs.append(aClass)
    subs.extend([x for x in aClass.__subclasses__()])
    return subs

class Foo(object):
    pass
    
