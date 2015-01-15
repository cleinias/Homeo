'''
Created on Jan 4, 2015

Functions that read the logbook produced by a DEAP GA simulation
and provide info, stats, and charts about the GA run

@author: stefano
'''
from deap import tools
import pickle
import os
import matplotlib.pyplot as plt
from Helpers.ExceptionAndDebugClasses import hDebug
from Helpers.GenomeDecoder import genomeDecoder
from operator import itemgetter
from tabulate import tabulate
import csv
from deap import creator, base

def main():
    "All function calls in the main() functions are for testing purposes only"  
    dirL='/home/stefano/Documents/Projects/Homeostat/Simulator/Python-port/Homeo/SimulationsData/'
    fileL = 'History-2015-01-11-12-55-19.hist'
    filename = os.path.join(dirL,fileL)
    #logbook = pickle.load(open(filename, 'r'))
    #---------------------------------------------
    #
    # Experiment to see whether I can unpickle the history object in a different environment
    creator.create("FitnessMin", base.Fitness, weights=(-1.0,))
    
    'Homeostat genome is a list plus an ID'     
    creator.create("Individual", list, fitness=creator.FitnessMin, ID=None)   

                
    'Register function to create a random individual'
    #toolbox.register("individual", self.initIndividual, creator.Individual, genomeSize=self.genomeSize, ID = 'DummyID')  
    
    'Register function to create an individual with given genome'
    #toolbox.register('individualClone', self.initIndividualClone, creator.Individual, self.clonableGenome)
    
    #
    #---------------------------------------------
    history = pickle.load(open(filename,'r'))
    showGenealogyTree(history)
    #hDebug('ga',"Logbook loaded")
    #indivs = indivsDecodedFromLogbook(logbook)
    #fitness_data = minMaxAvgFromLogbook(logbook)
    #indID = '001-003'
    #gens = extractAllGenomes(filename)
    #print indID, extractGenomeOfIndID(indID, (os.path.join(os.getcwd(),"Logbook-2015-01-04-19-11-21.lgb")))
    #saveGenomeToCSV(extractGenomeOfIndI('001-001', 
    #                                    (os.path.join(os.getcwd(),"Logbook-2015-01-04-19-11-21.lgb"))), 
    #                os.path.join(os.getcwd(),indID+'-genome.gnm'))
    #hof = hallOfFameInds(indivs, 10, max=False)
    #minMaxAvgFitPlot(fitness_data[0], fitness_data[1],fitness_data[2], fitness_data[3])
    
def plotFitnessesFromLogBook(logbook):
    """Produce a MatplotLib chart of min, max, and avg fitness
       from data extracted from the logbook"""
    
    fitness_data = minMaxAvgFromLogbook(logbook)
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
    """Extract data about min, max, and avg fitness from DEAP logbook
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
    with associated fitnesses and individual's name of form #gen-#"""
    rawIndivs = [x for x in logbook if "genome" in x]
    indivs = []
    for ind in rawIndivs:
        fit = ind["fitness"]
        decodedInd = genomeDecoder(noUnits,ind["genome"])
        name = ind["indivId"]
        indivs.append((decodedInd, fit, name))
        print "ind: %s\t has fitness: %.2f" % ( name, fit[0])
    return indivs

def hallOfFameInds(indivs, num, max=False):
    """Return the best num individuals from indivs (a list of individuals).
       Expects a list of tuples/list containing the genome at [0] and the fitness at [1].
       if max = True, sorts in ascending order (i.e for max fitness)"""
    a =  sorted(indivs,key=itemgetter(1), reverse = max)
    return a[:num]

def hallOfFame(logbook, num=10, max=False):
    """Return a string containing a formatted and sorted hall of fame list
       of individuals extracted from the logbook"""
    
    return genomeAndFitnessPrettyPrinter(hallOfFameInds(indivsDecodedFromLogbook(logbook),
                                                        num, max=max))
                                                         

def genomeAndFitnessList(decodedIndivs, num=10, noUnits=6):
    """Return a list containing a list of of  headers and 
       a sorted list (by fitness)
       of decoded individual genomes passed as a list of
       tuples with genome at [0], fitness at [1], and name at [2].
       Assumes 4 essential variables for homeoUnits"""
    
    'Construct headers'
    headers = ['Fitness', 'IndivID']
    for unit in xrange(noUnits):
        headers.append('U'+str(unit+1)+'-mass')
        headers.append('U'+str(unit+1)+'-visc')
        headers.append('U'+str(unit+1)+'-unis-time')
        headers.append('U'+str(unit+1)+'-maxDev')

    for connIn in xrange(noUnits):
        for connOut in xrange(noUnits):
            headers.append('Conn-W-'+str(connIn+1)+'-to-'+str(connOut+1))
    
    '''Flattens list of tuples including individual genomes and fitnesses to a list of lists.'''
    individuals = []
    for ind in decodedIndivs:        
        b = []
        b.append(ind[2])
        individuals.append(list(ind[1])+b+ind[0])
    
    if len(individuals)< num:
        return [headers,sorted(individuals, key=itemgetter(0), reverse=False)]
    else:
        return [headers,sorted(individuals, key=itemgetter(0), reverse=False)[:num]]

def genomeAndFitnessPrettyPrinter(individuals, noUnits=6):
    """Tabulate individuals with their headers """
    
    'Construct headers'
    headers = ['Fitness', 'IndivID']
    for unit in xrange(noUnits):
        headers.append('U'+str(unit+1)+'-mass')
        headers.append('U'+str(unit+1)+'-visc')
        headers.append('U'+str(unit+1)+'-unis-time')
        headers.append('U'+str(unit+1)+'-maxDev')

    for connIn in xrange(noUnits):
        for connOut in xrange(noUnits):
            headers.append('Conn-W-'+str(connIn+1)+'-to-'+str(connOut+1))

         
    return tabulate(individuals, headers, tablefmt='orgtbl')

def extractGenomeOfIndID(indID, logbookFileWithPath):
    """Extract the genome of individual indID from a DEAP logbook file.
    Return a dictionary with indivId and genome found at respective keys,
    returns 'Not Found' otherwise."""
    genome = {'indivId' : indID, 'genome': "Not Found"}
    logbookFile = open(logbookFileWithPath, 'r')
    logbook = pickle.load(logbookFile)
    logbookFile.close()
    for entry in xrange(len(logbook)):
        try:
            if logbook[entry]['indivId'] == indID:
                genome['genome'] = logbook[entry]['genome']
                break
        except KeyError:
            pass
    return genome        

def extractAllGenomes(logbookFileWithPath):
    """Extracts all genomes of a GA given simulation
       to a set of unique individuals"""
    inds = set()
    logbookFile = open(logbookFileWithPath, 'r')
    logbook = pickle.load(logbookFile)
    logbookFile.close()
    for entry in xrange(len(logbook)):
        try:
            inds.add(tuple(logbook[entry]['genome']))  # convert genome list to tuple for sets
        except KeyError:
            pass
    return inds        

def showGenealogyTree(history):
    """ Show the GA run genealogy as a tree on the basis of the GA run's history obiect"""
    import matplotlib.pyplot as plt
    import networkx

    "Need to recreate the Individual class used by history, otherwise it cannot be unpickled."
    "FIXME: the individual class should be imported from an independent module"    
    creator.create("FitnessMin", base.Fitness, weights=(-1.0,))
    creator.create("Individual", list, fitness=creator.FitnessMin, ID=None)   

    graph = networkx.DiGraph(history.genealogy_tree)
    graph = graph.reverse()     # Make the graph top-down
    node_colors = [history.genealogy_history[i].fitness.values[0] for i in graph]
    node_labels = {}
    #for i in graph:
    #    node_labels[i]=history.genealogy_history[i].ID
    networkx.draw(graph)#, node_color=node_colors, labels = node_labels)
    plt.show()
    

def saveGenomeToCSV(genome, filename):
    "Save a genome to a csv file"    
    try:
        genomeFile = open(filename, 'w')
        genomeWriter = csv.writer(genomeFile, delimiter = ',')
        genomeWriter.writerow(genome)
        genomeFile.close()
    except IOError:
        print "Could not save the genome to", filename

    
if __name__=="__main__":
    main()
    