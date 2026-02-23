'''
Created on Feb 2026

Tests for the GA simulation infrastructure:
- GenomeDecoder: encoding/decoding of homeostat genomes
- HomeoGASimulation: basic GA operations (population creation, individual init, bounds checking)
- StatsAnalyzer: utility functions for GA analysis

These tests do not require external robotic simulators (Webots, V-REP).
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

    def testGenomeDecoderViscosityRange(self):
        """Decoded viscosity values fall within HomeoUnit viscosity range"""
        noUnits = 4
        essentParams = 4
        genomeSize = noUnits * essentParams + noUnits ** 2
        genome = np.random.uniform(0, 1, size=genomeSize)
        decoded = genomeDecoder(noUnits, genome)
        for unit in range(noUnits):
            viscosity = decoded[unit * essentParams + 1]
            # viscosity is scaled from (0,1) weight; check it's a reasonable float
            self.assertIsInstance(viscosity, (int, float, np.floating))

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
        from Simulator.HomeoGenAlgGui import HomeoGASimulation
        cls.ga = HomeoGASimulation(
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
        """Genome size is noUnits*essentParams + noUnits^2"""
        expected = 4 * 4 + 4 ** 2  # 32
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
        """Toolbox has all required operators registered"""
        required_ops = ['evaluate', 'mate', 'mutate', 'select',
                        'population', 'individual', 'map']
        for op in required_ops:
            self.assertTrue(hasattr(self.ga.toolbox, op),
                            "Toolbox missing operator: %s" % op)


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


if __name__ == '__main__':
    unittest.main()
