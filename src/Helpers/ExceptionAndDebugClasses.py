'''
Created on Dec 31, 2014
Exception and debug classes shared by all modules
@author: stefano
'''

from sys import stderr 

class TCPConnectionError(Exception):
    def __init__(self, value):
            self.value = value
    def __str__(self):
        return repr(self.value)


class HomeoDebug(object):
    """Utility class that allows conditional printing of 
    debugging information depending on how the debugging
    parameters are set by the calling application.
    
    HomeoDebug as no instances, just a class-side collection
    keeping all the debugging codes and class methods.
    
    Debugging codes are strings. Current codes:
    
    network = networking-related
    eval = evaluation (for GA applications)
    ga = Genetic Algorithm related
    unit = HomeoUnit-related
    conn = HomeoConnection related
    major = major errors forcing application to stop"""
    
    
    allowableCodes = ['network','eval', 'ga', 'unit', 'conn', 'major']
    debugCodes = set()
    
    
    @classmethod
    def addDebugCodes(cls,codes):
        """Class method to be used by all apps wishing to enable
           printing of some classes of erroc messages.
           Codes is a space-separated string of allowed error classes codes"""
        for code in codes.split():
            if code in HomeoDebug.allowableCodes:
                HomeoDebug.debugCodes.add(code)
            else:
                stderr.write("Trying to add a non-allowed debugging code: " + code + "\n")
    
    
    @classmethod
    def printDebugMesg(cls,codes,debugString):
        "Method to be used by all classes wishing to print error messages"
        if set(codes.split()) <= HomeoDebug.debugCodes:
            stderr.write(debugString+"\n")

"Alias to bypass Python's inability to import class methods"
def hDebug(a,b):
    HomeoDebug.printDebugMesg(a, b)      