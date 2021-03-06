#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests Archive"""
from misura.canon.logger import get_module_logging
logging = get_module_logging(__name__)
import unittest
from misura.client.acquisition import MainWindow

from misura.client.tests import iutils_testing as iut
from PyQt4 import QtGui

logging.debug('Importing', __name__)

ut = False

def setUpModule():
    global ut
    from misura import utils_testing
    ut = utils_testing
    logging.debug('setUpModule', __name__)
    ut.parallel(1)


def tearDownModule():
    #ut.parallel(0)
    logging.debug('tearDownModule', __name__)


class HuAcquisition(unittest.TestCase):
    __test__ = False
    
    def setUp(self):
        self._root = ut.full_hsm()
        self.root = iut.FakeProxy(self._root)

    def tearDown(self):
        self._root.close()

# 	@unittest.skip('')
    def test_setInstrument(self):
        self.mw = MainWindow()
        logging.debug('setting instrument', self.root.hsm, self.root)
        self.mw.setInstrument(self.root.hsm, self.root)
        self.mw.show()
        QtGui.qApp.exec_()

    @unittest.skip('')
    def test_serve(self):
        p, main = None, None#ut.serve(self.root, 3880)
        p.start()
        p.join()

if __name__ == "__main__":
    unittest.main()
