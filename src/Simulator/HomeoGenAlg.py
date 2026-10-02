'''
Created on Dec 16, 2014
Split out of HomeoGenAlgGui.py: Oct 2026

@author: stefano

The GA engine for Homeo experiments, with no GUI: HomeoGASimulation and the
worker functions used for parallel evaluation.  Uses the DEAP GA framework.

It lives apart from the GUI (Simulator/HomeoGenAlgGui.py) so that a headless
GA run does not import PyQt5's widgets.  HomeoGenAlgGui re-exports the names
defined here, so existing imports from it keep working.
'''

from deap import base
from deap import creator
from deap import tools
from pickle import dump
from Simulator.HomeoQtSimulation import HomeoQtSimulation
import Simulator.HomeoExperiments
import numpy as np
import random
import re
import zlib
from contextlib import contextmanager
from Core.HomeoJIT import seed_jit_rng
import datetime
from operator import attrgetter
import multiprocessing
import os
import math
from time import time, strftime, localtime
from tabulate import tabulate
from Helpers.ExceptionAndDebugClasses import TCPConnectionError, HomeoDebug, hDebug
from Simulator.SimulatorBackend import SimulatorBackendHOMEO,SimulatorBackendVREP,SimulatorBackendWEBOTS
from threading import Lock
from glob import glob


# --- Reproducible evaluations ---
#
# A GA run draws from four random streams: numpy and Python's `random` in the
# parent (the initial population; DEAP's selection, crossover and mutation; the
# crossover/mutation coin flips), and, during each fitness evaluation, numpy
# (the homeostat's initial values as it is built) and numba's own state (all the
# noise while it runs).  Each evaluation gets its own seed, `evalSeed`, derived
# from the GA's seed by the run's noise scheme and attached to the individual
# before it is evaluated, so that it travels to a pool worker with the genome
# and is logged with the fitness it produced.  The evaluation seeds its streams
# from it; the serial path then restores the parent's numpy and `random` states,
# so evaluations never shift the GA's own draws and a run gives the same result
# with any number of workers.

NOISE_SCHEMES = ('individual', 'genome', 'generation')
"""How evaluations get their noise -- a research choice, so it is a GA parameter:
   'individual'  each evaluation its own sequence, keyed by the individual's ID:
                 independent noise per evaluation, as before seeding existed;
   'genome'      keyed by the genome's exact values: identical genomes face the
                 same noise and score the same;
   'generation'  keyed by the generation: everyone in a generation faces the
                 same noise (common random numbers)."""


def _id_key(ID):
    "Integers identifying an individual's ID: (generation, index) for 'GGG-III' IDs"
    m = re.fullmatch(r'(\d+)-(\d+)', str(ID))
    if m:
        return [0, int(m.group(1)), int(m.group(2))]
    return [1, zlib.crc32(str(ID).encode())]


def evaluation_seed(gaSeed, noiseScheme, ind, generation):
    """The seed for evaluating individual `ind`, created in `generation`, in a GA
       run seeded with `gaSeed` (a non-negative int), under `noiseScheme`.

       Derived through numpy's SeedSequence, so it is the same on every machine
       and Python version (unlike hash()), and fits np.random.seed."""
    if noiseScheme == 'individual':
        key = [0] + _id_key(ind.ID)
    elif noiseScheme == 'genome':
        genes = np.asarray(list(ind), dtype=np.float64)
        key = [1] + np.frombuffer(genes.tobytes(), dtype=np.uint32).tolist()
    elif noiseScheme == 'generation':
        key = [2, int(generation)]
    else:
        raise ValueError("noiseScheme must be one of %s, got %r" % (NOISE_SCHEMES, noiseScheme))
    return int(np.random.SeedSequence([int(gaSeed)] + key).generate_state(1)[0])


def seed_evaluation(seed):
    """Seed every random stream a fitness evaluation draws from."""
    np.random.seed(seed)       # numpy at Python level: building the homeostat
    seed_jit_rng(seed)         # numba's own state: the noise while it runs
    random.seed(seed)          # Python's random: HomeoNoise's non-JIT path


@contextmanager
def seeded_evaluation(seed):
    """Run the enclosed evaluation from `seed`, then give the caller back its
       numpy and Python `random` states.  A seed of None changes nothing (an
       individual created outside a GA run has none).  Numba's state is not
       restored: the GA itself never draws from it."""
    if seed is None:
        yield
        return
    numpy_state = np.random.get_state()
    random_state = random.getstate()
    seed_evaluation(seed)
    try:
        yield
    finally:
        np.random.set_state(numpy_state)
        random.setstate(random_state)


# --- Module-level configuration for multiprocessing workers ---
# Set by _init_worker() in each spawned worker process.
_worker_config = {}


def _init_worker(config):
    """Pool initializer: copy config into the module-level dict.

    Also nullifies the inherited pyglet GL context so that
    _has_gl_context() in KheperaSimulator correctly returns False.
    Without this, forkserver workers inherit a stale context reference
    from the parent process, causing shader compilation to fail when
    KheperaWheel tries to create pyglet shapes.
    """
    global _worker_config
    _worker_config = config

    # Clear stale pyglet GL context inherited from the parent process
    try:
        import pyglet.gl
        pyglet.gl.current_context = None
    except Exception:
        pass


def _evaluate_genome_worker(genome):
    """Pool entry point: evaluate `genome` from its evalSeed (see seeded_evaluation)."""
    with seeded_evaluation(getattr(genome, 'evalSeed', None)):
        return _run_genome_evaluation(genome)


def _run_genome_evaluation(genome):
    """Standalone fitness evaluation for use with multiprocessing.Pool.

    Creates its own SimulatorBackendHOMEO and HomeoQtSimulation per call,
    avoiding all shared state. Reads experiment parameters from the
    module-level _worker_config dict (set by _init_worker at pool start).
    """
    cfg = _worker_config
    experiment = cfg['experiment']
    stepsSize = cfg['stepsSize']
    dataDir = cfg['dataDir']

    backend = SimulatorBackendHOMEO(robotName='Khepera', lock=None)
    backend.setDataDir(dataDir)

    sim = HomeoQtSimulation(experiment=experiment, dataDir=dataDir)
    sim.maxRuns = stepsSize

    params = dict(cfg['experimentParams'])
    params['homeoGenome'] = genome
    params['backendSimulator'] = backend

    sim.initializeExperSetup(
        message="Building Homeostat from genome %s" % genome.ID,
        **params)

    backend.connect()
    backend.reset()
    sim.initializeExperSetup(
        message="Rebuilding world after reset", **params)
    backend.close()
    backend.connect()

    backend.setRobotModel(genome.ID)
    sim.homeostat.connectUnitsToNetwork()
    sim.maxRuns = stepsSize
    sim.initializeLiveData()

    # Enable headless/JIT optimizations for GA evaluation
    hom = sim.homeostat
    hom._headless = True
    hom._collectsData = False
    hom._slowingFactor = 0
    for u in hom.homeoUnits:
        u._headless = True

    # Compute actual tick count.  stepsSize means "simulated seconds".
    # When units have dt_fast < 1, more ticks are needed to cover the
    # same simulated time.  Use the smallest dt_fast across all evolved
    # units (those with the attribute) to determine the conversion.
    min_dt_fast = 1.0
    for u in hom.homeoUnits:
        dt = getattr(u, '_dt_fast', 1.0)
        if dt < min_dt_fast:
            min_dt_fast = dt
    actual_ticks = int(math.ceil(stepsSize / min_dt_fast))

    timeNow = time()
    for i in range(actual_ticks):
        sim.step()
    backend.kheperaSimulation.saveTrajectory()   # close (and flush) the .traj file

    finalDis = backend.finalDisFromTarget()
    fitness = cfg.get('fitnessSign', 1) * finalDis
    print(" Evaluation for model %s (%d ticks, min_dt=%.2f) took time: %s with fitness %.5f" % (
        genome.ID, actual_ticks, min_dt_fast,
        str(datetime.timedelta(seconds=time() - timeNow)), fitness))
    return fitness,


class HomeoGASimulation(object):
    '''
    Class managing a Genetic Algorithm simulation, no GUI interface.
    The debugging parameter is a string containing the name of the error
    classes HomeoDebug should print. See HomeoDebug class comment for 
    allowable error classes names. 
    '''
    
    from Helpers.General_Helper_Functions import simulations_data_dir as _sdd
    dataDirRoot = _sdd()
           
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
                                   vrepPort = None,
                                   nWorkers = 1,
                                   noiseScheme = 'individual'):
        
        if noiseScheme not in NOISE_SCHEMES:
            raise ValueError("noiseScheme must be one of %s, got %r" % (NOISE_SCHEMES, noiseScheme))
        self.noiseScheme = noiseScheme
        self.randomSeed = None          # set by generateRandomPop / generatePopOfClones
        self.worldBeingResetLock = Lock()
        self._stopRequested = False
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
        else:
            self.simulatorBackend = None

        "Directory to save simulations'data, used to save logbook and history and passed to HomeoQt simulation and other classes"
        self.dataDir = os.path.join(HomeoGASimulation.dataDirRoot,('SimsData-'+strftime("%Y-%m-%d-%H-%M-%S", localtime(time()))))
        try:
            os.makedirs(self.dataDir)
        except OSError:
            print("WARNING: Saving to existing directory", self.dataDir)

        if self.simulatorBackend is not None:
            self.simulatorBackend.setDataDir(self.dataDir)

        'General parameters for the experiment'
        self.experimentParams = {'dataDir' : self.dataDir, 'backendSimulator':self.simulatorBackend, 'noNoise' : noNoise, 'noUnisel' : noUnisel}

        "Tell HomeoDebug which error classes it should print "
        if debugging:
            HomeoDebug.addDebugCodes(debugging)
    
        self.popSize = popSize
        self.noUnits = noUnits
        exp_func = getattr(Simulator.HomeoExperiments, exp)
        self.noEvolvedUnits = getattr(exp_func, 'noEvolvedUnits', noUnits)
        self.fitnessSign = getattr(exp_func, 'fitnessSign', 1)
        self.genomeSize = getattr(exp_func, 'genomeSize',
                                   (self.noEvolvedUnits * essentParams) + (self.noEvolvedUnits * noUnits))
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
        if not hasattr(creator, 'FitnessMin'):
            creator.create("FitnessMin", base.Fitness, weights=(-1.0,))

        'Homeostat genome is a list plus an ID'
        if not hasattr(creator, 'Individual'):
            creator.create("Individual", list, fitness=creator.FitnessMin, ID=None)   
        
    
                    
        'Register function to create a random individual'
        self.toolbox.register("individual", self.initIndividual, creator.Individual, genomeSize=self.genomeSize, ID = 'DummyID')  
        
        'Register function to create an individual with given genome'
        self.toolbox.register('individualClone', self.initIndividualClone, creator.Individual, self.clonableGenome)
        
        'Population is a list of individual'
        self.toolbox.register("population", tools.initRepeat, list, self.toolbox.individual) 
        
        'Operator to create a list of identical individual of given genome'
        self.toolbox.register('popClones', tools.initRepeat, list, self.toolbox.individualClone)                            
        
        "Register map and evaluate functions (parallel or serial)"
        self.nWorkers = nWorkers
        self._pool = None

        if nWorkers > 1 and simulatorBackend == "HOMEO":
            config = {
                'experiment': exp,
                'experimentParams': {
                    'dataDir': self.dataDir,
                    'noNoise': noNoise,
                    'noUnisel': noUnisel,
                },
                'stepsSize': stepsSize,
                'dataDir': self.dataDir,
                'fitnessSign': self.fitnessSign,
            }

            ctx = multiprocessing.get_context('forkserver')
            self._pool = ctx.Pool(
                nWorkers, initializer=_init_worker, initargs=(config,))
            self.toolbox.register('map', self._pool.map)
            self.toolbox.register("evaluate", _evaluate_genome_worker)
            print("Using %d worker processes for parallel evaluation" % nWorkers)
        else:
            self.toolbox.register('map', map)
            self.toolbox.register("evaluate", self.evaluateGenomeFitnessSeeded)

        hDebug('ga',("Population defined.\nIndividual defined with genome size = " + str(self.genomeSize) +"\n"))

        "1.1 defining statistics tools"
        self.stats.register("avg", np.mean)
        self.stats.register("std", np.std)
        self.stats.register("min", np.min)
        self.stats.register("max", np.max)

        self.toolbox.register("mate", tools.cxTwoPoint)
        self.toolbox.register("mutate", tools.mutGaussian, mu = 0, sigma = 0.2, indpb=self.indivProb)            
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
                            noEvolvedUnits=self.noEvolvedUnits,
                            noUnits=self.noUnits,
                            length=self.stepsSize,
                            cxProb=self.cxProb,
                            mutationProb=self.mutationProb,
                            indivProb=self.indivProb,
                            tournSize=self.tournamentSize,
                            fitnessSign=self.fitnessSign,
                            timeElapsed = str(datetime.timedelta(seconds=timeElapsed)),
                            finalPop = len(pop),
                            finalIndivs = [(ind.ID, ind.fitness.values, list(ind)) for ind in pop],
                            type = self._type,
                            cloneName = clone,
                            randomSeed = self.randomSeed,
                            noiseScheme = self.noiseScheme) 


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
                    for i in range(len(child)):
                        if child[i] > max:
                            child[i] = max
                        elif child[i] < min:
                            child[i] = min
                return offspring
            return wrapper
        return decorator
    
    def initIndividual(self, indivClass, genomeSize, ID = None):
        "Generate an individual's random genome"
        ind = indivClass(np.random.uniform(0,1) for _ in range(genomeSize))
        ind.ID = ID
        return ind
    
    def initIndividualClone(self, indivClass, genome):
        """Generate an individual with given genome.
           Assumes 'genome' is a dictionary with keys indivId, fitness, and genome"""
        ind = indivClass(genome['genome'])
        ind.ID = genome["indivId"]
        if 'fitness' in genome and genome['fitness'] is not None:
            ind.fitness.values = genome['fitness']
        return ind

    def seedGA(self, randomSeed):
        """Seed the GA's own random streams -- numpy (initial population,
           crossover/mutation coin flips) and Python's random (DEAP's selection,
           crossover and mutation) -- and remember the seed: every evaluation's
           seed is derived from it."""
        self.randomSeed = int(randomSeed)
        np.random.seed(self.randomSeed)
        random.seed(self.randomSeed)

    def generatePopOfClones(self, cloneName ='', randomSeed = 64):
        """Generate a population of identical clones from
           genome stored in self.clonableGenome""" 

        self.seedGA(randomSeed)
        self._type = "clones"
        self._cloneName = cloneName
        return self.toolbox.popClones(n=self.popSize)
          
    def generateRandomPop(self, randomSeed = 64):
        """Generate a population of random individual with given random seed"""
        
        self.seedGA(randomSeed)   # For repeatable experiments
        self._type = 'random'
        return self.toolbox.population(n=self.popSize)

    def runGaSimulation(self, pop, progressCallback=None):
        """Execute a complete GA run. Could be either over a population of clones
           or over a truly randomly generated  population.
           All parameters (popsize, gen, cxProb, etc.) as well as DEAP-specific tools,
           are stored in class's ivars.
           Save fitness data to logbook.

           If progressCallback is provided it is called after generation 0 and
           after each subsequent generation with (gen, record, bestFitness).
           Set self._stopRequested = True to interrupt the run cleanly."""

        'Record time for naming logbook pickled object and computing time statistics'
        self._stopRequested = False
        timeStarted = time()
        timeElapsed = None
        if self.randomSeed is None:
            print("No GA seed set (population not made by generateRandomPop or "
                  "generatePopOfClones): seeding with 64")
            self.seedGA(64)
        try:
            gen = 0
            for i, ind in enumerate(pop):
                ind.ID = str(gen).zfill(self.IDPad)+"-"+str(i+1).zfill(self.IDPad)
            self.assignEvalSeeds(pop, gen)


            print("Start of evolution")

            # Evaluate the entire population
            print("-- Generation 0 --")
            fitnesses = list(self.toolbox.map(self.toolbox.evaluate, pop))
            for ind, fit in zip(pop, fitnesses):
                ind.fitness.values = fit
                "record the data about the newly evaluated individual's genome in the logbook"
                self.logbook.record(indivId = ind.ID, fitness = fit, genome = list(ind),
                                    evalSeed = ind.evalSeed)
            self.hof.update(pop)
            self.hist.update(pop)
            print("  Evaluated %i individuals" % len(pop))
            print("  Pop now includes: ", end="")
            for ind in pop:
                print(ind.ID+", ", end="")
            print()

            # Report gen-0 progress
            if progressCallback:
                record0 = self.stats.compile(pop)
                self.logbook.record(gen=0, evaluations=len(pop), **record0)
                progressCallback(0, record0, self.hof[0].fitness.values[0])

            #print "  With ID's ", sorted([ind.ID for ind in pop])

            # Begin the evolution
            # Main loop over generations
            for g in range(self.generSize):
                if self._stopRequested:
                    break

                print("-- Generation %s --" % str(g+1))

                # Select the next generation individuals with previously defined select function
                offspring = self.toolbox.select(pop, len(pop))
                # Clone the selected individuals
                offspring = list(map(self.toolbox.clone, offspring))
                print("  Offsprings now include: ", end="")
                for ind in offspring:
                    print(ind.ID+", ", end="")
                print()

                # Apply crossover and mutation on the offsprings
                hDebug('ga',"Applying crossover")
                mated = 0
                for child1, child2 in zip(offspring[::2], offspring[1::2]):
                    print("Mating %s and %s   --->   " % (child1.ID, child2.ID), end="")
                    if np.random.uniform() < self.cxProb:
                        print("YES!")
                        mated += 1
                        self.toolbox.mate(child1, child2)
                        del child1.fitness.values
                        del child2.fitness.values
                    else:
                        print("NO")
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
                self.assignEvalSeeds(invalid_ind, g+1)
                fitnesses = self.toolbox.map(self.toolbox.evaluate, invalid_ind)
                for ind, fit in zip(invalid_ind, fitnesses):
                    if self._stopRequested:
                        break
                    ind.fitness.values = fit

                    "record the data about the newly evaluated individual's genome in the logbook"
                    self.logbook.record(indivId = ind.ID, fitness = fit, genome = list(ind),
                                        evalSeed = ind.evalSeed)
                    #print "direct ind's name is %s and fitness is: %.2f" %(ind.ID, ind.fitness.values[0])

                hDebug('eval', str(len(invalid_ind)) + " individuals evaluated")

                # The population is entirely replaced by the offspring
                pop[:] = offspring

                # Elitism: re-insert the best individual from the previous
                # generation if it was lost during selection/variation.
                if self.hof and not any(self.indEq(ind, self.hof[0]) for ind in pop):
                    worst = max(range(len(pop)), key=lambda i: pop[i].fitness.values[0])
                    pop[worst] = self.toolbox.clone(self.hof[0])
                print("  Pop now includes: ", end="")
                for ind in pop:
                    print(ind.ID+", ", end="")
                print()

                "Compute stats for generation with the statistics object"
                record = self.stats.compile(pop)
                self.logbook.record(gen=g+1, evaluations = len(invalid_ind), **record)
                self.hof.update(pop)

                if progressCallback:
                    progressCallback(g+1, record, self.hof[0].fitness.values[0])

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
            print("Total time elapsed: ", str(datetime.timedelta(seconds=timeElapsed)))
            print("-- Cleaning up trajectory files --")
            self.cleanUpTrajFiles()
            'Record general GA run info to logbook and save logbook and history'
            self.saveLogbook(pop, timeElapsed, timeStarted)
            self.saveHistory(timeStarted)

            if self.simulatorBackend is not None:
                self.simulatorBackend.quit()

            #best_ind = tools.selBest(pop, 1)[0]
            #print("Best individual is %s, %s" % (best_ind, best_ind.fitness.values))

        except TCPConnectionError as e:
            hDebug("network major",("TCP connection error: \n" + e.value + "Cleaning up and quitting..."))
            hDebug("network",("Trying to quit simulation environment %s" % self.simulatorBackend))
            if self.simulatorBackend is not None:
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

        except Exception:
            "Something bad happened: Check if we did anything and save logbook and history of work done so far and re-raise."
            if timeElapsed is not None:
                self.saveLogbook(pop, timeElapsed, timeStarted)
                self.saveHistory(timeStarted)
            else:
                'TimeElapsed still unbound: we did not even get started.'
                pass
            raise
        finally:
            if self._pool is not None:
                self._pool.close()
                self._pool.join()
        
            

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
            dump(self.logbook, open(logbookFilename, "wb"))
        except IOError: #as e:
            #sys.stderr.write("Could not save the logbook to file:" + e.__str__ + "\n")
            print("Could not save the logbook to file:") #, e.__str__

    def saveHistory(self, timeStarted):
        """Save the history for the GA run to a pickled object
           for later analysis. Name the file according to the time
           the simulation started and save it in current directory"""
        historyFilename = self.getTimeFormattedCompleteFilename(timeStarted, 'History', 'hist')
        try:
            dump(self.hist, open(historyFilename, "wb"))
        except IOError: #as e:
            #sys.stderr.write("Could not save the logbook to file:" + e.__str__ + "\n")
            print("Could not save the history to file:") #, e.__str__
    
    
    def getTimeFormattedCompleteFilename(self,timeStarted, prefix, extension, path = None):
        """ Return a string containing a complete filename (including path)
            that starts with prefix, plus a formatted version of the timeNow string, plus
            the extension.
            Create a folder under the globally defined dataDir if no path is given.
            TimeStarted is in seconds from the epoch (as returned by time.time())
        """ 
        formattedTime = strftime("%Y-%m-%d-%H-%M-%S", localtime(timeStarted))
        filename = prefix+'-'+formattedTime+ '.' + extension
        if path is None:
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
        for i in range(self.popSize):
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
        for i in range(len(population[0])):
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
                     
        if genome is None:
            genome=self.createRandomHomeostatGenome(self.genomeSize)
        params = {'homeoGenome':genome, 'dataDir' : self.dataDir}
        self._simulation.initializeExperSetup(**params)
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
    
    def assignEvalSeeds(self, individuals, generation):
        """Give each individual about to be evaluated its evaluation seed."""
        for ind in individuals:
            ind.evalSeed = evaluation_seed(self.randomSeed, self.noiseScheme, ind, generation)

    def evaluateGenomeFitnessSeeded(self, genome):
        """Serial-path evaluation: evaluateGenomeFitness from the genome's
           evalSeed, leaving the GA's own random streams as they were."""
        with seeded_evaluation(getattr(genome, 'evalSeed', None)):
            return self.evaluateGenomeFitness(genome)

    def evaluateGenomeFitness(self,genome=None):
        """Run a simulation for a given number of steps on the given genome.
           Return final distance from target"""
            
        if genome is None:
            genome=self.createRandomHomeostatGenome(self.genomeSize)

        if self.simulatorBackend.name == "VREP":
            self.simulatorBackend.connect()
        self.experimentParams['homeoGenome']= genome
        self._simulation.initializeExperSetup(
            message="Building Homeostat from genome %s" % genome.ID,
            **self.experimentParams)

        hDebug('network', "Trying to connect to supervisor")
        self.simulatorBackend.connect()
        hDebug('network', "Connected")
        hDebug('network', "Resetting simulation world")
        self.simulatorBackend.reset()
        if self.simulatorBackend.name == "HOMEO":
            self._simulation.initializeExperSetup(
                message="Rebuilding world after reset",
                **self.experimentParams)
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

        # Enable headless/JIT optimizations for GA evaluation
        hom = self._simulation.homeostat
        hom._headless = True
        hom._collectsData = False
        hom._slowingFactor = 0
        for u in hom.homeoUnits:
            u._headless = True

        # Compute actual tick count (stepsSize = simulated seconds).
        min_dt_fast = 1.0
        for u in hom.homeoUnits:
            dt = getattr(u, '_dt_fast', 1.0)
            if dt < min_dt_fast:
                min_dt_fast = dt
        actual_ticks = int(math.ceil(self.stepsSize / min_dt_fast))

        #self._simulThread.start()
        timeNow = time()
        hDebug('eval' , "Simulation started at time: " +  str(timeNow))
        hDebug('eval', ("Now computing %d ticks (%d sim-seconds, min_dt=%.2f)..." % (actual_ticks, self.stepsSize, min_dt_fast)))
        self.worldBeingResetLock.acquire()
        for i in range(actual_ticks):
            hDebug('eval', ("Step: "+ str(i+1)+"\n"))
            self._simulation.step()
        self.worldBeingResetLock.release()
        if self.simulatorBackend.name == "HOMEO":
            self.simulatorBackend.kheperaSimulation.saveTrajectory()   # close (and flush) the .traj file
        hDebug('eval', ("Elapsed time in seconds was " + str(round((time() - timeNow),3))))
        finalDis =self.simulatorBackend.finalDisFromTarget()
        fitness = self.fitnessSign * finalDis
        hDebug('eval', ("Final distance from target was: " + str(finalDis)))
        print(" Evaluation for model %s (%d ticks, min_dt=%.2f) took time: %s with fitness %.5f" %(
            genome.ID, actual_ticks, min_dt_fast, str(datetime.timedelta(seconds=time()- timeNow)), fitness))
        return fitness,                                       # Return a tuple, as required by DEAP
        
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
    for i in range(k):
        aspirants = tools.selRandom(individuals, tournsize)
        chosen.append(max(aspirants, key=attrgetter("fitness")))
        individuals.remove(max(aspirants, key=attrgetter("fitness")))
    return chosen
