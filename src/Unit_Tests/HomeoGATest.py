'''
Tests for the GA simulation infrastructure:
- GenomeDecoder: encoding/decoding of homeostat genomes
- HomeoGASimulation: basic GA operations (population creation, individual init, bounds checking)

(StatsAnalyzer's tests are in StatsAnalyzerTest.)  These tests need no
external robot simulator.
HomeoGASimulation tests require Box2D (for the internal HOMEO simulator) and are
skipped if Box2D is not installed.

@author: stefano
'''

import unittest
import numpy as np
import os
import tempfile

from Helpers.GenomeDecoder import genomeDecoder, genomePrettyPrinter, statFileDecoder
from Core.HomeoUnit import HomeoUnit
from Core.HomeoConnection import HomeoConnection

# Check if Box2D is available for the HOMEO backend tests
try:
    from KheperaSimulator.KheperaSimulator import KheperaSimulation
    HAS_BOX2D = True
except ImportError:
    HAS_BOX2D = False


class GenomeDecoderTest(unittest.TestCase):
    """Tests for genome encoding/decoding utilities"""

    def testGenomeDecoderLength(self):
        """genomeDecoder returns correct number of decoded values"""
        noUnits = 4
        essentParams = 4
        genomeSize = noUnits * essentParams + noUnits ** 2
        genome = np.random.uniform(0, 1, size=genomeSize)
        decoded = genomeDecoder(noUnits, genome)
        expectedLen = noUnits * essentParams + noUnits ** 2
        self.assertEqual(len(decoded), expectedLen)

    def testGenomeDecoderLength6Units(self):
        """genomeDecoder works for 6-unit homeostats"""
        noUnits = 6
        essentParams = 4
        genomeSize = noUnits * essentParams + noUnits ** 2
        genome = np.random.uniform(0, 1, size=genomeSize)
        decoded = genomeDecoder(noUnits, genome)
        expectedLen = noUnits * essentParams + noUnits ** 2
        self.assertEqual(len(decoded), expectedLen)

    def testGenomeDecoderMassRange(self):
        """Decoded mass values fall within HomeoUnit mass range"""
        noUnits = 4
        essentParams = 4
        genomeSize = noUnits * essentParams + noUnits ** 2
        genome = np.random.uniform(0, 1, size=genomeSize)
        decoded = genomeDecoder(noUnits, genome)
        minMass = HomeoUnit.DefaultParameters['minMass']
        maxMass = HomeoUnit.DefaultParameters['maxMass']
        for unit in range(noUnits):
            mass = decoded[unit * essentParams + 0]
            self.assertGreaterEqual(mass, minMass)
            self.assertLessEqual(mass, maxMass)

    def testGenomeDecoderValues(self):
        """Genes 0, 0.5 and 1 decode to each parameter's documented minimum,
        midpoint and maximum: classic (mass, viscosity, uniselector interval,
        maxDeviation, then weights) and weight-free with dt_fast (mass,
        viscosity, tau_a, maxDeviation, dt_fast, and the effective mass and
        viscosity, mass / dt_fast**2 and viscosity / dt_fast)."""
        for gene, classic, weightfree in (
                (0.0, [10, 0, 0, 0.1], [1, 0, 100, 0.1, 0.2, 25, 0]),
                (0.5, [5005, 5, 500, 500.05], [5.5, 5, 1000, 500.05, 1.1, 5.5 / 1.21, 5 / 1.1]),
                (1.0, [10000, 10, 1000, 1000], [10, 10, 10000, 1000, 2.0, 2.5, 5])):
            with self.subTest(gene=gene):
                decoded = genomeDecoder(2, [gene] * 12, layout='classic')
                expected = classic * 2 + [2 * gene - 1] * 4
                for value, want in zip(decoded, expected):
                    self.assertAlmostEqual(value, want, places=9)
                decoded = genomeDecoder(2, [gene] * 10, layout='weightfree_dt')
                self.assertEqual(len(decoded), 14)
                for value, want in zip(decoded, weightfree * 2):
                    self.assertAlmostEqual(value, want, places=9)

    def testGenomeDecoderV2Values(self):
        """The _v2 layout: mass 0.25 -> 250 and viscosity 0.05 -> 50,
        log-uniform; tau_a and maxDeviation as in the other weight-free layouts"""
        for gene, values in ((0.0, [0.25, 0.05, 100, 0.1]),
                             (0.5, [0.25 * 1000 ** 0.5, 0.05 * 1000 ** 0.5, 1000, 500.05]),
                             (1.0, [250, 50, 10000, 1000])):
            with self.subTest(gene=gene):
                decoded = genomeDecoder(2, [gene] * 8, layout='weightfree_v2')
                for value, want in zip(decoded, values * 2):
                    self.assertAlmostEqual(value, want, places=9)
        # its size is the 'weightfree' layout's: never guessed
        from Helpers.GenomeDecoder import genomeLayout
        self.assertEqual(genomeLayout(4, 8, 2), 'weightfree')

    def testGenomeDecoderConnectionWeights(self):
        """Decoded connection weights map (0,1) to (-1,1)"""
        noUnits = 4
        essentParams = 4
        genomeSize = noUnits * essentParams + noUnits ** 2
        genome = np.random.uniform(0, 1, size=genomeSize)
        decoded = genomeDecoder(noUnits, genome)
        for conn in range(noUnits * noUnits):
            weight = decoded[noUnits * essentParams + conn]
            # connWeightFromGAWeight maps (0,1) to (-1,1)
            self.assertGreaterEqual(weight, -1.0)
            self.assertLessEqual(weight, 1.0)

    def testGenomeDecoderBoundaryValues(self):
        """genomeDecoder handles boundary genome values (all 0s and all 1s)"""
        noUnits = 4
        essentParams = 4
        genomeSize = noUnits * essentParams + noUnits ** 2

        # All zeros
        genome_zeros = [0.0] * genomeSize
        decoded_zeros = genomeDecoder(noUnits, genome_zeros)
        self.assertEqual(len(decoded_zeros), genomeSize)

        # All ones
        genome_ones = [1.0] * genomeSize
        decoded_ones = genomeDecoder(noUnits, genome_ones)
        self.assertEqual(len(decoded_ones), genomeSize)

    def testGenomePrettyPrinter(self):
        """genomePrettyPrinter returns a non-empty string"""
        noUnits = 4
        essentParams = 4
        genomeSize = noUnits * essentParams + noUnits ** 2
        genome = np.random.uniform(0, 1, size=genomeSize)
        decoded = genomeDecoder(noUnits, genome)
        result = genomePrettyPrinter(noUnits, decoded)
        self.assertIsInstance(result, str)
        self.assertTrue(len(result) > 0)
        self.assertIn('mass:', result)
        self.assertIn('visc:', result)

    def testTrimmedGenomeDecoder(self):
        """genomeDecoder with noEvolvedUnits < noUnits produces correct length"""
        noUnits = 6
        noEvolvedUnits = 4
        essentParams = 4
        genomeSize = noEvolvedUnits * essentParams + noEvolvedUnits * noUnits  # 40
        genome = np.random.uniform(0, 1, size=genomeSize)
        decoded = genomeDecoder(noUnits, genome, noEvolvedUnits=noEvolvedUnits)
        expectedLen = noEvolvedUnits * essentParams + noEvolvedUnits * noUnits  # 40
        self.assertEqual(len(decoded), expectedLen)

    def testTrimmedGenomeConnectionWeights(self):
        """Trimmed genome decodes connection weights correctly"""
        noUnits = 6
        noEvolvedUnits = 4
        essentParams = 4
        genomeSize = noEvolvedUnits * essentParams + noEvolvedUnits * noUnits  # 40
        genome = np.random.uniform(0, 1, size=genomeSize)
        decoded = genomeDecoder(noUnits, genome, noEvolvedUnits=noEvolvedUnits)
        # Connection weights start after noEvolvedUnits * essentParams = 16 decoded values
        connStart = noEvolvedUnits * essentParams
        for i in range(noEvolvedUnits * noUnits):
            weight = decoded[connStart + i]
            self.assertGreaterEqual(weight, -1.0)
            self.assertLessEqual(weight, 1.0)

    def testTrimmedGenomePrettyPrinter(self):
        """genomePrettyPrinter works with noEvolvedUnits < noUnits"""
        noUnits = 6
        noEvolvedUnits = 4
        essentParams = 4
        genomeSize = noEvolvedUnits * essentParams + noEvolvedUnits * noUnits
        genome = np.random.uniform(0, 1, size=genomeSize)
        decoded = genomeDecoder(noUnits, genome, noEvolvedUnits=noEvolvedUnits)
        result = genomePrettyPrinter(noUnits, decoded, noEvolvedUnits=noEvolvedUnits)
        self.assertIsInstance(result, str)
        self.assertIn('mass:', result)
        # Should have 4 mass lines (evolved units), not 6
        self.assertEqual(result.count('mass:'), noEvolvedUnits)

    def testMassFromWeightBoundaries(self):
        """massFromWeight maps 0 to minMass and 1 to maxMass"""
        minMass = HomeoUnit.DefaultParameters['minMass']
        maxMass = HomeoUnit.DefaultParameters['maxMass']
        self.assertAlmostEqual(HomeoUnit.massFromWeight(0.0), minMass)
        self.assertAlmostEqual(HomeoUnit.massFromWeight(1.0), maxMass)

    def testConnWeightFromGAWeightBoundaries(self):
        """connWeightFromGAWeight maps 0->-1, 0.5->0, 1->1"""
        conn = HomeoConnection()
        self.assertAlmostEqual(conn.connWeightFromGAWeight(0.0), -1.0)
        self.assertAlmostEqual(conn.connWeightFromGAWeight(0.5), 0.0)
        self.assertAlmostEqual(conn.connWeightFromGAWeight(1.0), 1.0)


@unittest.skipUnless(HAS_BOX2D, "Box2D not installed — HOMEO backend unavailable")
class HomeoGASimulationTest(unittest.TestCase):
    """Tests for HomeoGASimulation class — HOMEO backend only"""

    @classmethod
    def setUpClass(cls):
        """Create a HomeoGASimulation with HOMEO backend and small parameters"""
        from Simulator.HomeoGenAlg import HomeoGASimulation
        cls.ga = HomeoGASimulation(
            postEvalTop=0,
            popSize=4,
            stepsSize=10,
            generSize=1,
            noUnits=4,
            essentParams=4,
            simulatorBackend="HOMEO",
        )

    def testInstantiation(self):
        """HomeoGASimulation instantiates with HOMEO backend"""
        self.assertIsNotNone(self.ga)
        self.assertEqual(self.ga.popSize, 4)
        self.assertEqual(self.ga.stepsSize, 10)

    def testGenomeSize(self):
        """Genome size is noEvolvedUnits*essentParams + noEvolvedUnits*noUnits"""
        # For 4-unit system where all units are evolved: 4*4 + 4*4 = 32
        expected = 4 * 4 + 4 * 4  # 32
        self.assertEqual(self.ga.genomeSize, expected)

    def testCreateRandomGenome(self):
        """createRandomHomeostatGenome returns array of correct size with values in [0,1]"""
        genome = self.ga.createRandomHomeostatGenome(self.ga.genomeSize)
        self.assertEqual(len(genome), self.ga.genomeSize)
        for val in genome:
            self.assertGreaterEqual(val, 0.0)
            self.assertLessEqual(val, 1.0)

    def testGenerateRandomPop(self):
        """generateRandomPop creates a population of correct size"""
        pop = self.ga.generateRandomPop(randomSeed=42)
        self.assertEqual(len(pop), self.ga.popSize)

    def testIndividualHasID(self):
        """Individuals have an ID attribute"""
        pop = self.ga.generateRandomPop(randomSeed=42)
        for ind in pop:
            self.assertTrue(hasattr(ind, 'ID'))

    def testIndividualGenomeLength(self):
        """Each individual's genome has the correct length"""
        pop = self.ga.generateRandomPop(randomSeed=42)
        for ind in pop:
            self.assertEqual(len(ind), self.ga.genomeSize)

    def testCheckBoundsDecorator(self):
        """checkBounds decorator clips values to [0,1]"""
        decorator = self.ga.checkBounds(0, 1)

        @decorator
        def dummy_func(*args, **kwargs):
            return [[1.5, -0.3, 0.5, 2.0]]

        result = dummy_func()
        for child in result:
            for val in child:
                self.assertGreaterEqual(val, 0)
                self.assertLessEqual(val, 1)
                self.assertIsInstance(val, float)        # 0 and 1 too, not ints

    def testIndEq(self):
        """indEq returns True for identical genomes, False for different"""
        pop = self.ga.generateRandomPop(randomSeed=42)
        self.assertTrue(self.ga.indEq(pop[0], pop[0]))
        if len(pop) > 1:
            self.assertFalse(self.ga.indEq(pop[0], pop[1]))

    def testEvaluateGenomeFitnessSuperDummy(self):
        """SUPER_DUMMY evaluator returns a tuple with a float fitness"""
        result = self.ga.evaluateGenomeFitnessSUPER_DUMMY()
        self.assertIsInstance(result, tuple)
        self.assertEqual(len(result), 1)
        self.assertIsInstance(result[0], float)

    def testDataDirCreated(self):
        """GA simulation creates its data directory"""
        self.assertTrue(os.path.isdir(self.ga.dataDir))

    def testToolboxRegistered(self):
        """The serial toolbox evaluates seeded, selects by tournaments of
        tournamentSize, and maps serially (mate and mutate: GALoopTest)"""
        from deap import tools
        toolbox = self.ga.toolbox
        self.assertEqual(toolbox.evaluate.func, self.ga.evaluateGenomeFitnessSeeded)
        self.assertIs(toolbox.select.func, tools.selTournament)
        self.assertEqual(toolbox.select.keywords, {'tournsize': self.ga.tournamentSize})
        self.assertIs(toolbox.map.func, map)
        self.assertEqual(len(toolbox.population(n=3)), 3)


@unittest.skipUnless(HAS_BOX2D, "Box2D not installed — HOMEO backend unavailable")
class HomeoGASimulationTrimmedGenomeTest(unittest.TestCase):
    """Test that 6-unit system with 4 evolved units produces trimmed genome"""

    @classmethod
    def setUpClass(cls):
        from Simulator.HomeoGenAlg import HomeoGASimulation
        cls.ga = HomeoGASimulation(
            postEvalTop=0,
            popSize=4,
            stepsSize=10,
            generSize=1,
            noUnits=6,
            essentParams=4,
            simulatorBackend="HOMEO",
        )

    def testTrimmedGenomeSize(self):
        """6-unit system with 4 evolved units has genome size 40"""
        # noEvolvedUnits=4 from experiment attribute, noUnits=6
        # genomeSize = 4*4 + 4*6 = 40
        self.assertEqual(self.ga.genomeSize, 40)
        self.assertEqual(self.ga.noEvolvedUnits, 4)
        self.assertEqual(self.ga.noUnits, 6)

    def testTrimmedIndividualGenomeLength(self):
        """Individuals have genome length matching trimmed genome size"""
        pop = self.ga.generateRandomPop(randomSeed=42)
        for ind in pop:
            self.assertEqual(len(ind), 40)


class HomeoGASimulationUnitCountTest(unittest.TestCase):
    "The GA takes the unit count, which its logbook records, from the setup"

    def testTheDirectVehicleHasFourUnits(self):
        from Simulator.HomeoGenAlg import HomeoGASimulation
        ga = HomeoGASimulation(postEvalTop=0, popSize=2, stepsSize=10, generSize=1,
                               noUnits=6, simulatorBackend=None,
                               exp='initializeBraiten2_direct_GA_continuous_weightfree_v2')
        self.assertEqual(ga.noUnits, 4)
        self.assertEqual(ga.noEvolvedUnits, 2)
        self.assertEqual(ga.genomeSize, 8)


try:
    import PyQt5.QtWidgets
    HAS_QT_WIDGETS = True
except ImportError:
    HAS_QT_WIDGETS = False


@unittest.skipUnless(HAS_QT_WIDGETS, "PyQt5 not installed — the GA GUI module needs it")
class GAGuiReexportTest(unittest.TestCase):
    """The engine moved to Simulator/HomeoGenAlg.py; the GUI module still offers it."""

    def testGuiModuleReexportsTheEngine(self):
        "existing imports from HomeoGenAlgGui get the very same objects"
        import Simulator.HomeoGenAlg as engine
        import Simulator.HomeoGenAlgGui as gui
        for name in ('HomeoGASimulation', 'selTournamentRemove',
                     '_init_worker', '_evaluate_genome_worker'):
            self.assertIs(getattr(gui, name), getattr(engine, name), name)


@unittest.skipUnless(HAS_BOX2D, "Box2D not installed — HOMEO backend unavailable")
@unittest.skipUnless(HAS_QT_WIDGETS, "PyQt5 not installed — the GA GUI module needs it")
class GAGuiSeedTest(unittest.TestCase):
    """The GA GUI's seed field seeds the whole run."""

    @classmethod
    def setUpClass(cls):
        from unittest import mock
        from PyQt5.QtWidgets import QApplication, QMessageBox
        from Simulator.HomeoGenAlg import HomeoGASimulation
        cls.app = QApplication.instance() or QApplication([])
        cls.tmp = tempfile.TemporaryDirectory()
        cls.savedRoot = HomeoGASimulation.dataDirRoot
        HomeoGASimulation.dataDirRoot = cls.tmp.name
        cls.mock, cls.QMessageBox = mock, QMessageBox

    @classmethod
    def tearDownClass(cls):
        from Simulator.HomeoGenAlg import HomeoGASimulation
        HomeoGASimulation.dataDirRoot = cls.savedRoot
        cls.tmp.cleanup()

    def _guiRun(self, seed):
        """Run a 4-individual, 1-generation GA from the GUI; return what it evaluated."""
        from Simulator.HomeoGenAlgGui import HomeoGASimulGUI
        gui = HomeoGASimulGUI()
        gui.noIndividualsSpinBox.setValue(4)
        gui.stepsSpinBox.setValue(100)
        gui.generationsSpinBox.setValue(1)
        gui.workersSpinBox.setValue(1)
        gui.experimentComboBox.setCurrentText(
            "initializeBraiten2_2_Full_GA_continuous_weightfree_fixed_v2")
        self.assertEqual(gui.experimentComboBox.currentText(),
                         "initializeBraiten2_2_Full_GA_continuous_weightfree_fixed_v2")
        gui.seedSpinBox.setValue(seed)
        gui._initializePopulation()
        self.assertEqual(gui.gaSimulation.randomSeed, seed)
        gui.gaSimulation.postEvalTop = 0      # not what is tested; 200 evaluations

        def fail(*args):                  # an error dialog would block the test
            raise RuntimeError(args[2])
        # stdout redirection into the output pane is not what is tested here
        with self.mock.patch.object(self.QMessageBox, 'critical', side_effect=fail), \
             self.mock.patch.object(gui, '_redirectStdout'), \
             self.mock.patch.object(gui, '_restoreStdout'):
            gui._startEvolution()
        return [(r['indivId'], list(r['fitness']), r['genome'], r['evalSeed'])
                for r in gui.gaSimulation.logbook if 'indivId' in r]

    def testSeedFieldMakesGuiRunsReproducible(self):
        "the same seed gives the same run, another seed another run"
        first = self._guiRun(7)
        self.assertEqual(self._guiRun(7), first)
        self.assertNotEqual(self._guiRun(8), first)

    def testClonesNeedAGenome(self):
        """Clones without a genome to clone: a warning, and no population (not
        a random one, silently); no worker pool is left by initializing
        again."""
        from Simulator.HomeoGenAlgGui import HomeoGASimulGUI
        gui = HomeoGASimulGUI()
        gui.workersSpinBox.setValue(2)
        gui.popTypeComboBox.setCurrentText("Clones")
        with self.mock.patch.object(self.QMessageBox, 'warning') as warned:
            gui._initializePopulation()
        warned.assert_called_once()
        self.assertIsNone(gui.gaSimulation)
        self.assertFalse(gui.startPushButton.isEnabled())
        gui.popTypeComboBox.setCurrentText("Random")
        gui._initializePopulation()
        first = gui.gaSimulation
        gui._initializePopulation()
        self.assertIsNone(first._pool)
        self.assertIsNone(gui.gaSimulation._pool)

    def testSeedFieldDefaultsTo64(self):
        "the field starts at 64, the default seed of GUI runs"
        from Simulator.HomeoGenAlgGui import HomeoGASimulGUI
        gui = HomeoGASimulGUI()           # keep a reference: Qt deletes an unreferenced widget
        self.assertEqual(gui.seedSpinBox.value(), 64)


class StatFileDecoderTest(unittest.TestCase):
    """Tests for stat file decoding"""

    def testStatFileDecoder(self):
        """statFileDecoder reads a GA stat file and decodes genomes"""
        noUnits = 4
        essentParams = 4
        genomeSize = noUnits * essentParams + noUnits ** 2

        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as fin:
            values = [1, 2.5, 10.3] + [0.5] * genomeSize
            fin.write('\t'.join(str(v) for v in values) + '\n')
            inFile = fin.name

        outFile = inFile + '.decoded'
        try:
            statFileDecoder(inFile, outFile, noUnits=noUnits)
            self.assertTrue(os.path.exists(outFile))
            with open(outFile) as f:
                lines = f.readlines()
            self.assertEqual(len(lines), 2)  # header + 1 data line
        finally:
            os.unlink(inFile)
            if os.path.exists(outFile):
                os.unlink(outFile)

    def testWeightFreeLinesGetTheirOwnHeaders(self):
        """A weight-free genome is decoded under weight-free headers, one per
        value, not under classic ones"""
        with tempfile.TemporaryDirectory() as tmp:
            inFile, outFile = os.path.join(tmp, 'in.txt'), os.path.join(tmp, 'out.txt')
            with open(inFile, 'w') as f:
                f.write('\t'.join(str(v) for v in [1, 2.5, 10.3] + [0.5] * 20) + '\n')
            statFileDecoder(inFile, outFile, noUnits=6, noEvolvedUnits=4)
            with open(outFile) as f:
                headers, values = [line.split('\t')[:-1] for line in f.readlines()]
        self.assertEqual(len(headers), len(values))
        self.assertEqual(headers[3:8], ['U1-mass', 'U1-visc', 'U1-tau_a', 'U1-maxDev',
                                        'U1-dt_fast'])

    def testAGenomeOfNoLayoutIsAnError(self):
        """A genome size that matches no layout raises instead of being read
        as classic and silently truncated"""
        with self.assertRaises(ValueError):
            genomeDecoder(6, [0.5] * 61)
        with self.assertRaises(ValueError):
            genomeDecoder(6, [0.5] * 61, layout='classic')
        self.assertEqual(len(genomeDecoder(6, [0.5] * 60)), 60)


class ExperimentAttributesTest(unittest.TestCase):
    """Tests for experiment function attributes (fitnessSign, noEvolvedUnits)"""

    def setUp(self):
        import Simulator.HomeoExperiments as exps
        self.exps = exps

    def testPhototaxisFitnessSign(self):
        """Phototaxis experiment has fitnessSign == 1 (minimise distance)"""
        self.assertEqual(self.exps.initializeBraiten2_2_Full_GA_phototaxis.fitnessSign, 1)

    def testScototaxisFitnessSign(self):
        """Scototaxis experiment has fitnessSign == -1 (negate distance)"""
        self.assertEqual(self.exps.initializeBraiten2_2_Full_GA_scototaxis.fitnessSign, -1)

    def testPhototaxisNoEvolvedUnits(self):
        """Phototaxis experiment has noEvolvedUnits == 4"""
        self.assertEqual(self.exps.initializeBraiten2_2_Full_GA_phototaxis.noEvolvedUnits, 4)

    def testScototaxisNoEvolvedUnits(self):
        """Scototaxis experiment has noEvolvedUnits == 4"""
        self.assertEqual(self.exps.initializeBraiten2_2_Full_GA_scototaxis.noEvolvedUnits, 4)

    def testExistingExperimentsFitnessSign(self):
        """Existing experiment functions have fitnessSign == 1 (backward compat)"""
        for name in ['initializeBraiten2_2_Full_GA']:
            func = getattr(self.exps, name)
            self.assertEqual(func.fitnessSign, 1,
                             "%s should have fitnessSign == 1" % name)


if __name__ == '__main__':
    unittest.main()
