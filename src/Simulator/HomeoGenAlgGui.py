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
from PyQt4.QtCore import *
from PyQt4.QtGui import * 
import sys
import numpy as np
#import RobotSimulator.WebotsTCPClient
from RobotSimulator.WebotsTCPClient import WebotsTCPClient
from socket import error as SocketError
import os
from math import sqrt
from time import sleep, time, strftime, localtime
from tabulate import tabulate
from Helpers.ExceptionAndDebugClasses import TCPConnectionError, HomeoDebug
from Helpers.ExceptionAndDebugClasses import hDebug
from Helpers.GenomeDecoder import genomeDecoder


class HomeoGASimulation(QWidget):
    '''
    Class managing a Genetic Algorithm simulation, no GUI interface.
    The debugging parameter is a string containing the name of the error
    classes HomeoDebug should print. See HomeoDebug class comment for 
    allowable error classes names. 
    '''
    
    def __init__(self,parent=None, stepSize = 1000, 
                                   popSize=150,
                                   generSize = 1, 
                                   noUnits=6, 
                                   essentParams=4, 
                                   supervisor_host = 'localhost', 
                                   supervisor_port = 10021, 
                                   exp = "initializeBraiten2_2_NoUnisel_Full_GA",
                                   debugging = None):

        "Tell HomeoDebug which error classes it should print "
        if debugging:
            HomeoDebug.addDebugCodes(debugging)
    
        self.popSize = popSize
        self.genomeSize = (noUnits*essentParams)+noUnits**2   
        self.stepsSize = stepSize    
        self.generSize = generSize

        '''
        Create a HomeoQTSimulation object to hold the actual simulation and initialize it.
        Instance HomeoQTSimulation's variable maxRun holds the number of steps the single simulations should be run       
        '''
        
        super(HomeoGASimulation,self).__init__(parent)
        self._simulation = HomeoQtSimulation(experiment=exp)             # instance variable holding the real simulation
        self._simulation.maxRuns=self.stepsSize
        #self._simulation.initializeExperSetup(self.createRandomHomeostatGenome())
        self._supervisor = WebotsTCPClient(ip=supervisor_host, port=supervisor_port)
        

        #=======================================================================
        # "prepare to run the simulation itself in a thread"
        # self._simulThread = SimulationThread()
        # self._simulation.moveToThread(self._simulThread)
        # self._simulThread.started.connect(self._simulation.go)
        #=======================================================================
        
        
        "construct the interface"
        #self.setWindowTitle('Homeo GA simulation')
        #self.setMinimumWidth(400)
 
        #self.buildGui()
        #self.connectSlots()
        #self._supervisor.clientConnect()
        
    def runGaSimulation(self, cxProb = 0.5, mutationProb = 0.2, indivProb = 0.05, tournamentSize = 3):
        try:
            """Initialize and run a complete GA simulation with the specified parameters"""
             
            "1. Create individual types [Homeostat genome], define type of genes, define population"
            toolbox = base.Toolbox()
            
            'GA simulation will minimize fitness (distance from target)'
            creator.create("FitnessMin", base.Fitness, weights=(-1.0,))
            
            'Homeostat genome is a list plus an ID'     
            creator.create("Individual", list, fitness=creator.FitnessMin, ID=None)   
            
            def initIndividual(indivClass, genomeSize, ID = None):
                ind = indivClass(np.random.uniform(0,1) for _ in xrange(genomeSize))
                ind.ID = ID
                return ind
                
            
            #---------- 'Each gene is a uniform random number in [0,1) interval'
            #------------------ toolbox.register("gene", np.random.uniform, 0,1)
            
            'Define how to create an individual'
            toolbox.register("individual", initIndividual, creator.Individual, genomeSize=self.genomeSize, ID = 'DummyID')  
            
            'Population is a list of individual'
            toolbox.register("population", tools.initRepeat, list, toolbox.individual)                             
            
            hDebug('ga',("Population defined.\nIndividual defined with genome size = " + str(self.genomeSize) +"\n"))
            
            "1.1 defining statistics tools"
            stats = tools.Statistics(key=lambda ind: ind.fitness.values)
            stats.register("avg", np.mean)
            stats.register("std", np.std)
            stats.register("min", np.min)
            stats.register("max", np.max)
            
            logbook = tools.Logbook()
            'Record time for naming logbook pickled object and computing time statistics'
            timeStarted = time()
            
            "2. Registering GA operators"
            
            toolbox.register("evaluate", self.evaluateGenomeFitness)
            toolbox.register("mate", tools.cxTwoPoint)
            toolbox.register("mutate", tools.mutFlipBit, indpb=indivProb)
            toolbox.register("select", tools.selTournament, tournsize=tournamentSize)
        
            "3. Run GA simulation"               
            np.random.seed(64)   # For repeatable experiments
            pop = toolbox.population(n=self.popSize)
            gen = 0
            for i, ind in enumerate(pop):
                ind.ID = str(gen)+"-"+(str(i+1))
                
                    
            print("Start of evolution")
            
            # Evaluate the entire population
            print "-- Generation 0 --"
            fitnesses = list(map(toolbox.evaluate, pop))
            for ind, fit in zip(pop, fitnesses):
                ind.fitness.values = fit
                "record the data about the newly evaluated individual's genome in the logbook"
                logbook.record(indivId = ind.ID, fitness = fit, genome = list(ind))
            
            print("  Evaluated %i individuals" % len(pop))
            
            # Begin the evolution
            # Main loop over generations
            for g in xrange(self.generSize):
                print("-- Generation %s --" % str(g+1))
                
                # Select the next generation individuals with previously defined select function 
                offspring = toolbox.select(pop, len(pop))
                # Clone the selected individuals
                offspring = list(map(toolbox.clone, offspring))
            
                # Apply crossover and mutation on the offspring
                hDebug('ga',"Applying crossover")
                mated = 0
                for child1, child2 in zip(offspring[::2], offspring[1::2]):
                    if np.random.uniform() < cxProb:
                        mated += 1
                        toolbox.mate(child1, child2)
                        del child1.fitness.values
                        del child2.fitness.values
                hDebug('ga',str(mated) + " individuals mated")
        
                hDebug('eval', "Now mutating individuals")
                mutants = 0
                for mutant in offspring:                
                    if np.random.uniform() < mutationProb:
                        toolbox.mutate(mutant)
                        del mutant.fitness.values
                        mutants += 1
                hDebug('eval', str(mutants)+ "  mutants generated")
            
                # Evaluate the individuals with an invalid fitness
                # (Fitnesses have become invalid for all mutated and crossed-over individuals) 
                hDebug('eval', "Evaluating individual with invalid fitness")
                invalid_ind = [ind for ind in offspring if not ind.fitness.valid]
                fitnesses = map(toolbox.evaluate, invalid_ind)
                for i, ind in enumerate(invalid_ind):
                    ind.ID = str(g+1) + "-"+str(i+1) 
                for ind, fit in zip(invalid_ind, fitnesses):
                    ind.fitness.values = fit
                    
                    "record the data about the newly evaluated individual's genome in the logbook"
                    logbook.record(indivId = ind.ID, fitness = fit, genome = list(ind))

                
                hDebug('eval', str(len(invalid_ind)) + " individuals evaluated")
                
                # The population is entirely replaced by the offspring
                pop[:] = offspring
                
                # Gather all the fitnesses in one list and print the stats
                #===============================================================
                # fits = [ind.fitness.values[0] for ind in pop]
                # 
                # length = len(pop)
                # mean = sum(fits) / length
                # sum2 = sum(x*x for x in fits)
                # std = abs(sum2 / length - mean**2)**0.5
                # 
                # print("  Min %s" % min(fits))
                # print("  Max %s" % max(fits))
                # print("  Avg %s" % mean)
                # print("  Std %s" % std)
                #===============================================================
                "Compute stats for generation with the statistics object"
                record = stats.compile(pop)
                logbook.record(gen=g+1, evaluations = len(invalid_ind), **record)
                             
            print genomeDecoder(4, tools.selBest(pop,10)[0])
            self.simulationEnvironQuit()
            timeElapsed = timeStarted - time()
            logbook.record(timeElapsed = localtime(timeElapsed))
            logbook.record(finalPop = len(pop), finalIndivs = [(ind.ID, ind.fitness.values, list(ind)) for ind in pop]) 
            print("-- End of (successful) evolution --")
            self.saveLogbook(timeStarted, logbook)
            
            best_ind = tools.selBest(pop, 1)[0]
            print("Best individual is %s, %s" % (best_ind, best_ind.fitness.values))
        except TCPConnectionError as e:
            hDebug("network major",("TCP connection error: \n" + e.value + "Cleaning up and quitting...")) 
            hDebug("network",("Trying to quit webots"))
            self.simulationEnvironQuit()
            
            

    def saveLogbook(self, timeStarted, logbook):
        """Save the logbook for the GA run to a pickled object
           for later analysis. Name the file according to the time
           the simulation started and save it in current directory"""
        logbookFilename = self.getTimeFormattedCompleteFilename(timeStarted, 'Logbook', 'lgb')   
        try:
            dump(logbook, open(logbookFilename, "w"))
        except IOError as e:
            sys.stderr.write("Could not save the logbook to file:" + e + "\n")
           
    def getTimeFormattedCompleteFilename(self,timeStarted, prefix, extension, path = None):
        """ Return a string containing a complete filename (including path)
            that starts with prefix, plus a formatted version of the timeNow string, plus
            the extension.
            Uses the "SimulationData" subdir of the src directory is no path is given.
            TimeStarted is in seconds from the epoch (as returned by time.time())
        """ 
        formattedTime = strftime("%Y-%m-%d-%H-%M-%S", localtime(timeStarted))
        filename = prefix+'-'+formattedTime+ '.' + extension
        if path == None:
            addedPath = 'SimulationsData'
            datafilePath = os.path.join(os.getcwd().split('src/')[0],addedPath)
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
        self.simulationEnvironQuit()
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
        
    def buildGui(self):
        '''
        Build the general GUI for the GA simulation
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

    def createRandomHomeostatGenome(self,genomeSize):
        '''Create a list containing the essential parameters for every
           units in a fully  connected Homeostat and the weights of
           all the connections.
           All values are in the [0,1] range. It is the responsibility of
           the Homeostat- and connections-instantiating method to scale these 
           values to the Units' appropriate ranges.
           
           Basic essential parameters are 5: mass, viscosity,
           uniselectorTiming, and maxDeviation.
           
           (The potentiometer is also an essential parameter, but it is specified as one of the unit's
            connections)
        '''          
        return np.random.uniform(size=genomeSize)

    def simulationEnvironReset(self):
        """Reset webots simulation.
         Do not return from function until the simulation has really exited 
         and the previous tcp/ip socket is no longer valid.
        """
        try:
            self._supervisor._clientSocket.send("R")
            response = self._supervisor._clientSocket.recv(100) 
            hDebug('network',("Reset Webots simulation: received back "+ response + " from server"))
            try:
                while True:
                    self._supervisor._clientSocket.send(".")
                    sleep(0.05)
            except SocketError:
                pass
        except SocketError:
            raise TCPConnectionError("Could not reset Webots simulation")
        
    def simulationEnvironResetPhysics(self):
        "Reset Webots simulation physics"
        try:
            self._supervisor._clientSocket.send("P")
            response = self._supervisor._clientSocket.recv(100) 
            hDebug('network', ("Reset Webots simulation physics: received back %s from server" % response))
        except SocketError:
            raise TCPConnectionError("Could not reset Webots simulation's physics")
            
    
    def simulationEnvironQuit(self):
        "Quit Webots application"
        try:
            self._supervisor._clientSocket.send("Q")
            response = self._supervisor._clientSocket.recv(100) 
            hDebug('newtwork', "Quit Webots: received back " + response + " from server")
        except SocketError:
            hDebug('newtwork',  "Sorry, I lost the connection to Webots and could not could not quit")
        
    def evaluateGenomeFitnessDUMMY(self,genome=None):
        """For GA testing purposes: initialize experiments and homeostats,
         but do not run simulation on Webots"""         
                     
        if genome==None:
            genome=self.createRandomHomeostatGenome(self.genomeSize)
        self._simulation.initializeExperSetup(genome)
        self._supervisor.clientConnect()
        self.simulationEnvironReset()
        self._supervisor.close()
        self._supervisor.clientConnect()
        self._simulation.homeostat.connectUnitsToNetwork()
        self._simulation.maxRuns = self.stepsSize
        "Initialize live data recording and display "
        self._simulation.initializeLiveData()
        #self._simulThread.start()
        finalDis =self.finalDisFromTarget()
        return finalDis,                   # Return a tuple, as required by DEAP
    
    def evaluateGenomeFitness(self,genome=None):
        """Run a simulation for a given number of steps on the given genome.
           Return final distance from target"""
            
        if genome==None:
            genome=self.createRandomHomeostatGenome(self.genomeSize)
        self._simulation.initializeExperSetup(genome)
        hDebug('network', "Trying to connect to supervisor")
        self._supervisor.clientConnect()
        hDebug('network', "Connected")
        hDebug('network', "Resetting Webots")
        self.simulationEnvironReset()
        hDebug('network', "Closing connection to supervisor")
        self._supervisor.close()
        hDebug('network', "Reconnecting to supervisor")
        self._supervisor.clientConnect()
        hDebug('network', "Connecting units to network")
        self._simulation.homeostat.connectUnitsToNetwork()
        self._simulation.maxRuns = self.stepsSize
        "Initialize live data recording and display "
        self._simulation.initializeLiveData()

        #self._simulThread.start()
        timeNow = time()
        hDebug('eval' , "Simulation started at time: " +  str(timeNow))  
        hDebug('eval', ("Now computing exactly " + str(self.stepsSize) + " steps...."))
        for i in xrange(self.stepsSize):
            hDebug('eval', ("Step: "+ str(i+1)+"\n"))
            self._simulation.step()
        #self._simulation.go()
        hDebug('eval', ("Elapsed time in seconds was " + str(round((time() - timeNow),3))))
        finalDis =self.finalDisFromTarget()
        hDebug('eval', ("Final distance from target was: " + str(finalDis)))
        return finalDis,                                       # Return a tuple, as required by DEAP
        
    def finalDisFromTarget(self):
        '''Compute the distance from target by asking the supervisor to
        evaluate the distance between a node with 'DEF' = 'TARGET'
        and the KHEPERA robot'''
        
        self._supervisor._clientSocket.send("D")
        response = float(self._supervisor._clientSocket.recv(100)) 
        return response
        
    def finalDisFromTargetFromFile(self, target):
        """ Compute the distance between robot and target at
        the end of the simulation.
        
        Target must be passed to function as a list of 2 floats (x-coord, y-coord)
        
        Read the robot's final position from the trajectory data file
        
        Assume that the current directory is under a "src" directory
        and that a data folder called 'SimulationsData will exist
        at the same level as "src"
        Assume also that the trajectory data filename will start with 
        the string filenamePattern and will include date and time info in the filename
        so they properly sort in time order
        Get the most recent file fulfilling the criteria
        """ 
        
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
    
if __name__ == '__main__':
    app = QApplication(sys.argv)
    simul = HomeoGASimulation(popSize=10, stepSize=10, generSize = 3, debugging = 'major')
    #simul.runOneGenSimulation()
    simul.runGaSimulation()
    simul.show()
    app.exec_()
