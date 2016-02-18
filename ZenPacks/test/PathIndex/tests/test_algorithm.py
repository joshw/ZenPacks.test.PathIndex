#!/usr/bin/env python

import logging
import unittest
import pickle
from timeit import Timer

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)-8s %(message)s'
)
log = logging.getLogger('zen.testpathindex')


# import sys
# sys.setrecursionlimit(10000)
# import pickle
# f = open("_unindex.pickle", "w")
# pickle.dump(self._unindex, f)
# f.close()
# f = open("paths.pickle", "w")
# pickle.dump(paths, f)
# f.close()


class TestAlgorithm(unittest.TestCase):

    disableLogging = False

    def test_it(self):

        docid = 1820790055
        with open("paths.pickle") as f:
            paths = pickle.load(f)

        with open("_unindex.pickle") as f:
            _unindex = pickle.load(f)

        def old():
            unindex_paths = []

            unin = _unindex[docid]
            for oldpath in list(unin):
                if list(oldpath.split('/')) not in paths:
                    unindex_paths.append((docid, (oldpath,)))

            print "unindex_paths=%s" % unindex_paths

        def new():
            unindex_paths = []

            unin = set(_unindex[docid])
            paths_set = set(['/'.join(x) for x in paths])

            for oldpath in unin - paths_set:
                unindex_paths.append((docid, (oldpath,)))

            print "unindex_paths=%s" % unindex_paths

        log.info("[Old] Running test (2 times)..")
        timer = Timer(stmt=old)
        old_results = timer.repeat(2, 1)
        log.info("[Old] Results:\n%s" % old_results)

        log.info("[New] Running test (2 times)..")
        timer = Timer(stmt=new)
        new_results = timer.repeat(2, 1)
        log.info("[New] Results:\n%s" % new_results)


def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    suite.addTest(makeSuite(TestAlgorithm))
    return suite

if __name__ == "__main__":
    unittest.main()
