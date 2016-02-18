#!/usr/bin/env python

import logging
import unittest
from pprint import pformat
from timeit import Timer

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)-8s %(message)s'
)
log = logging.getLogger('zen.testpathindex')

import Globals

from Products.ZenTestCase.BaseTestCase import BaseTestCase
from Products.ZenUtils.Utils import unused
unused(Globals)

from ZenPacks.test.PathIndex.OneComponent import OneComponent
from ZenPacks.test.PathIndex.ManyComponent import ManyComponent

PROFILE = False


class TestPathIndexPerformance(BaseTestCase):

    disableLogging = False

    def test_go(self):

        self.dmd.Devices.createOrganizer('/TestPathIndex')
        self.dmd.Devices.TestPathIndex.setZenProperty('zPythonClass', 'ZenPacks.test.PathIndex.MyDevice')

        results = []
        if PROFILE:
            results.append((8000, self.dotest(8000)))
        else:
            results.append((50, self.dotest(50)))
            results.append((500, self.dotest(500)))
            results.append((1000, self.dotest(1000)))
            results.append((5000, self.dotest(5000)))
            results.append((8000, self.dotest(8000)))

        log.info(pformat(results))

    def dotest(self, num_comps):
        log.info("Running test cycle (number of components = %d)" % num_comps)

        d = self.dmd.Devices.findDevice('testpathindex')
        if d:
            log.info("  Deleting previous test device.")
            d.deleteDevice()

        device = self.dmd.Devices.TestPathIndex.createInstance('testpathindex')

        # || = containing
        #  | = non-containing
        #
        #             MyDevice
        #            //  ||   \\
        #          //    ||     \\
        #        //      ||       \\
        # ManyComponent  ||   ManyComponent  [... NUM_COMPS more]
        #         \      ||      /
        #           \    ||    /
        #           OneComponent (oc)
        #
        # In this scenario, there are many non-containing paths (getAllPaths)
        # on the bottom component.  This affects how long it takes to index,
        # and is particularly important because in most zenpacks, for every
        # object we add related to it, we will re-index it.  So index_object
        # on oc would be called NUM_COMPS times, and get slower and
        # slower as the size increased.

        oc = OneComponent("onecomponent-1")
        device.oneComponents._setObject(oc.id, oc)

        # quirk of the unit test environment?  not sure.
        if 'getAllPaths' not in device.componentSearch.indexes():
            device._createComponentSearchPathIndex()

        oc = device.oneComponents._getOb(oc.id)

        log.info("Building %d components (please wait..)" % num_comps)
        for id_ in range(1, num_comps + 1):
            c = ManyComponent("comp-%d" % id_)
            device.manyComponents._setObject(c.id, c)

        lastcomp = device.manyComponents._getOb("comp-%d" % num_comps)

        def setup():
            log.info("  Clearing existing relationships..")

            for c in oc.manyComponents():
                oc.manyComponents.removeRelation(c)

            oc.unindex_object()

            # # clean out any old relationship data from catalogs
            # if needs_reindex:
            #     log.info("    Reindexing after removals..")
            #     oc.index_object()
            #     log.info("  Finished indexing")

            log.info("  Setting up new relationships..")

            # re-add them, but don't index yet.
            for c in device.manyComponents():
                if c.id != lastcomp.id:
                    c.oneComponents.addRelation(oc)

        def stmt():
            log.info("  Running indexing test..")
            oc.index_object()
            log.info("  Finished indexing - Addding another and re-indexing.")
            lastcomp.oneComponents.addRelation(oc)

            if PROFILE:
                import pprofile
                profiler = pprofile.Profile()
                with profiler:
                    oc.index_object()
                    log.info("  Finished.")

                with open("callgrind.out", "w") as f:
                    profiler.callgrind(f)
            else:
                oc.index_object()
                log.info("  Finished.")

        timer = Timer(setup=setup,
                      stmt=stmt)

        if PROFILE:
            log.info("Running tests..")
            results = timer.repeat(1, 1)
        else:
            log.info("Running tests (3 times)..")
            results = timer.repeat(3, 1)

        log.info("Results:\n%s" % results)
        return results


def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    suite.addTest(makeSuite(TestPathIndexPerformance))
    return suite

if __name__ == "__main__":
    unittest.main()
