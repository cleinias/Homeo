'''
@author: stefano

The GA engine for Homeo experiments, with no GUI: HomeoGASimulation and the
worker functions used for parallel evaluation.  Uses the DEAP GA framework.

It lives apart from the GUI (Simulator/HomeoGenAlgGui.py) so that a headless
GA run does not import PyQt5's widgets.  HomeoGenAlgGui re-exports the names
defined here, so they can also be imported from it.
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
from time import time, strftime, localtime
from Helpers.ExceptionAndDebugClasses import HomeoDebug, hDebug
from Simulator.SimulatorBackend import SimulatorBackendHOMEO
from Helpers.General_Helper_Functions import homeo_version
from threading import Lock
from glob import glob

# The robot every GA evaluation and replay builds (a KheperaRobot model); GA
# logbooks record it, with the simulator and the Homeo code (homeo_version)
GA_ROBOT = 'epuck2'


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


def repeat_seeds(evalSeed, k):
    """The seeds of an individual's k evaluations: its evalSeed (so that one
       evaluation is the one a replay with the logged evalSeed repeats), then
       seeds derived from it.  None (no seed) k times for an unseeded one."""
    if evalSeed is None:
        return [None] * k
    return [int(evalSeed)] + [int(np.random.SeedSequence([int(evalSeed), j]).generate_state(1)[0])
                              for j in range(1, k)]


def averaged_fitness(scores):
    """What an evaluation of k runs returns: (mean score, score of run 1, ...).
       The GA takes the first value as the fitness and logs the others; a
       single run returns (score,)."""
    if len(scores) == 1:
        return (scores[0],)
    return (float(np.mean(scores)),) + tuple(scores)


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


def evaluation_runs(genome, evalsPerIndividual):
    """How many runs an evaluation of genome averages: its own evalRuns if
       it has one (the post-evaluation's jobs: 1), else evalsPerIndividual."""
    return getattr(genome, 'evalRuns', evalsPerIndividual)


def _evaluate_genome_worker(genome):
    """Pool entry point: evaluate `genome` from its evalSeed (see
       seeded_evaluation), as the mean of evalsPerIndividual runs (see
       evaluation_runs, repeat_seeds, averaged_fitness)."""
    scores = []
    for seed in repeat_seeds(getattr(genome, 'evalSeed', None),
                             evaluation_runs(genome, _worker_config.get('evalsPerIndividual', 1))):
        with seeded_evaluation(seed):
            scores.append(_run_genome_evaluation(genome)[0])
    return averaged_fitness(scores)


def prepare_genome_evaluation(genome, experiment, experimentParams, stepsSize, dataDir,
                              modelName=None, adjustHomeostat=None):
    """Build the simulation for evaluating `genome` exactly as a GA evaluation
       does, ready to run: returns (sim, backend), where sim.step() advances
       it one tick and stops at stepsSize ticks.  stepsSize counts homeostat
       ticks, whatever the units' dt_fast: the world advances by the same
       amount every tick, so every individual gets the same time in the
       world.  Shared by the pool workers and replay_best_with_statelog.py,
       so that a replay seeded with a logged evalSeed repeats the evaluation.

       genome          a list of genes with an ID attribute
       experiment      name of the experiment function in Simulator.HomeoExperiments
       experimentParams  extra arguments for it ('dataDir', 'noNoise', 'noUnisel')
       modelName       name for the trajectory file (default: genome.ID)
       adjustHomeostat called with the homeostat once it is built, before its
                       units are connected (a replay uses it to swap uniselectors)
    """
    backend = SimulatorBackendHOMEO(robotName='Khepera', lock=None, robotModel=GA_ROBOT)
    backend.setDataDir(dataDir)

    sim = HomeoQtSimulation(experiment=experiment, dataDir=dataDir)
    sim.maxRuns = stepsSize

    params = dict(experimentParams)
    params['homeoGenome'] = genome
    params['backendSimulator'] = backend

    sim.initializeExperSetup(
        message="Building Homeostat from genome %s" % genome.ID,
        **params)

    backend.connect()
    backend.reset()
    sim.initializeExperSetup(
        message="Rebuilding world after reset", **params)
    if adjustHomeostat is not None:
        adjustHomeostat(sim.homeostat)
    backend.close()
    backend.connect()

    backend.setRobotModel(genome.ID if modelName is None else modelName)
    sim.maxRuns = stepsSize
    sim.initializeLiveData()

    # Enable headless/JIT optimizations for GA evaluation
    hom = sim.homeostat
    hom._headless = True
    hom._collectsData = False
    hom._slowingFactor = 0
    for u in hom.homeoUnits:
        u._headless = True
    return sim, backend


def evaluate_genome(genome, experiment, experimentParams, stepsSize, dataDir, fitnessSign=1):
    """One fitness evaluation of `genome`: build it (prepare_genome_evaluation),
       run it for stepsSize ticks, and return (fitnessSign * final distance
       from the target,).  The serial path and the pool workers both evaluate
       through it."""
    if genome is None:
        raise ValueError('a fitness evaluation needs a genome')
    sim, backend = prepare_genome_evaluation(genome, experiment, experimentParams,
                                             stepsSize, dataDir)
    timeNow = time()
    for i in range(stepsSize):
        sim.step()
    backend.kheperaSimulation.saveTrajectory()   # close (and flush) the .traj file

    fitness = fitnessSign * backend.finalDisFromTarget()
    print(" Evaluation for model %s (%d ticks) took time: %s with fitness %.5f" % (
        genome.ID, stepsSize, str(datetime.timedelta(seconds=time() - timeNow)), fitness))
    return fitness,


def _run_genome_evaluation(genome):
    """Standalone fitness evaluation for use with multiprocessing.Pool:
    evaluate_genome with the module-level _worker_config (set by
    _init_worker at pool start)."""
    cfg = _worker_config
    return evaluate_genome(genome, cfg['experiment'], cfg['experimentParams'], cfg['stepsSize'],
                           cfg['dataDir'], cfg.get('fitnessSign', 1))


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
                                   simulatorBackend = "HOMEO",
                                   nWorkers = 1,
                                   noiseScheme = 'individual',
                                   evalsPerIndividual = 1,
                                   postEvalTop = 10,
                                   postEvalSeeds = 20):
        """Noisy evaluation:
           evalsPerIndividual  runs per evaluation, the fitness their mean
           postEvalTop, postEvalSeeds  at the end of a run, the hall of fame's
                       best postEvalTop are re-evaluated on postEvalSeeds fresh
                       seeds each and ranked by their mean (0: none); see
                       postEvaluate"""
        
        if noiseScheme not in NOISE_SCHEMES:
            raise ValueError("noiseScheme must be one of %s, got %r" % (NOISE_SCHEMES, noiseScheme))
        if int(evalsPerIndividual) < 1:
            raise ValueError("evalsPerIndividual must be at least 1, got %r" % evalsPerIndividual)
        self.noiseScheme = noiseScheme
        self.evalsPerIndividual = int(evalsPerIndividual)
        self.postEvalTop = int(postEvalTop)
        self.postEvalSeeds = int(postEvalSeeds)
        self.postEvaluation = None      # set by postEvaluate
        self.randomSeed = None          # set by generateRandomPop / generatePopOfClones
        self.worldBeingResetLock = Lock()
        self._stopRequested = False
        timeElapsed = None
        self._robotName = "Khepera"
        
        # "HOMEO" (Box2D), or anything else for none (the dummy evaluators).
        if simulatorBackend == "HOMEO":
            self.simulatorBackend =  SimulatorBackendHOMEO(robotName = self._robotName, lock = self.worldBeingResetLock,
                                                           robotModel = GA_ROBOT)
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
        exp_func = getattr(Simulator.HomeoExperiments, exp)
        # The homeostat's units, sensor units included: the setup's own count
        # where it declares one (the 2+2 direct vehicle 4, the 3c vehicle 10),
        # else noUnits (6, the classic vehicle's).
        self.noUnits = getattr(exp_func, 'noUnits', noUnits)
        self.noEvolvedUnits = getattr(exp_func, 'noEvolvedUnits', noUnits)
        self.fitnessSign = getattr(exp_func, 'fitnessSign', 1)
        self.genomeSize = getattr(exp_func, 'genomeSize',
                                   (self.noEvolvedUnits * essentParams) + (self.noEvolvedUnits * self.noUnits))
        # How the genes decode (Helpers.GenomeDecoder): recorded in the logbook,
        # since two layouts can have the same size; None for classic
        self.genomeLayout = getattr(exp_func, 'genomeLayout', None)
        # The TARGET's intensity the setup gives (GA_LIGHT_INTENSITY), recorded
        # so that a replay rebuilds the same world
        self.lightIntensity = getattr(exp_func, 'lightIntensity', None)
        self.stepsSize = stepsSize
        self.generSize = generSize
        self.experiment = exp
        self.cxProb = cxProb 
        self.mutationProb = mutationProb 
        self.indivProb = indivProb 
        self.tournamentSize = tournamentSize
        self.clonableGenome = clonableGenome
        if clonableGenome is not None:
            self.checkClonableGenome(clonableGenome)
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
        self._poolConfig = None         # the workers' setup, when evaluating in parallel

        if nWorkers > 1 and simulatorBackend == "HOMEO":
            self._poolConfig = {
                'experiment': exp,
                'experimentParams': {
                    'dataDir': self.dataDir,
                    'noNoise': noNoise,
                    'noUnisel': noUnisel,
                },
                'stepsSize': stepsSize,
                'dataDir': self.dataDir,
                'fitnessSign': self.fitnessSign,
                'evalsPerIndividual': self.evalsPerIndividual,
            }
            # The pool itself is made by each run (_startPool), which closes it
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
        # Out-of-range genes: a mutation's are reflected back into [0, 1]
        # (reflectBounds); crossover only swaps genes, so its clip is
        # a safety net that never acts
        self.toolbox.decorate("mate", self.checkBounds(0, 1))
        self.toolbox.decorate("mutate", self.reflectBounds(0, 1))
        
        "2.1 Define Hall of Fame and History operators"               
        'Decorate the variation operators to insert newly created individuals in the GA history'
        self.toolbox.decorate("mate", self.hist.decorator)
        self.toolbox.decorate("mutate", self.hist.decorator)
        
    def recordGADataToLogbook(self,timeElapsed, pop):
        """Insert general GA simulation parameters into logbook, replacing
           the previous summary: there is one, the latest."""
        self.logbook[:] = [rec for rec in self.logbook if 'finalIndivs' not in rec]

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
                            genomeLayout=self.genomeLayout,
                            lightIntensity=self.lightIntensity,
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
                            cloneSourceFitness = (self.clonableGenome or {}).get('fitness')
                                                 if self._type == 'clones' else None,
                            randomSeed = self.randomSeed,
                            noiseScheme = self.noiseScheme,
                            evalsPerIndividual = self.evalsPerIndividual,
                            postEvaluation = self.postEvaluation,
                            noNoise = self.experimentParams['noNoise'],
                            noUnisel = self.experimentParams['noUnisel'],
                            homeo = homeo_version(),
                            simulator = 'box2d',
                            robot = GA_ROBOT) 


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
    
    def checkBounds(self, low, high):
        "Decorate a variation operator: its offspring's genes clipped to [low, high], as floats"
        low, high = float(low), float(high)
        def decorator(func):
            def wrapper(*args, **kargs):
                offspring = func(*args, **kargs)
                for child in offspring:
                    for i in range(len(child)):
                        if child[i] > high:
                            child[i] = high
                        elif child[i] < low:
                            child[i] = low
                return offspring
            return wrapper
        return decorator

    @staticmethod
    def reflect(value, low=0.0, high=1.0):
        """value folded back into [low, high] by its overshoot: 1.07 -> 0.93,
           -0.05 -> 0.05 (repeatedly, for an overshoot beyond the range)."""
        span = high - low
        x = (value - low) % (2 * span)
        return low + (2 * span - x if x > span else x)

    def reflectBounds(self, low, high):
        """Decorate a mutation: its out-of-range genes reflected back into
           [low, high].  Mutation alone then keeps a uniform spread of genes
           uniform.  Clipping them instead would put many mutated genes
           exactly on 0 or 1, the parameters' extremes."""
        low, high = float(low), float(high)
        def decorator(func):
            def wrapper(*args, **kargs):
                offspring = func(*args, **kargs)
                for child in offspring:
                    for i in range(len(child)):
                        if not low <= child[i] <= high:
                            child[i] = self.reflect(child[i], low, high)
                return offspring
            return wrapper
        return decorator
    
    def initIndividual(self, indivClass, genomeSize, ID = None):
        "Generate an individual's random genome"
        ind = indivClass(np.random.uniform(0,1) for _ in range(genomeSize))
        ind.ID = ID
        return ind
    
    def checkClonableGenome(self, genome):
        '''ValueError unless genome (a dict as StatsAnalyzer.extractGenomeOfIndID
           returns) fits this run's setup: its genomeLayout is the setup's, and
           it has the setup's number of genes.  The layout must be named, since
           two layouts can have the same size.'''
        if 'genomeLayout' not in genome:
            raise ValueError('the genome to clone does not say its layout (genomeLayout)')
        if genome['genomeLayout'] != self.genomeLayout:
            raise ValueError("the genome to clone has layout %r, %s's is %r"
                             % (genome['genomeLayout'], self.experiment, self.genomeLayout))
        if len(genome['genome']) != self.genomeSize:
            raise ValueError("the genome to clone has %d genes, %s's genomes %d"
                             % (len(genome['genome']), self.experiment, self.genomeSize))

    def initIndividualClone(self, indivClass, genome):
        """Generate an individual with given genome.
           Assumes 'genome' is a dictionary with keys indivId, genome and,
           optionally, fitness.  The clone starts without a fitness:
           generation 0 evaluates it, like every individual.  The logged
           fitness came from another run's evaluation (often of another code
           version), so it is recorded in the logbook's summary as
           cloneSourceFitness, not given to the clones."""
        ind = indivClass(genome['genome'])
        ind.ID = genome["indivId"]
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

    def _startPool(self):
        """The run's worker pool, when evaluating in parallel.  One per run,
        made at its start and closed at its end, so that the same object can
        run more than once."""
        if self._poolConfig is None:
            return
        ctx = multiprocessing.get_context('forkserver')
        self._pool = ctx.Pool(
            self.nWorkers, initializer=_init_worker, initargs=(self._poolConfig,))
        self.toolbox.register('map', self._pool.map)
        self.toolbox.register("evaluate", _evaluate_genome_worker)

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
        # A run's records are its own: a fresh logbook, hall of fame and
        # history (cleared in place: the variation operators are decorated
        # with this history), and no post-evaluation yet
        self.logbook = tools.Logbook()
        self.hof.clear()
        self.hist.__init__()
        self.postEvaluation = None
        self._startPool()
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
                self._storeEvaluation(ind, fit)
            self.hof.update(pop)
            self.hist.update(pop)
            print("  Evaluated %i individuals" % len(pop))
            print("  Pop now includes: ", end="")
            for ind in pop:
                print(ind.ID+", ", end="")
            print()

            # Generation 0's statistics, recorded whether or not anyone is
            # told of them, so headless runs' fitness curves have it too
            record0 = self.stats.compile(pop)
            self.logbook.record(gen=0, evaluations=len(pop), **record0)
            if progressCallback:
                progressCallback(0, record0, self.hof[0].fitness.values[0])
            # Saved now, so that a crash in generation 1 does not lose
            # generation 0 too
            self.saveLogbook(pop, time() - timeStarted, timeStarted)
            self.saveHistory(timeStarted)

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

                # Elitism: the previous generation's best genome survives.  If
                # selection and variation lost it, a copy is evaluated with
                # the offspring and replaces the worst of them.
                elite = self.toolbox.clone(min(pop, key=lambda ind: ind.fitness.values[0]))
                eliteLost = not any(self.indEq(ind, elite) for ind in offspring)

                # Under noise ('individual' and 'generation' schemes) everyone
                # is evaluated afresh, survivors and the elite included: a
                # score kept from an earlier generation is one old noisy
                # draw, and selection would favour the lucky ones.  Under
                # 'genome' a genome always scores the same, so only changed
                # ones are evaluated.
                if self.noiseScheme != 'genome':
                    for ind in offspring + [elite]:
                        if ind.fitness.valid:
                            del ind.fitness.values

                hDebug('eval', "Evaluating individual with invalid fitness")
                invalid_ind = [ind for ind in offspring if not ind.fitness.valid]
                if eliteLost and not elite.fitness.valid:
                    invalid_ind.append(elite)

                "Change the ID's of the invalid ind's"
                for i, ind in enumerate(invalid_ind):
                    #print "The old ind's ID was: ", ind.ID
                    ind.ID = str(g+1).zfill(self.IDPad) + "-"+str(i+1).zfill(self.IDPad)
                    #print "Now changed to: ", ind.ID

                'Re-evaluate'
                self.assignEvalSeeds(invalid_ind, g+1)
                fitnesses = self.toolbox.map(self.toolbox.evaluate, invalid_ind)
                stopped = False
                for ind, fit in zip(invalid_ind, fitnesses):
                    self._storeEvaluation(ind, fit)
                    #print "direct ind's name is %s and fitness is: %.2f" %(ind.ID, ind.fitness.values[0])
                    # Stop asked during the generation (serial evaluation is
                    # lazy, so the GUI's Stop lands here): keep what was
                    # evaluated in the logbook and the previous generation as
                    # the population, and end the run as at its end.
                    if self._stopRequested:
                        stopped = True
                        break
                if stopped:
                    print("-- Stopped during generation %d: its offspring are discarded --" % (g+1))
                    break

                hDebug('eval', str(len(invalid_ind)) + " individuals evaluated")

                # The population is entirely replaced by the offspring
                pop[:] = offspring
                if eliteLost:
                    worst = max(range(len(pop)), key=lambda i: pop[i].fitness.values[0])
                    pop[worst] = elite
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
            if not self._stopRequested and self.postEvalTop > 0:
                self.postEvaluate()
            timeElapsed = time() - timeStarted
            print("-- End of (successful) evolution --")
            print("Total time elapsed: ", str(datetime.timedelta(seconds=timeElapsed)))
            print("-- Cleaning up trajectory files --")
            self.cleanUpTrajFiles()
            'Record general GA run info to logbook and save logbook and history'
            self.saveLogbook(pop, timeElapsed, timeStarted)
            self.saveHistory(timeStarted)

            # The built-in simulator stays, for another run on this object
            # (quitting it would discard its simulation); an external one
            # is shut down
            if self.simulatorBackend is not None and self.simulatorBackend.name != "HOMEO":
                self.simulatorBackend.quit()

            #best_ind = tools.selBest(pop, 1)[0]
            #print("Best individual is %s, %s" % (best_ind, best_ind.fitness.values))

        except Exception:
            "Something bad happened: save the logbook and history of the work done so far and re-raise."
            self.saveLogbook(pop, time() - timeStarted, timeStarted)
            self.saveHistory(timeStarted)
            raise
        finally:
            if self._pool is not None:
                self._pool.close()
                self._pool.join()
                self._pool = None
        
            

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
            with open(logbookFilename, "wb") as f:
                dump(self.logbook, f)
        except IOError: #as e:
            #sys.stderr.write("Could not save the logbook to file:" + e.__str__ + "\n")
            print("Could not save the logbook to file:") #, e.__str__

    def saveHistory(self, timeStarted):
        """Save the history for the GA run to a pickled object
           for later analysis. Name the file according to the time
           the simulation started and save it in current directory"""
        historyFilename = self.getTimeFormattedCompleteFilename(timeStarted, 'History', 'hist')
        try:
            with open(historyFilename, "wb") as f:
                dump(self.hist, f)
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
    
        
    def evaluateGenomeFitnessSUPER_DUMMY(self,genome=None):
        """For GA testing purposes: do not initialize experiments and homeostats,
           and do NOT run a simulation: 
           just return a normally distributed random fitness instead"""         
                     
        #=======================================================================
        # if genome==None:
        #     genome=self.createRandomHomeostatGenome(self.genomeSize)
        # self._simulation.initializeExperSetup(genome)
        # self._supervisor.clientConnect()
        # self.simulationEnvironReset()
        # self._supervisor.close()
        # self._supervisor.clientConnect()
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
           evalSeed, leaving the GA's own random streams as they were; the
           mean of evalsPerIndividual runs (see _evaluate_genome_worker)."""
        scores = []
        for seed in repeat_seeds(getattr(genome, 'evalSeed', None),
                                 evaluation_runs(genome, self.evalsPerIndividual)):
            with seeded_evaluation(seed):
                scores.append(self.evaluateGenomeFitness(genome)[0])
        return averaged_fitness(scores)

    def _storeEvaluation(self, ind, result):
        """Give ind the fitness an evaluation returned (its first value: see
           averaged_fitness) and log the evaluation, with the runs' scores
           when there were several."""
        ind.fitness.values = tuple(result[:1])
        extra = {'scores': list(result[1:])} if len(result) > 1 else {}
        self.logbook.record(indivId = ind.ID, fitness = ind.fitness.values, genome = list(ind),
                            evalSeed = ind.evalSeed, **extra)

    def postEvaluate(self):
        """Re-evaluate the hall of fame's best postEvalTop individuals on
           postEvalSeeds fresh seeds each, one run per seed whatever
           evalsPerIndividual, and rank them by their mean score.  The hall of
           fame keeps each genome with the score it entered with, which, with
           noise, is mostly a lucky evaluation: the mean says which genome is
           best.  Kept in self.postEvaluation and the logbook's summary: a
           list, best mean first, of dicts with
               indivId, genome   the hall of fame's individual
               mean, sd, scores  over the seeds, single runs
               hofFitness        the score it entered the hall of fame with
               evaluations, loggedBest, loggedMean
                                 how often the run's logbook records the
                                 genome, its lowest and its mean fitness there
           The seeds are derived from the GA's seed, so a rerun repeats them."""
        top = list(self.hof)[:self.postEvalTop]
        if not top or self.postEvalSeeds < 1:
            return None
        jobs = []
        for i, ind in enumerate(top):
            for j in range(self.postEvalSeeds):
                job = self.toolbox.clone(ind)
                job.ID = 'post-%s-%d' % (ind.ID, j + 1)
                job.evalSeed = int(np.random.SeedSequence(
                    [int(self.randomSeed), 3, i, j]).generate_state(1)[0])
                job.evalRuns = 1
                jobs.append((i, job))
        print("-- Post-evaluation: the best %d of the hall of fame, %d seeds each --"
              % (len(top), self.postEvalSeeds))
        results = list(self.toolbox.map(self.toolbox.evaluate, [job for _, job in jobs]))
        scores = [[] for _ in top]
        for (i, _), result in zip(jobs, results):
            scores[i].append(float(result[0]))
        def logged(ind):
            fitnesses = [r['fitness'][0] for r in self.logbook
                         if 'genome' in r and list(r['genome']) == list(ind)]
            return {'evaluations': len(fitnesses), 'loggedBest': float(min(fitnesses)),
                    'loggedMean': float(np.mean(fitnesses))}
        self.postEvaluation = sorted(
            (dict({'indivId': ind.ID, 'genome': list(ind), 'hofFitness': ind.fitness.values[0],
                   'mean': float(np.mean(s)), 'sd': float(np.std(s)), 'scores': s},
                  **logged(ind))
             for ind, s in zip(top, scores)),
            key=lambda entry: entry['mean'])
        for entry in self.postEvaluation:
            print("  %s: mean %.4f (sd %.4f) over %d seeds; hall of fame %.4f"
                  % (entry['indivId'], entry['mean'], entry['sd'], len(entry['scores']),
                     entry['hofFitness']))
        return self.postEvaluation

    def evaluateGenomeFitness(self, genome):
        """Evaluate genome as a pool worker does (evaluate_genome), with this
           run's experiment, parameters and length.  Returns (fitness,)."""
        params = {key: value for key, value in self.experimentParams.items()
                  if key in ('dataDir', 'noNoise', 'noUnisel')}
        return evaluate_genome(genome, self.experiment, params, self.stepsSize, self.dataDir,
                               self.fitnessSign)

    def cleanUpTrajFiles(self):
        """Remove all files not related to specific homeostat models from
           dataDir: the trajectories of the robot before it has a model name,
           which the writer names trajData-ID-Unspecified-<time>[<tag>][-n].traj."""
        unspecificFileList = glob(os.path.join(self.dataDir, "trajData-ID-Unspecified-*.traj"))
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
