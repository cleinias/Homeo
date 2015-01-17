'''
Created on Dec 30, 2014
Utilities to interpret the genome of a Homeostat for further analysis
@author: stefano
'''
from Core.HomeoUnit import *
from Core.HomeoConnection import *
import sys
from twisted.protocols.ftp import FileNotFoundError

def main(argv):
    try:
        statFileDecoder(sys.argv[1], sys.argv[2])
    except IndexError:
        print "Usage: statFileDecoder fileIn fileOut [noUnits=]"
    except FileNotFoundError:
            print "You entered filename: ", sys.argv[1]
            print "File not found"
    except:
        raise            
            
def statFileDecoder(statFileIn,statFileOut, noUnits=6, rounding=2):
    """Read a GA stat file and convert the values in the genome
       (all in (0,1) range) to the actual value used by the units.
       
       The GA stat file structure is composed by identical line containing
       Run Number
       Final Distance
       Run time
       genome for each unit (essentParam each for each unit in noUnits)
       connection weights   (noUnits^2)  
       """
    headers = ['Run', 'Dist.', 'Time']
    for unit in xrange(noUnits):
        headers.append('U'+str(unit+1)+'-mass')
        headers.append('U'+str(unit+1)+'-visc')
        headers.append('U'+str(unit+1)+'-unis-time')
        headers.append('U'+str(unit+1)+'-maxDev')

    for connIn in xrange(noUnits):
        for connOut in xrange(noUnits):
            headers.append('Conn-W-'+str(connIn+1)+'-to-'+str(connOut+1))
    
    fileIn= open(statFileIn,"r")
    if statFileOut is not None:
        fileOut = open(statFileOut, "w")
    else:
        print "Usage: statFileGenomeDecoder fileIn fileOut"
        print "Please enter a filename to write the decoded genome information to"
        return
    lines = fileIn.readlines()
    fileIn.close()
    
    "adding headers"
    for heading in headers:
        fileOut.write(heading+"\t")
    fileOut.write("\n")
    "Converting Ga lines into converted valued"
    for lineAsString in lines:
        line = lineAsString.split()
        "General run info"
        fileOut.write(line[0]+"\t")              # Run number
        fileOut.write(line[1]+"\t")              # Final Distance
        fileOut.write(line[2]+"\t")              # Run Time
        "Converting genome and printing to file"
        lineAsFloats = [float(x) for x in line]
        convertedGenome = genomeDecoder(noUnits, lineAsFloats[3:])
        for value in convertedGenome:
            fileOut.write(str(round(value, rounding))+"\t")
        fileOut.write("\n")        
    fileOut.close()
    
def genomeDecoder(noUnits, genome):
    """Convert the values in the genome to the actual value used by the units
       Accepts a list of floats (values all in (0,1) range) whose length is: 
       noUnits*essentVars + noUnits**2
       Depends on Units having 4 essential variables
       Return a list of actual values.
    """
    decodedValues = []
    essenVar = 4
    "Converting units' values"
    for unit in xrange(noUnits):
        decodedValues.append(HomeoUnit.massFromWeight(genome[(unit*essenVar) + 0]))                    # Mass        
        decodedValues.append(HomeoUnit.viscosityfromWeight(genome[(unit*essenVar) +1]))               # Viscosity
        decodedValues.append(HomeoUnit.uniselectorTimeIntervalFromWeight(genome[(unit*essenVar) +2])) # UniselectorTiming (integer)                
        decodedValues.append(HomeoUnit.maxDeviationFromWeight(genome[(unit*essenVar) + 3]))            # maxDeviation (integer)                        
    
    "Converting connection weights"
    for conn in xrange(noUnits*noUnits):
        decodedValues.append(HomeoConnection.connWeightFromGAWeight(genome[(essenVar*noUnits)+conn]))

    return decodedValues

def genomePrettyPrinter(noUnits, decodedGenome):
    "Return a string with all decoded values preceded by labels "
    outString = ''
    essVar = 4
    for unit in xrange(noUnits):
        outString += 'mass: '
        outString += str(round(decodedGenome[(unit*essVar)+0],3))           # Mass
        outString += '\tvisc: '
        outString += str(round(decodedGenome[(unit*essVar)+1],3))           # Viscosity
        outString += '\tunisel: '
        outString += str(round(decodedGenome[(unit*essVar)+2],3))           # UniselectorTiming (integer) 
        outString += '\tmaxDev: '               
        outString += str(round(decodedGenome[(unit*essVar)+3],3))            # maxDeviation (integer)  
        outString += '\n'                      
    
    for connIn in xrange(noUnits):
        #outString += '\t'
        for connOut in xrange(noUnits):
            outString += (str(connIn+1) + ' to ' +  str(connOut+1) + ': ')
            outString += str(round(decodedGenome[(noUnits*essVar)+(noUnits*connIn) + connOut],3))
#            print " reading weight at: %d as from %d to %d" %(((noUnits*essVar)+(noUnits*connIn) + connOut), connIn+1 , connOut + 1)
            outString += '\t'   
        outString += '\n'
    return outString 
    
if __name__ == "__main__":
    main(sys.argv[0])
    
    