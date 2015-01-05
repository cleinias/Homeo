'''
Created on Jan 4, 2015

@author: stefano
'''
from deap import tools
import pickle
from os import chdir
import matplotlib.pyplot as plt
from Helpers.ExceptionAndDebugClasses import hDebug
from Helpers.GenomeDecoder import genomeDecoder
from operator import itemgetter
from tabulate import tabulate


def main():
    chdir("/home/stefano/Documents/Projects/Homeostat/Simulator/Python-port/Homeo/SimulationsData/Testing")
    filename = logfile = open('Logbook-2015-01-03-17-39-20.lgb','r')
    logbook = pickle.load(filename)
    hDebug('ga',"Logbook loaded")
    indivs = indivsDecodedFromLogbook(logbook)
    fitness_data = minMaxAvgFromLogbook(logbook)
    hof = hallOfFameInds(indivs, 10, max=False)
    genomeAndFitnessPrettyPrinter(hof, noUnits=6)
    minMaxAvgFitPlot(fitness_data[0], fitness_data[1],fitness_data[2], fitness_data[3])
    
def minMaxAvgFitPlot(gen, fit_mins, fit_maxs, fit_avgs):
    "Plot min, max, and average fitnesses per generation"
    
    "FIXME: Make axes equal (not scaled differently)"
    
    fig, ax1 = plt.subplots()
    line1 = ax1.plot(gen, fit_mins, "b-", label="Minimum Fitness")
    ax1.set_xlabel("Generation")
    ax1.set_ylabel("Fitness", color="b")
    for tl in ax1.get_yticklabels():
        tl.set_color("b")
    
    ax2 = ax1.twinx()
    line2 = ax2.plot(gen, fit_avgs, "r-", label="Average Fitness")
    #for tl in ax2.get_yticklabels():
    #    tl.set_color("r")
    
    ax3 = ax1.twinx()
    line3 = ax3.plot(gen, fit_maxs, "y-", label="Max Fitness")
    for tl in ax3.get_yticklabels():
        tl.set_color("y")

    lns = line1 + line2 + line3
    labs = [l.get_label() for l in lns]
    ax1.legend(lns, labs, loc="upper right")
    
    plt.show()

def minMaxAvgFromLogbook(logbook):
    """Extract data about min, max, and avg fitness from Deap logbook
       Return a tuple of fitness lists, prefix with a list with the generations"""
    
    fit_records = [x for x in logbook if 'std' in x]
    gens = [x["gen"] for x in fit_records]
    fit_mins = [x["min"] for x in fit_records]
    fit_maxs = [x["max"] for x in fit_records]
    fit_avgs  = [x["avg"] for x in fit_records]
   
    ' Debugging'
    hDebug('ga',("%s\t%s\t%s\t%s" %("gen", "min", "max", "avg")))
    for gen, fmin, fmax, favg in zip(gens, fit_mins, fit_maxs, fit_avgs):
        hDebug('ga',("%d\t%.3f\t%.3f\t%.3f" % (gen, fmin,fmax,favg))) 
    'end debugging'
    
    return (gens,fit_mins,fit_maxs,fit_avgs)

def indivsDecodedFromLogbook(logbook, noUnits=6):
    """Extracts all the individual genomes from the logbook, 
    with associated fitnesses"""
    rawIndivs = [x for x in logbook if "genome" in x]
    indivs = []
    for ind in rawIndivs:
        fit = ind["fitness"]
        decodedInd = genomeDecoder(noUnits,ind["genome"])
        indivs.append((decodedInd, fit))
    return indivs

def hallOfFameInds(indivs, num, max=False):
    """Return the best num individuals from indivs (a list of individuals).
       Expects a list of tuples/list containing the genome at [0] and the fitness at [1].
       if max = True, sorts in ascending order (i.e for max fitness)"""
    a =  sorted(indivs,key=itemgetter(1), reverse = max)
    return a[:num]

def genomeAndFitnessPrettyPrinter(decodedIndivs, noUnits=6):
    """Formats and prints a (possibly sorted) list
       of decoded individual genomes passed as a list of
       tuples with genome at [0] and fitness at [1].
       Assumes 4 essential variables for homeoUnits"""
    
    'Construct headers'
    headers = ['Fitness']
    for unit in xrange(noUnits):
        headers.append('U'+str(unit+1)+'-mass')
        headers.append('U'+str(unit+1)+'-visc')
        headers.append('U'+str(unit+1)+'-unis-time')
        headers.append('U'+str(unit+1)+'-maxDev')

    for connIn in xrange(noUnits):
        for connOut in xrange(noUnits):
            headers.append('Conn-W-'+str(connIn+1)+'-to-'+str(connOut+1))
    
    'Flattens list of tuples including individual genomes and fitnesses to a list of lists'
    individuals = []
    for ind in decodedIndivs:
        individuals.append(list(ind[1])+ind[0])
    print tabulate(individuals, headers, tablefmt='orgtbl')


    
if __name__=="__main__":
    main()
    