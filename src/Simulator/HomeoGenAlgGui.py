'''
Created on Dec 16, 2014

@author: stefano

Module with classes and functions needed to run a GA simulation of Homeo experiments.
Uses the DEAP GA framework for full GA simulations
'''

from deap import base
from deap import creator
from deap import tools
from deap.tools.mutation import mutFlipBit
from pickle import dump
from Simulator.HomeoQtSimulation import HomeoQtSimulation
from Helpers.SimulationThread import SimulationThread
from Helpers.GenomeDecoder import genomeDecoder, genomePrettyPrinter
from PyQt4.QtCore import *
from PyQt4.QtGui import * 
# import sys
import numpy as np
# import csv
import datetime
from operator import attrgetter
from scoop import futures


#import RobotSimulator.WebotsTCPClient
from RobotSimulator.WebotsTCPClient import WebotsTCPClient
# from socket import error as SocketError
import os
from math import sqrt
from time import time, strftime, localtime, sleep
from tabulate import tabulate
from Helpers.ExceptionAndDebugClasses import TCPConnectionError, HomeoDebug, hDebug
from Helpers.StatsAnalyzer import extractGenomeOfIndID
from SimulatorBackend import SimulatorBackendHOMEO,SimulatorBackendVREP,SimulatorBackendWEBOTS
from threading import Lock
from glob import glob


class HomeoGASimulGUI(QWidget):
    """GUI to GA simulation"""
        
    def __init__(self, parent = None):
        super(HomeoGASimulGUI,self).__init__(parent)
        
        "construct the interface"
        self.setWindowTitle('Homeo GA simulation')
        self.setMinimumWidth(400)
 
        self.buildGui()
        self.connectSlots()
        
        self.gaSimulation = HomeoGASimulation()

    def buildGui(self):
        '''Build the general GUI for the GA simulation
        '''
        
        #mainGui = QDialog()
        'layouts'
        self.controlLayout = QGridLayout()
        self.overallLayout = QVBoxLayout()
        self.textLayout = QVBoxLayout()

        
        'widgets'
        self.initializePopButton = QPushButton("Initialize Population")
        self.noIndividualsSpinBox = QSpinBox()
        self.noIndividualsLabel = QLabel("No of individuals")
        self.startPushButton = QPushButton("Start")
        self.stopPushButton = QPushButton("Stop")
        self.quitPushButton = QPushButton("Quit")
        self.currentFitnessLineEdit = QLineEdit()
        self.currentFitnessLabel = QLabel("Current Fitness")
        self.outputPane = QTextEdit()
        
        self.controlLayout.addWidget(self.initializePopButton,0,0)
        self.controlLayout.addWidget(self.noIndividualsLabel,0,2)
        self.controlLayout.addWidget(self.noIndividualsSpinBox, 0,3)
        self.controlLayout.addWidget(self.currentFitnessLabel, 1,2)
        self.controlLayout.addWidget(self.currentFitnessLineEdit, 1,3)
        self.controlLayout.addWidget(self.startPushButton, 2,0)
        self.controlLayout.addWidget(self.stopPushButton,2,2)
        self.controlLayout.addWidget(self.quitPushButton,2,3)
        
        'text pane'
        self.textLayout.addWidget(self.outputPane)
        
        self.overallLayout.addLayout(self.controlLayout)
        self.overallLayout.addLayout(self.textLayout)
        self.setLayout(self.overallLayout)
        #return mainGui

    def connectSlots(self):
        pass
    
            

class HomeoGASimulation(object):
    '''
    Class managing a Genetic Algorithm simulation, no GUI interface.
    The debugging parameter is a string containing the name of the error
    classes HomeoDebug should print. See HomeoDebug class comment for 
    allowable error classes names. 
    '''
    
    dataDirRoot = '/home/stefano/Documents/Projects/Homeostat/Simulator/Python-port/Homeo/SimulationsData/'
           
    def __init__(self,parent=None, stepsSize = 1000, 
                                   popSize=150,
                                   generSize = 1, 
                                   noUnits=6, 
                                   essentParams=4, 
#                                   exp = "initializeBraiten2_2_NoUnisel_No_Noise_Full_GA",
                                   exp = "initializeBraiten2_2_Full_GA",
                                   noNoise = False,
                                   noUnisel = False,
                                   cxProb = 0.5, 
                                   mutationProb = 0.2, 
                                   indivProb = 0.05, 
                                   tournamentSize = 3,
                                   ID_padding = 3,
                                   clonableGenome = None,
                                   debugging = None,
                                   simulatorBackend = "VREP",
                                   vrepPort = None):
        
        self.worldBeingResetLock = Lock()
        timeElapsed = None
        self._robotName = "Khepera"
        
        if simulatorBackend == "VREP":
            self.simulatorBackend = SimulatorBackendVREP('127.0.0.1', vrepPort, robotName = self._robotName)
        elif simulatorBackend == "WEBOTS":
            self.simulatorBackend = SimulatorBackendWEBOTS('127.0.0.1',
                                                           10021,              # supervisor port
                                                           '127.0.0.1',
                                                           10020,              # robot port
                                                           robotName = self._robotName)              
        elif simulatorBackend == "HOMEO":
            self.simulatorBackend =  SimulatorBackendHOMEO(robotName = self._robotName, lock = self.worldBeingResetLock)

        "Directory to save simulations'data, used to save logbook and history and passed to HomeoQt simulation and other classes"
        self.dataDir = os.path.join(HomeoGASimulation.dataDirRoot,('SimsData-'+strftime("%Y-%m-%d-%H-%M-%S", localtime(time()))))
        try:
            os.mkdir(self.dataDir)
        except OSError:
            print "WARNING: Saving to existing directory", self.dataDir
         
        self.simulatorBackend.setDataDir(self.dataDir)

        'General parameters for the experiment'
        self.experimentParams = {'dataDir' : self.dataDir, 'backendSimulator':self.simulatorBackend, 'noNoise' : noNoise, 'noUnisel' : noUnisel}

        "Tell HomeoDebug which error classes it should print "
        if debugging:
            HomeoDebug.addDebugCodes(debugging)
    
        self.popSize = popSize
        self.genomeSize = (noUnits*essentParams)+noUnits**2   
        self.stepsSize = stepsSize    
        self.generSize = generSize
        self.experiment = exp
        self.cxProb = cxProb 
        self.mutationProb = mutationProb 
        self.indivProb = indivProb 
        self.tournamentSize = tournamentSize
        self.clonableGenome = clonableGenome
        self.stats = tools.Statistics(key=lambda ind: ind.fitness.values)


        self.IDPad = ID_padding
        
        'Statistics, tools, and general record keeping variables'
        self.toolbox = base.Toolbox()
        self.logbook = tools.Logbook()
        self.hof = tools.HallOfFame(10, similar = self.indEq)
        self.hist = tools.History()
        
        '''
        Create a HomeoQTSimulation object to hold the actual simulation and initialize it.
        Instance HomeoQTSimulation's variable maxRun holds the number of steps the single simulations should be run       
        '''
        
        self._simulation = HomeoQtSimulation(experiment=exp, dataDir=self.dataDir)             # instance variable holding the real simulation
        self._simulation.maxRuns=self.stepsSize
        #self._simulation.initializeExperSetup(self.createRandomHomeostatGenome())
        

        #=======================================================================
        # "prepare to run the simulation itself in a thread"
        # self._simulThread = SimulationThread()
        # self._simulation.moveToThread(self._simulThread)
        # self._simulThread.started.connect(self._simulation.go)
        #=======================================================================
        
        "1. Create individual types [Homeostat genome], define type of genes, define population"
            
        'GA simulation will minimize fitness (distance from target)'
        creator.create("FitnessMin", base.Fitness, weights=(-1.0,))
        
        'Homeostat genome is a list plus an ID'     
        creator.create("Individual", list, fitness=creator.FitnessMin, ID=None)   
        
    
                    
        'Register function to create a random individual'
        self.toolbox.register("individual", self.initIndividual, creator.Individual, genomeSize=self.genomeSize, ID = 'DummyID')  
        
        'Register function to create an individual with given genome'
        self.toolbox.register('individualClone', self.initIndividualClone, creator.Individual, self.clonableGenome)
        
        'Population is a list of individual'
        self.toolbox.register("population", tools.initRepeat, list, self.toolbox.individual) 
        
        'Operator to create a list of identical individual of given genome'
        self.toolbox.register('popClones', tools.initRepeat, list, self.toolbox.individualClone)                            
        
#         "Operator to use scoop's parallel processing capabilities"
#         self.toolbox.register('map',futures.map)

        "Operator to use standard (serial) map function"
        self.toolbox.register('map',map)
        
        hDebug('ga',("Population defined.\nIndividual defined with genome size = " + str(self.genomeSize) +"\n"))
        
        "1.1 defining statistics tools"
        self.stats.register("avg", np.mean)
        self.stats.register("std", np.std)
        self.stats.register("min", np.min)
        self.stats.register("max", np.max)
        
        
        "2. Registering GA operators"
        
        self.toolbox.register("evaluate", self.evaluateGenomeFitness)
        #self.toolbox.register("evaluate", self.evaluateGenomeFitnessSUPER_DUMMY)   #For testing purposes

        self.toolbox.register("mate", tools.cxTwoPoint)
        self.toolbox.register("mutate", tools.mutGaussian, mu = 0, sigma = 2, indpb=self.indivProb)            
        self.toolbox.register("select", tools.selTournament, tournsize=self.tournamentSize)
        " FIXME---> NEED TO REMOVE SELECTED INDIVIDUALS FROM ASPIRANTS POOL <-----"
        #self.toolbox.register("select", tools.selBest)
        self.toolbox.decorate("mate", self.checkBounds(0, 1))
        self.toolbox.decorate("mutate", self.checkBounds(0, 1))
        
        "2.1 Define Hall of Fame and History operators"               
        'Decorate the variation operators to insert newly created individuals in the GA history'
        self.toolbox.decorate("mate", self.hist.decorator)
        self.toolbox.decorate("mutate", self.hist.decorator)
        
    def recordGADataToLogbook(self,timeElapsed, pop):
        " Insert general GA simulation parameters into logbook"
        
        " for non cloned population the self._cloname attr is None"
        try:
            clone = self._cloneName
        except AttributeError:
            clone  = 'Random population'
         
        self.logbook.record(date = strftime("%a, %d %b %Y %H:%M:%S",localtime()),
                            exp=self._simulation.currentExperiment,
                            initPop=self.popSize,
                            generations=self.generSize,
                            genomeSize=self.genomeSize,
                            length=self.stepsSize,
                            cxProb=self.cxProb,
                            mutationProb=self.mutationProb,
                            indivProb=self.indivProb,
                            tournSize=self.tournamentSize,
                            timeElapsed = str(datetime.timedelta(seconds=timeElapsed)), 
                            finalPop = len(pop), 
                            finalIndivs = [(ind.ID, ind.fitness.values, list(ind)) for ind in pop],
                            type = self._type,
                            cloneName = clone) 


        #=======================================================================
        # simulationParameters = {'population':self.popSize, 'generations':self.generSize, 
        #     'genomeSize':self.genomeSize, 
        #     'length':self.stepsSize, 
        #     'experiment':self._simulation.currentExperiment, 
        #     'cxProb':self.cxProb, 
        #     'mutationProb':self.mutationProb, 
        #     'indivProb':self.indivProb, 
        #     'tournsize':self.tournamentSize}
        #=======================================================================
        
        #self.logbook.record(GaParameters=simulationParameters)
        #print "The logbook has a record of GaParameters: ", 'GaParameters' in self.logbook


        
        #self._supervisor.clientConnect()
        
    def indEq(self,indA, indB):
        """Two individuals are equals iff they share the same genome"""
        #hDebug('ga', "indA is: " + indA)
        #hDebug('ga', "indB is: " + indB)
        return indA == indB
    
    def checkBounds(self, min, max):
        def decorator(func):
            def wrapper(*args, **kargs):
                offspring = func(*args, **kargs)
                for child in offspring:
                    for i in xrange(len(child)):
                        if child[i] > max:
                            child[i] = max
                        elif child[i] < min:
                            child[i] = min
                return offspring
            return wrapper
        return decorator
    
    def initIndividual(self, indivClass, genomeSize, ID = None):
        "Generate an individual's random genome"
        ind = indivClass(np.random.uniform(0,1) for _ in xrange(genomeSize))
        ind.ID = ID
        return ind
    
    def initIndividualClone(self, indivClass, genome):
        """Generate an individual with given genome.
           Assumes 'genome' is a dictionary with keys indivId and genome"""
        ind = indivClass(genome['genome'])
        ind.ID = genome["indivId"]        
        return ind      

    def generatePopOfClones(self, cloneName =''):
        """Generate a population of identical clones from
           genome stored in self.clonableGenome""" 

        self._type = "clones"
        self._cloneName = cloneName
        return self.toolbox.popClones(n=self.popSize)
          
    def generateRandomPop(self, randomSeed = 64):
        """Generate a population of random individual with given random seed"""
        
        np.random.seed(randomSeed)   # For repeatable experiments
        self._type = 'random'
        return self.toolbox.population(n=self.popSize)

    def runGaSimulation(self, pop):
        """Execute a complete GA run. Could be either over a population of clones
           or over a truly randomly generated  population.
           All parameters (popsize, gen, cxProb, etc.) as well as DEAP-specific tools,
           are stored in class's ivars.
           Save fitness data to logbook"""
          
        'Record time for naming logbook pickled object and computing time statistics'
        timeStarted = time()
        timeElapsed = None        
        try:
            gen = 0
            for i, ind in enumerate(pop):
                ind.ID = str(gen).zfill(self.IDPad)+"-"+str(i+1).zfill(self.IDPad)
                            
                    
            print("Start of evolution")
            
            # Evaluate the entire population
            print "-- Generation 0 --"
            fitnesses = list(self.toolbox.map(self.toolbox.evaluate, pop))
            for ind, fit in zip(pop, fitnesses):
                ind.fitness.values = fit
                "record the data about the newly evaluated individual's genome in the logbook"
                self.logbook.record(indivId = ind.ID, fitness = fit, genome = list(ind))
            self.hof.update(pop)
            self.hist.update(pop)
            print "  Evaluated %i individuals" % len(pop)
            print "  Pop now includes: ",
            for ind in pop:
                print ind.ID+", ",
            print
            #print "  With ID's ", sorted([ind.ID for ind in pop])
            
            # Begin the evolution
            # Main loop over generations
            for g in xrange(self.generSize):
                print("-- Generation %s --" % str(g+1))
                
                # Select the next generation individuals with previously defined select function
                offspring = self.toolbox.select(pop, len(pop))
                # Clone the selected individuals
                offspring = list(map(self.toolbox.clone, offspring))
                print "  Offsprings now include: ",
                for ind in offspring:
                    print ind.ID+", ",
                print

                # Apply crossover and mutation on the offsprings
                hDebug('ga',"Applying crossover")
                mated = 0
                for child1, child2 in zip(offspring[::2], offspring[1::2]):
                    print "Mating %s and %s   --->   " % (child1.ID, child2.ID),
                    if np.random.uniform() < self.cxProb:
                        print "YES!"
                        mated += 1
                        self.toolbox.mate(child1, child2)
                        del child1.fitness.values
                        del child2.fitness.values
                    else:
                        print "NO"
                hDebug('ga',str(mated) + " individuals mated")
        
                hDebug('eval,ga', "Now mutating individuals")
                mutants = 0
                for mutant in offspring:                
                    if np.random.uniform() < self.mutationProb:
                        self.toolbox.mutate(mutant)
                        del mutant.fitness.values
                        mutants += 1
                hDebug('eval ga', str(mutants)+ "  mutants generated")
            
                # Evaluate the individuals with an invalid fitness
                # (Fitnesses have become invalid for all mutated and crossed-over individuals) 
                hDebug('eval', "Evaluating individual with invalid fitness")
                invalid_ind = [ind for ind in offspring if not ind.fitness.valid]
               
                "Change the ID's of the invalid ind's" 
                for i, ind in enumerate(invalid_ind):
                    #print "The old ind's ID was: ", ind.ID
                    ind.ID = str(g+1).zfill(self.IDPad) + "-"+str(i+1).zfill(self.IDPad) 
                    #print "Now changed to: ", ind.ID
    
                'Re-evaluate'
                fitnesses = map(self.toolbox.evaluate, invalid_ind)
                for ind, fit in zip(invalid_ind, fitnesses):
                    ind.fitness.values = fit
                    
                    "record the data about the newly evaluated individual's genome in the logbook"
                    self.logbook.record(indivId = ind.ID, fitness = fit, genome = list(ind))
                    #print "direct ind's name is %s and fitness is: %.2f" %(ind.ID, ind.fitness.values[0])

                hDebug('eval', str(len(invalid_ind)) + " individuals evaluated")
                
                # The population is entirely replaced by the offspring
                pop[:] = offspring
                print "  Pop now includes: ",
                for ind in pop:
                    print ind.ID+", ",
                print

                "Compute stats for generation with the statistics object"
                record = self.stats.compile(pop)
                self.logbook.record(gen=g+1, evaluations = len(invalid_ind), **record)
                self.hof.update(pop)
                "save logbook and history after each generation"
                timeElapsed = time() - timeStarted 
                self.saveLogbook(pop, timeElapsed,timeStarted)
                self.saveHistory(timeStarted)
                #self.hist.update(pop)

                #print "   Generation " + str(g+1) + " with ID's: ", sorted([ind.ID for ind in pop])
                             
            #print genomeDecoder(4, tools.selBest(pop,10)[0])
            #self.simulationEnvironQuit()
            timeElapsed = time() - timeStarted 
            print("-- End of (successful) evolution --")
            print "Total time elapsed: ", str(datetime.timedelta(seconds=timeElapsed))
            print("-- Cleaning up trajectory files --")
            self.cleanUpTrajFiles()
            'Record general GA run info to logbook and save logbook and history'
            self.saveLogbook(pop, timeElapsed, timeStarted)
            self.saveHistory(timeStarted)
            
            self.simulatorBackend.quit()
            
            #best_ind = tools.selBest(pop, 1)[0]
            #print("Best individual is %s, %s" % (best_ind, best_ind.fitness.values))
        
        except TCPConnectionError as e:
            hDebug("network major",("TCP connection error: \n" + e.value + "Cleaning up and quitting...")) 
            hDebug("network",("Trying to quit simulation environment" % self.simulatorBackend))
            self.simulatorBackend.quit()
        #=======================================================================
        # except VREP_Error as e:
        #     "Try to close connection to V-REP"
        #
        #     "FIXME : TO DO"
        # finally: 
        #     "release V-rep and/or Webots connections if we crashed"
        #     
        #     "FIXME: TO DO"
        #=======================================================================

        except:
            "Something bad happened: Check if we did anything and save logbook and history of work done so far and re-raise."
            if timeElapsed is not None:
                self.saveLogbook(pop, timeElapsed, timeStarted)
                self.saveHistory(timeStarted)
            else: 
                'TimeElapsed still unbound: we did not even get started.'
                pass
            raise
        
            

    def saveLogbook(self, pop, timeElapsed, timeStarted):
        """Insert general info about the GA run into logbook
           and the logbook for the GA run to a pickled object
           for later analysis. Name the file according to the time
           the simulation started and save it in current directory.
           Overwrite existing file is necessary, i.e. update with 
           the latest version 
           """
        self.recordGADataToLogbook(timeElapsed, pop)   
        logbookFilename = self.getTimeFormattedCompleteFilename(timeStarted, 'Logbook', 'lgb')
        try:
            dump(self.logbook, open(logbookFilename, "w"))
        except IOError: #as e:
            #sys.stderr.write("Could not save the logbook to file:" + e.__str__ + "\n")
            print "Could not save the logbook to file:" #, e.__str__ 

    def saveHistory(self, timeStarted):
        """Save the history for the GA run to a pickled object
           for later analysis. Name the file according to the time
           the simulation started and save it in current directory"""
        historyFilename = self.getTimeFormattedCompleteFilename(timeStarted, 'History', 'hist')
        try:
            dump(self.hist, open(historyFilename, "w"))
        except IOError: #as e:
            #sys.stderr.write("Could not save the logbook to file:" + e.__str__ + "\n")
            print "Could not save the history to file:" #, e.__str__ 
    
    
    def getTimeFormattedCompleteFilename(self,timeStarted, prefix, extension, path = None):
        """ Return a string containing a complete filename (including path)
            that starts with prefix, plus a formatted version of the timeNow string, plus
            the extension.
            Create a folder under the globally defined dataDir if no path is given.
            TimeStarted is in seconds from the epoch (as returned by time.time())
        """ 
        formattedTime = strftime("%Y-%m-%d-%H-%M-%S", localtime(timeStarted))
        filename = prefix+'-'+formattedTime+ '.' + extension
        if path == None:
            datafilePath = self.dataDir
        else: datafilePath = path
        return os.path.join(datafilePath, filename)
         
      
                   
    def runOneGenSimulation(self):
        """Manually run a one generation of a GA experiment .
           Record fitness and genome for each individual to file"""
        
        fullPathstatsFilename = self.getTimeFormattedCompleteFilename(time(), 'Ga_Statistics', 'txt')       
        statsFile = open(fullPathstatsFilename,'w')
        self.results = [] 
        population = []
        for i in xrange(self.popSize):
            population.append(self.createRandomHomeostatGenome(self.genomeSize))  
        timeGen = time()               
        for runNumber, indiv in enumerate(population):
            timeInd = time()
            runResults = []
            runResults.append(str(runNumber+1))
            runResults.append(round((self.evaluateGenomeFitness(genome = indiv)[0]),4))
            runResults.append(str(round((time() - timeInd),2)))
            for gene in indiv:
                runResults.append(gene)
            for i in runResults:
                statsFile.write(str(i)+'\t')
            self.results.append(runResults)
            statsFile.write('\n')
            statsFile.flush()
            os.fsync(statsFile)
            self.simulatorBackend.quit()
        statsFile.close()
        headers = ['Run', 'Final distance','Time in secs']
        for i in xrange(len(population[0])):
            headers.append('Gene'+str(i+1))
        hDebug('eval',(tabulate(self.results, headers, tablefmt='orgtbl')))
        hDebug('eval',( "Total time for generation was: "+ str(round((time() - timeGen),2))))
        
        
            
        #=======================================================================
        # "debugging code"
        # print "Simulation starting....."
        # result = self.finalDisFromTarget(simTarget)
        # print "Final distance from target was: %f" % result
        # print "......simulation over."
        # 
        # "end debugging code"
        #=======================================================================
        

    def createRandomHomeostatGenome(self,genomeSize):
        '''Create a list containing the essential parameters for every
           units in a fully  connected Homeostat and the weights of
           all the connections.
           All values are in the [0,1] range. It is the responsibility of
           the Homeostat- and connections-instantiating method to scale these 
           values to the Units' appropriate ranges.
           
           Basic essential parameters are 4: mass, viscosity,
           uniselectorTiming, and maxDeviation.
           
           (The potentiometer is also an essential parameter, but it is specified as one of the unit's
            connections)
        '''          
        return np.random.uniform(size=genomeSize)
    
        
    def evaluateGenomeFitnessDUMMY(self,genome=None):
        """For GA testing purposes: initialize experiments and homeostats,
           but do not run simulation on Webots, return a normally distributed 
           random fitness instead"""         
                     
        if genome==None:
            genome=self.createRandomHomeostatGenome(self.genomeSize)
        params = {'homeoGenome':genome, 'dataDir' : self.dataDir}
        self._simulation.initializeExperSetup(params)
        self.simulatorBackend.connect()
        self.simulatorBackend.reset()
        self.simulatorBackend.close()
        self.simulatorBackend.connect()
        self._simulation.homeostat.connectUnitsToNetwork()
        self._simulation.maxRuns = self.stepsSize
        "Initialize live data recording and display "
        self._simulation.initializeLiveData()
        #self._simulThread.start()
        finalDis =self.finalDisFromTarget()
        return finalDis,                   # Return a tuple, as required by DEAP

    def evaluateGenomeFitnessSUPER_DUMMY(self,genome=None):
        """For GA testing purposes: do not initialize experiments and homeostats,
           and do NOT run simulation on Webots: 
           just return a normally distributed random fitness instead"""         
                     
        #=======================================================================
        # if genome==None:
        #     genome=self.createRandomHomeostatGenome(self.genomeSize)
        # self._simulation.initializeExperSetup(genome)
        # self._supervisor.clientConnect()
        # self.simulationEnvironReset()
        # self._supervisor.close()
        # self._supervisor.clientConnect()
        # self._simulation.homeostat.connectUnitsToNetwork()
        # self._simulation.maxRuns = self.stepsSize
        # "Initialize live data recording and display "
        # self._simulation.initializeLiveData()
        #=======================================================================
        #self._simulThread.start()
        finalDis = np.random.normal(loc=3, scale = 3)
        return finalDis,                   # Return a tuple, as required by DEAP (vide trailing comma)
    
    def evaluateGenomeFitness(self,genome=None):
        """Run a simulation for a given number of steps on the given genome.
           Return final distance from target"""
            
        if genome==None:
            genome=self.createRandomHomeostatGenome(self.genomeSize)
                    
        if self.simulatorBackend.name == "VREP":
            self.simulatorBackend.connect()
        self.experimentParams['homeoGenome']= genome
        self._simulation.initializeExperSetup(**self.experimentParams)

        "testing"
#         sleep(1)
        "end testing"
        
        hDebug('network', "Trying to connect to supervisor")
#         self._supervisor.clientConnect()
        self.simulatorBackend.connect()
        hDebug('network', "Connected")
        hDebug('network', "Resetting Webots")
        self.simulatorBackend.reset()
        if self.simulatorBackend.name == "HOMEO":
            print " recreating experimental setup just for HOMEO backend"
            self._simulation.initializeExperSetup(**self.experimentParams)
        hDebug('network', "Closing connection to supervisor")
        self.simulatorBackend.close()
#         self._supervisor.close()
        hDebug('network', "Reconnecting to supervisor")
#         self._supervisor.clientConnect()
        self.simulatorBackend.connect()
        hDebug('network', "Connecting units to network")
        #
        #
        self.simulatorBackend.setRobotModel(genome.ID)
        
        "testing"
#         sleep(1)
        "end testing"
        
        self._simulation.homeostat.connectUnitsToNetwork()
        self._simulation.maxRuns = self.stepsSize
        "Initialize live data recording and display "
        self._simulation.initializeLiveData()

        #self._simulThread.start()
        timeNow = time()
        hDebug('eval' , "Simulation started at time: " +  str(timeNow))  
        hDebug('eval', ("Now computing exactly " + str(self.stepsSize) + " steps...."))
        self.worldBeingResetLock.acquire()
#         for sensor in self.simulatorBackend.world.allBodies[self._robotName].sensors.values():
#             print  sensor.shape.pos
        print "Lock ACQUIRED by evaluateGenomeFitness"
        for i in xrange(self.stepsSize):
            hDebug('eval', ("Step: "+ str(i+1)+"\n"))
            print "step: ",i+1
            self._simulation.step()
        #self._simulation.go()
        self.worldBeingResetLock.release()
        print "Lock RELEASED by evaluateGenomeFitness"
        hDebug('eval', ("Elapsed time in seconds was " + str(round((time() - timeNow),3))))
        finalDis =self.simulatorBackend.finalDisFromTarget()
        hDebug('eval', ("Final distance from target was: " + str(finalDis)))
        print " Evaluation for model %s took time: %s with fitness %.5f" %(genome.ID, str(datetime.timedelta(seconds=time()- timeNow)), finalDis)
        return finalDis,                                       # Return a tuple, as required by DEAP
        
    def finalDisFromTargetFromFile(self, target):
        """Compute the distance between robot and target at
        the end of the simulation.
        
        Target must be passed to function as a list of 2 floats (x-coord, y-coord)
        
        Read the robot's final position from the trajectory data file
        
        Assume that the current directory is under a "src" directory
        and that a data folder called 'SimulationsData will exist
        at the same level as "src"
        Assume also that the trajectory data filename will start with 
        the string filenamePattern and will include date and time info in the filename
        so they properly sort in time order
        Get the most recent file fulfilling the criteria"""

        
        addedPath = 'SimulationsData'
        datafilePath = os.path.join(os.getcwd().split('src/')[0],addedPath)
        fileNamepattern = 'trajectoryData'
        try:
            trajDataFilename = max([ f for f in os.listdir(datafilePath) if f.startswith(fileNamepattern) ])
        except ValueError:
            print "The file I tried to open was:", os.path.join(datafilePath, max([ f for f in os.listdir(datafilePath) if f.startswith(fileNamepattern)]))
            messageBox =  QMessageBox.warning(self, 'No data file', 'There are no trajectory data to visualize', QMessageBox.Cancel)
            messageBox.show()
        fullPathTrajFilename = os.path.join(datafilePath, trajDataFilename)
        robotFinalPos =os.popen("tail --lines=1 " + fullPathTrajFilename).read()
        robotX = float(robotFinalPos.split('\t')[0])
        robotY = float(robotFinalPos.split('\t')[1])
        #=======================================================================
        # print "Robot's final position is at x: %f\t y:%d" % (robotX,robotY)
        # print "Target is at x: %f\t y: %f" % (target[0],target[1])
        # print "Distance to target is: ", sqrt((target[0]-robotX)**2 + (target[1]-robotY)**2)
        #=======================================================================
        return sqrt((target[0]-robotX)**2 + (target[1]-robotY)**2)
    
    def cleanUpTrajFiles(self):
        "Remove all files not related to specific homeostat models from dataDir"
        unspecificFileList = glob(self.dataDir+"/*-Unspecified.traj")
        for f in unspecificFileList:
            os.remove(f)
    
def selTournamentRemove(individuals, k, tournsize):
    """Select *k* individuals from the input *individuals* using *k*
    tournaments of *tournsize* individuals and remove them from the initial list.
    The list returned contains references to the input *individuals*.
    
    :param individuals: A list of individuals to select from.
    :param k: The number of individuals to select.
    :param tournsize: The number of individuals participating in each tournament.
    :returns: A list of selected individuals.
    
    This function uses the :func:`~random.choice` function from the python base
    :mod:`random` module.
    """
    chosen = []
    for i in xrange(k):
        aspirants = tools.selRandom(individuals, tournsize)
        chosen.append(max(aspirants, key=attrgetter("fitness")))
        individuals.remove(max(aspirants, key=attrgetter("fitness")))
    return chosen
    
                
if __name__ == '__main__':
    #app = QApplication(sys.argv)
    #simulGUI = HomeoGASimulGUI()
    logD = "/home/stefano/Documents/Projects/Homeostat/Simulator/Python-port/Homeo/SimulationsData/SimsData-2015-03-07-11-27-23"
    logL = 'Logbook-2015-03-07-11-27-23.lgb'
    id = '003-031'
    logF = os.path.join(logD,logL)
    genome = extractGenomeOfIndID(id,logF)
#    print [round(x,3) for x in genome['genome']]
#    print [round(x,3) for x in genomeDecoder(6, genome['genome'])]
    #print genomePrettyPrinter(6, genomeDecoder(6, genome['genome']))
#     simul = HomeoGASimulation(popSize=3, stepsSize=100, generSize = 0,  clonableGenome = genome, debugging = 'ga major', simulatorBackend = "WEBOTS")
    simul = HomeoGASimulation(popSize=1000, stepsSize=50, generSize = 10,  clonableGenome = genome, debugging = 'network', simulatorBackend = "HOMEO", noUnisel = True, noNoise = True)
    #simul.test()
    #simul.runOneGenSimulation()
#     simul.runGaSimulation(simul.generatePopOfClones(cloneName='003-031'))
    simul.runGaSimulation(simul.generateRandomPop())
    #simul.showGenealogyTree(simul.hist, simul.toolbox)
    #simulGUI.show()
    #app.exec_()
