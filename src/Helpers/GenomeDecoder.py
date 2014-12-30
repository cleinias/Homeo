'''
Created on Dec 30, 2014
Utilities to interpret the genome of a Homeostat for further analysis
@author: stefano
'''
from Core.HomeoUnit import *
from Core.HomeoConnection import *
import sys

def main(argv):
    try:
        statFileGenomeDecoder(sys.argv[1], sys.argv[2])
    except IndexError:
        print "Usage: genomeDecoder fileIn fileOut [noUnits=]"
    except:
            print "You entered filename: ", sys.argv[1]
            print "File not found"
            
            
def statFileGenomeDecoder(statFileIn,statFileOut, noUnits=6):
    """Read a GA stat file and convert the values in the genome
       (all in (,1) range to the actual value used by the units.
       
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
        print " Please enter a filename to write the decoded genome information to"
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
        "Now reading units's values"
        for unit in xrange(noUnits):
                realMass = HomeoUnit.massFromWeight(float(line[(4*(unit+1))+0]))                      # Mass
                fileOut.write(str(realMass)+"\t")
                realViscosity = HomeoUnit.viscosityfromWeight(float(line[(4*(unit+1))+1]))            # Viscosity
                fileOut.write(str(realViscosity)+"\t")
                realTiming = HomeoUnit.uniselectorTimeIntervalFromWeight(float(line[(4*(unit+2))+2])) # UniselectorTiming (integer)                
                fileOut.write(str(realTiming)+"\t")
                realDeviation = HomeoUnit.maxDeviationFromWeight(float(line[(4*(unit+1))+3]))         # maxDeviation (integer)                        
                fileOut.write(str(realDeviation)+"\t")
        "now reading connection weights and writing them out unchanged"
        for conn in xrange(noUnits*noUnits):
            realConnWeight = HomeoConnection.connWeightFromGAWeight(float(line[(((4*noUnits)+3)+conn)]))
            fileOut.write(str(realConnWeight)+"\t")
        fileOut.write("\n")        
    fileOut.close()
    

if __name__ == "__main__":
    main(sys.argv[0])
    
    