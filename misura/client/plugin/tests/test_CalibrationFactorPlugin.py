#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Testing CalibrationFactorPlugin."""
import unittest
import os
import veusz.document as document
from misura.client import filedata
from misura.client.tests import iutils_testing as iut
from misura.client import plugin


nativem4 = os.path.join(iut.data_dir, 'calibration.h5')


class CalibrationFactorPlugin(unittest.TestCase):

    """Tests the CalibrationFactorPlugin"""

    @unittest.skip("WAITING FOR A CALIBRATION TEST FILE!!!")
    def test(self):
        # Simulate an import
        imp = filedata.OperationMisuraImport(
            filedata.ImportParamsMisura(filename=nativem4))
        doc = filedata.MisuraDocument()
        self.cmd = document.CommandInterface(doc)
        plugin.makeDefaultDoc(self.cmd)
        imp.do(doc)
        fields = {'d': 'summary/vertical/sample0/d', 'T': 'summary/kiln/T',
                  'std': 'NIST SRM738', 'start': 50, 'end': 50, 'label': 1, 'add': 1,
                  'currentwidget': '/'}
        p = plugin.CalibrationFactorPlugin()
        p.apply(self.cmd, fields)
        self.assertIn(fields['d'] + '_NIST_SRM738', doc.data)
        doc.model.refresh(force=True)


if __name__ == "__main__":
    unittest.main(verbosity=2)
