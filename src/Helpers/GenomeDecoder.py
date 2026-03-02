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
        statFileDecoder(sys.argv[1], sys.argv[2])
    except IndexError:
        print("Usage: statFileDecoder fileIn fileOut [noUnits=]")
    except FileNotFoundError:
            print("You entered filename: ", sys.argv[1])
            print("File not found")
    except:
        raise            
            
def statFileDecoder(statFileIn,statFileOut, noUnits=6, rounding=2, noEvolvedUnits=None):
    """Read a GA stat file and convert the values in the genome
       (all in (0,1) range) to the actual value used by the units.

       The GA stat file structure is composed by identical line containing
       Run Number
       Final Distance
       Run time
       genome for each unit (essentParam each for each evolved unit)
       connection weights   (noEvolvedUnits * noUnits)

       noEvolvedUnits defaults to noUnits for backward compatibility
       with old 60-gene logbooks.
       """
    if noEvolvedUnits is None:
        noEvolvedUnits = noUnits
    headers = ['Run', 'Dist.', 'Time']
    for unit in range(noEvolvedUnits):
        headers.append('U'+str(unit+1)+'-mass')
        headers.append('U'+str(unit+1)+'-visc')
        headers.append('U'+str(unit+1)+'-unis-time')
        headers.append('U'+str(unit+1)+'-maxDev')

    for connIn in range(noEvolvedUnits):
        for connOut in range(noUnits):
            headers.append('Conn-W-'+str(connIn+1)+'-to-'+str(connOut+1))

    fileIn= open(statFileIn,"r")
    if statFileOut is not None:
        fileOut = open(statFileOut, "w")
    else:
        print("Usage: statFileGenomeDecoder fileIn fileOut")
        print("Please enter a filename to write the decoded genome information to")
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
        convertedGenome = genomeDecoder(noUnits, lineAsFloats[3:], noEvolvedUnits=noEvolvedUnits)
        for value in convertedGenome:
            fileOut.write(str(round(value, rounding))+"\t")
        fileOut.write("\n")        
    fileOut.close()
    
def genomeDecoder(noUnits, genome, noEvolvedUnits=None, layout=None):
    """Convert the values in the genome to the actual value used by the units.

    Accepts a list of floats (values all in (0,1) range).

    Parameters
    ----------
    noUnits : int
        Total number of units in the homeostat.
    genome : list of float
        Raw genome values in [0, 1).
    noEvolvedUnits : int, optional
        Number of units whose body params are evolved.
        Defaults to noUnits for backward compatibility.
    layout : str, optional
        Genome layout identifier:
        - None or 'classic'  : 4 body params + connection weights (old GA)
        - 'weightfree'       : 4 body params per unit, no connection weights
        - 'weightfree_dt'    : 5 body params per unit (incl. dt_fast), no weights

        When layout is None, the function auto-detects based on genome size:
        if len(genome) == noEvolvedUnits * noUnits + noEvolvedUnits * 4,
        it's 'classic'; otherwise it tries the weight-free layouts.

    Returns a list of decoded actual values.
    """
    if noEvolvedUnits is None:
        noEvolvedUnits = noUnits

    # Auto-detect layout from genome size
    if layout is None:
        classic_size = noEvolvedUnits * 4 + noEvolvedUnits * noUnits
        wf4_size = noEvolvedUnits * 4
        wf5_size = noEvolvedUnits * 5
        gl = len(genome)
        if gl == classic_size:
            layout = 'classic'
        elif gl == wf5_size:
            layout = 'weightfree_dt'
        elif gl == wf4_size:
            layout = 'weightfree'
        else:
            layout = 'classic'   # fallback

    if layout == 'classic':
        return _decode_classic(noUnits, genome, noEvolvedUnits)
    elif layout == 'weightfree':
        return _decode_weightfree(genome, noEvolvedUnits, has_dt_fast=False)
    elif layout == 'weightfree_dt':
        return _decode_weightfree(genome, noEvolvedUnits, has_dt_fast=True)
    else:
        return _decode_classic(noUnits, genome, noEvolvedUnits)


def _decode_classic(noUnits, genome, noEvolvedUnits):
    """Classic layout: 4 body params per evolved unit + connection weights."""
    decodedValues = []
    essenVar = 4
    for unit in range(noEvolvedUnits):
        decodedValues.append(HomeoUnit.massFromWeight(genome[(unit*essenVar) + 0]))                    # Mass
        decodedValues.append(HomeoUnit.viscosityfromWeight(genome[(unit*essenVar) +1]))               # Viscosity
        decodedValues.append(HomeoUnit.uniselectorTimeIntervalFromWeight(genome[(unit*essenVar) +2])) # UniselectorTiming (integer)
        decodedValues.append(HomeoUnit.maxDeviationFromWeight(genome[(unit*essenVar) + 3]))            # maxDeviation (integer)

    offset = essenVar * noEvolvedUnits
    for conn in range(noEvolvedUnits * noUnits):
        decodedValues.append(HomeoConnection.connWeightFromGAWeight(genome[offset + conn]))

    return decodedValues


def _decode_weightfree(genome, noEvolvedUnits, has_dt_fast=True):
    """Weight-free layout: body params only, no connection weights.

    Per-unit gene order: [mass, viscosity, tau_a, maxDeviation, (dt_fast)].
    """
    decodedValues = []
    genes_per_unit = 5 if has_dt_fast else 4
    for unit in range(noEvolvedUnits):
        base = unit * genes_per_unit
        decodedValues.append(HomeoUnit.massFromWeight(genome[base + 0]))
        decodedValues.append(HomeoUnit.viscosityfromWeight(genome[base + 1]))
        decodedValues.append(HomeoUnit.tauAFromWeight(genome[base + 2]))
        decodedValues.append(HomeoUnit.maxDeviationFromWeight(genome[base + 3]))
        if has_dt_fast:
            decodedValues.append(HomeoUnit.dtFastFromWeight(genome[base + 4]))

    return decodedValues

def genomePrettyPrinter(noUnits, decodedGenome, noEvolvedUnits=None, layout=None):
    """Return a string with all decoded values preceded by labels.
       noEvolvedUnits defaults to noUnits for backward compatibility."""
    if noEvolvedUnits is None:
        noEvolvedUnits = noUnits

    if layout in ('weightfree_dt', 'weightfree'):
        return _pretty_print_weightfree(decodedGenome, noEvolvedUnits, layout)

    # Classic layout
    outString = ''
    essVar = 4
    for unit in range(noEvolvedUnits):
        outString += 'mass: '
        outString += str(round(decodedGenome[(unit*essVar)+0],3))           # Mass
        outString += '\tvisc: '
        outString += str(round(decodedGenome[(unit*essVar)+1],3))           # Viscosity
        outString += '\tunisel: '
        outString += str(round(decodedGenome[(unit*essVar)+2],3))           # UniselectorTiming (integer)
        outString += '\tmaxDev: '
        outString += str(round(decodedGenome[(unit*essVar)+3],3))            # maxDeviation (integer)
        outString += '\n'

    for connIn in range(noEvolvedUnits):
        #outString += '\t'
        for connOut in range(noUnits):
            outString += (str(connIn+1) + ' to ' +  str(connOut+1) + ': ')
            outString += str(round(decodedGenome[(noEvolvedUnits*essVar)+(noUnits*connIn) + connOut],3))
            outString += '\t'
        outString += '\n'
    return outString


def _pretty_print_weightfree(decodedGenome, noEvolvedUnits, layout):
    """Pretty-print a weight-free decoded genome."""
    has_dt = (layout == 'weightfree_dt')
    ppunit = 5 if has_dt else 4
    outString = ''
    for unit in range(noEvolvedUnits):
        base = unit * ppunit
        outString += 'mass: %s' % round(decodedGenome[base + 0], 3)
        outString += '\tvisc: %s' % round(decodedGenome[base + 1], 3)
        outString += '\ttau_a: %s' % round(decodedGenome[base + 2], 3)
        outString += '\tmaxDev: %s' % round(decodedGenome[base + 3], 3)
        if has_dt:
            outString += '\tdt_fast: %s' % round(decodedGenome[base + 4], 3)
        outString += '\n'
    outString += '(no connection weights in genome)\n'
    return outString
    
if __name__ == "__main__":
    main(sys.argv[0])
    
    