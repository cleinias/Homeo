# Copyright (C) 2015-2026 Stefano Franchi
#
# This file is part of Homeo, a simulation of Ashby's homeostat and of
# homeostat-controlled robots.
#
# Homeo is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your
# option) any later version.
#
# Homeo is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License
# for more details.
#
# You should have received a copy of the GNU General Public License
# along with Homeo.  If not, see <https://www.gnu.org/licenses/>.
#
# SPDX-License-Identifier: GPL-3.0-or-later

'''
Exception and debug classes shared by all modules
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