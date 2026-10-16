'''
@author: stefano

The classic GA setup, initializeBraiten2_2_Full_GA, builds the homeostat its
genome describes.  The self-connections are
manual: the genome sets them and the uniselector leaves them alone.
'''
from Core.HomeoUnit import HomeoUnitError
from Simulator.SimulatorBackend import SimulatorBackendHOMEO
from Simulator.HomeoExperiments import initializeBraiten2_2_Full_GA

import tempfile
import threading
import unittest

import numpy as np


class ClassicGASetupTest(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.backend = SimulatorBackendHOMEO(lock=threading.Lock(), robotName='Khepera')
        self.backend.kheperaSimulation.dataDir = self.tmp.name
        self.addCleanup(self.tmp.cleanup)
        self.addCleanup(self.backend.quit)

    def testUnitGenesAreSlicedByNoHomeoParameters(self):
        # 4 units x 5 parameters, then the connections: the unit slices and
        # the connection offset both use noHomeoParameters, and a unit given
        # 5 parameters instead of its 4 refuses them: no silent misreading
        genome = np.random.random(4 * 5 + 4 * 6)
        with self.assertRaises(HomeoUnitError):
            initializeBraiten2_2_Full_GA(genome, noHomeoParameters=5,
                                         backendSimulator=self.backend)

    def testUnitGenesAreTheFirstOnes(self):
        genome = np.random.random(4 * 4 + 4 * 6)
        hom = initializeBraiten2_2_Full_GA(genome, backendSimulator=self.backend)
        for i, unit in enumerate(hom.homeoUnits[:4]):
            self.assertEqual(unit.mass, unit.massFromWeight(genome[4 * i]))

    def testSelfConnectionsAreManual(self):
        genome = np.random.random(4 * 4 + 4 * 6)
        hom = initializeBraiten2_2_Full_GA(genome, backendSimulator=self.backend)
        for unit in hom.homeoUnits[:4]:
            self.assertEqual(unit.inputConnections[0].state, 'manual', unit.name)
            for conn in unit.inputConnections[1:]:
                self.assertEqual(conn.state, 'uniselector', unit.name)

    def testTheEyesUniselectorRedrawsItsSensorLink(self):
        """The sensor -> eye link is adaptive like every other link between
        units: the eye's uniselector redraws it"""
        genome = np.random.random(4 * 4 + 4 * 6)
        hom = initializeBraiten2_2_Full_GA(genome, backendSimulator=self.backend)
        eye = [u for u in hom.homeoUnits if u.name == 'Left Eye'][0]
        link = [c for c in eye.inputConnections if c.incomingUnit.name == 'Left Sensor'][0]
        self.assertEqual(link.state, 'uniselector')
        before = link.weight * link.switch
        eye.operateUniselector()
        self.assertNotEqual(link.weight * link.switch, before)

    def testTheUniselectorLeavesSelfConnectionsAlone(self):
        genome = np.random.random(4 * 4 + 4 * 6)
        hom = initializeBraiten2_2_Full_GA(genome, backendSimulator=self.backend)
        selfWeights = [u.inputConnections[0].weight for u in hom.homeoUnits[:4]]
        for unit in hom.homeoUnits[:4]:
            unit.operateUniselector()
        self.assertEqual([u.inputConnections[0].weight for u in hom.homeoUnits[:4]],
                         selfWeights)


class ClassicGenomeLabelsTest(unittest.TestCase):
    '''The labels of the classic connection genes name the connection each
    gene sets.'''

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.backend = SimulatorBackendHOMEO(lock=threading.Lock(), robotName='Khepera')
        self.backend.kheperaSimulation.dataDir = self.tmp.name
        self.addCleanup(self.tmp.cleanup)
        self.addCleanup(self.backend.quit)

    def testLabelsNameTheConnectionsTheGenesSet(self):
        from Helpers.GenomeDecoder import classicConnectionSources, genomePrettyPrinter, genomeDecoder
        from Helpers.StatsAnalyzer import _genome_headers
        genome = np.random.random(4 * 4 + 4 * 6)
        hom = initializeBraiten2_2_Full_GA(genome, backendSimulator=self.backend)
        units = hom.homeoUnits
        noUnits, noEvolved = len(units), initializeBraiten2_2_Full_GA.noEvolvedUnits
        actual = [(units.index(unit) + 1, units.index(conn.incomingUnit) + 1)
                  for unit in units[:noEvolved] for conn in unit.inputConnections]
        self.assertEqual(classicConnectionSources(noUnits, noEvolved), actual)
        headers = _genome_headers(noUnits, noEvolved)
        self.assertEqual(headers[2 + 4 * noEvolved:], ['W-%d-from-%d' % p for p in actual])
        self.assertIn('W-2-from-2', headers)
        text = genomePrettyPrinter(noUnits, genomeDecoder(noUnits, genome, noEvolved), noEvolved)
        self.assertIn('2 from 2: ', text)
        self.assertNotIn(' to ', text)


if __name__ == '__main__':
    unittest.main()
