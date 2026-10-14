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
            
def statFileDecoder(statFileIn,statFileOut, noUnits=6, rounding=2, noEvolvedUnits=None,
                    layout=None):
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
       layout: see genomeDecoder; None detects it from the first line's
       genome, and every line must have the same.  The headers are the
       layout's: until 14 Oct 2026 they were always the classic ones, so a
       weight-free genome was written under them (HN-11).
       """
    if noEvolvedUnits is None:
        noEvolvedUnits = noUnits

    fileIn= open(statFileIn,"r")
    if statFileOut is not None:
        fileOut = open(statFileOut, "w")
    else:
        print("Usage: statFileGenomeDecoder fileIn fileOut")
        print("Please enter a filename to write the decoded genome information to")
        return
    lines = [line for line in fileIn.readlines() if line.strip()]
    fileIn.close()
    if layout is None and lines:
        layout = genomeLayout(noUnits, len(lines[0].split()) - 3, noEvolvedUnits)
    headers = ['Run', 'Dist.', 'Time'] + genomeHeaders(noUnits, noEvolvedUnits, layout)

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
        convertedGenome = genomeDecoder(noUnits, lineAsFloats[3:], noEvolvedUnits=noEvolvedUnits,
                                        layout=layout)
        for value in convertedGenome:
            fileOut.write(str(round(value, rounding))+"\t")
        fileOut.write("\n")        
    fileOut.close()
    
def classicConnectionSources(noUnits, noEvolvedUnits):
    """The (unit, source) pair of each connection gene of the classic layout,
    in gene order, units numbered from 1 in the order they were added.

    The classic GA setup (initializeBraiten2_2_Full_GA) writes each evolved
    unit's genes over its inputConnections, which addFullyConnectedUnit orders
    as the self-connection first, then the other units in the order they were
    added: unit k's genes are its inputs from k, 1, ..., k-1, k+1, ..., N.
    Until 14 Oct 2026 the labels read gene k*N+j as the connection from unit
    k to unit j+1 (review finding HN-03): reversed, and, for every unit but
    the first, rotated -- the self-connection was labelled k-to-1."""
    pairs = []
    for unit in range(1, noEvolvedUnits + 1):
        pairs.append((unit, unit))
        pairs += [(unit, source) for source in range(1, noUnits + 1) if source != unit]
    return pairs


def classicConnectionLabels(noUnits, noEvolvedUnits):
    "Column labels of the classic connection genes: 'W-<unit>-from-<source>'."
    return ['W-%d-from-%d' % pair for pair in classicConnectionSources(noUnits, noEvolvedUnits)]


GENOME_LAYOUTS = ('classic', 'weightfree', 'weightfree_dt')


def genomeSize(noUnits, noEvolvedUnits, layout):
    "The number of genes of a layout (see genomeDecoder)."
    return {'classic': noEvolvedUnits * 4 + noEvolvedUnits * noUnits,
            'weightfree': noEvolvedUnits * 4,
            'weightfree_dt': noEvolvedUnits * 5}[layout]


def genomeLayout(noUnits, length, noEvolvedUnits=None):
    """The layout of a genome of this length.  A length that matches no
    layout is an error: until 14 Oct 2026 it was read as classic, silently
    dropping extra genes (HN-11)."""
    if noEvolvedUnits is None:
        noEvolvedUnits = noUnits
    for layout in GENOME_LAYOUTS:
        if length == genomeSize(noUnits, noEvolvedUnits, layout):
            return layout
    raise ValueError('a genome of %d genes matches no layout for %d units, %d evolved'
                     % (length, noUnits, noEvolvedUnits))


def genomeHeaders(noUnits, noEvolvedUnits, layout=None):
    "Column labels of a decoded genome in this layout (None: classic)."
    headers = []
    if layout in ('weightfree', 'weightfree_dt'):
        for unit in range(noEvolvedUnits):
            u = 'U' + str(unit + 1)
            headers += [u + '-mass', u + '-visc', u + '-tau_a', u + '-maxDev']
            if layout == 'weightfree_dt':
                headers.append(u + '-dt_fast')
    else:
        for unit in range(noEvolvedUnits):
            u = 'U' + str(unit + 1)
            headers += [u + '-mass', u + '-visc', u + '-unis-time', u + '-maxDev']
        headers += classicConnectionLabels(noUnits, noEvolvedUnits)
    return headers


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

        When layout is None, the function detects it from the genome's size
        (genomeLayout); a size that matches no layout, or a genome of the
        wrong size for the given layout, raises ValueError.

    Returns a list of decoded actual values.
    """
    if noEvolvedUnits is None:
        noEvolvedUnits = noUnits

    if layout is None:
        layout = genomeLayout(noUnits, len(genome), noEvolvedUnits)
    if layout not in GENOME_LAYOUTS:
        raise ValueError('layout must be one of %s, got %r' % (GENOME_LAYOUTS, layout))
    if len(genome) != genomeSize(noUnits, noEvolvedUnits, layout):
        raise ValueError('a %s genome for %d units, %d evolved, has %d genes, not %d'
                         % (layout, noUnits, noEvolvedUnits,
                            genomeSize(noUnits, noEvolvedUnits, layout), len(genome)))

    if layout == 'classic':
        return _decode_classic(noUnits, genome, noEvolvedUnits)
    return _decode_weightfree(genome, noEvolvedUnits, has_dt_fast=(layout == 'weightfree_dt'))


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

    Per-unit gene order: [mass, viscosity, tau_a, maxDeviation, (dt_fast)],
    decoded as the weight-free setups in Simulator/HomeoExperiments.py do.
    """
    decodedValues = []
    genes_per_unit = 5 if has_dt_fast else 4
    for unit in range(noEvolvedUnits):
        base = unit * genes_per_unit
        decodedValues.append(HomeoUnit.massFromWeightWeightfree(genome[base + 0]))
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

    offset = noEvolvedUnits * essVar
    for gene, (unit, source) in enumerate(classicConnectionSources(noUnits, noEvolvedUnits)):
        outString += '%d from %d: %s\t' % (unit, source, round(decodedGenome[offset + gene], 3))
        if (gene + 1) % noUnits == 0:
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
    
    