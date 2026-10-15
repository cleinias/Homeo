'''
Created on Dec 31, 2014
Exception and debug classes shared by all modules
@author: stefano
'''

from sys import stderr 

class HomeoDebug(object):
    """Utility class that allows conditional printing of 
    debugging information depending on how the debugging
    parameters are set by the calling application.
    
    HomeoDebug has no instances, just a class-side collection
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
           printing of some classes of error messages.
           Codes is a space-separated string of allowed error classes codes, 
           or the string 'all' """
        if 'all' in codes.split():
            HomeoDebug.debugCodes = set(HomeoDebug.allowableCodes)
        else:
            for code in codes.split():
                if code in HomeoDebug.allowableCodes:
                    HomeoDebug.debugCodes.add(code)
                else:
                    stderr.write("Trying to add a non-allowed debugging code: " + code + "\n")
    
    
    @classmethod
    def printDebugMesg(cls,codes,debugString,*args):
        """Method to be used by all classes wishing to print error messages.
           With args, debugString is a %-format, filled in only when the
           message is printed: hot paths pay nothing when debugging is off."""
        if not cls.debugCodes:
            return
        if set(codes.split()) <= HomeoDebug.debugCodes:
            stderr.write((debugString % args if args else debugString)+"\n")

"Alias to bypass Python's inability to import class methods"
def hDebug(a, b, *args):
    HomeoDebug.printDebugMesg(a, b, *args)      