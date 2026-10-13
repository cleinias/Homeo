'''
A recorded seed must reproduce the run: every random stream is seeded from
it, numba's included (review findings SH-03, RE-05).

Numba keeps its own random state, which np.random.seed() does not reach, and
the headless unit and connection noise draws from it.  Here a run is repeated
in one process: with numba unseeded the second run continues the first one's
stream and differs.
'''
import os
import tempfile
import unittest


def headless(hom):
    hom.slowingFactor = 0
    hom.collectsData = False
    hom._headless = True
    for unit in hom.homeoUnits:
        unit._headless = True
    return hom


def state(hom, backend):
    robot = backend.kheperaSimulation.allBodies['Khepera']
    return ([round(u.criticalDeviation, 12) for u in hom.homeoUnits],
            [round(c, 12) for c in robot.body.position])


class SeedReproducibilityTest(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        os.environ['HOMEO_DATA_DIR'] = self.tmp.name

    def tearDown(self):
        os.environ.pop('HOMEO_DATA_DIR', None)
        self.tmp.cleanup()

    def twice(self, setup):
        runs = []
        for _ in range(2):
            hom, backend, _ = setup()
            headless(hom).runFor(300)
            backend.kheperaSimulation.saveTrajectory()
            runs.append(state(hom, backend))
        return runs

    def testAshbyPhototaxis(self):
        import HomeoExperiments.KheperaExperiments.phototaxis_braitenberg2_Ashby as A
        for kind in ('ashby', 'continuous'):
            with self.subTest(uniselector=kind):
                first, second = self.twice(
                    lambda: A.setup_phototaxis(seed=123, uniselector_type=kind))
                self.assertEqual(first, second)

    def testBraitenberg3c(self):
        import HomeoExperiments.KheperaExperiments.braitenberg3c_control as C
        first, second = self.twice(lambda: C.setup_braiten3c_control(seed=123))
        self.assertEqual(first, second)


if __name__ == '__main__':
    unittest.main()
