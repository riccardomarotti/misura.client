#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Libreria per il plotting semplice durante l'acquisizione."""
import os
from misura.canon.logger import Log as logging
import veusz.dataimport.base as base
from misura.canon import option
from proxy import getFileProxy
import collections


class LinkedMisuraFile(base.LinkedFileBase):
    mtype = 'LinkedMisuraFile'

    def __init__(self, params):
        base.LinkedFileBase.__init__(self, params)
        self.samples = []
        """List of samples contained in this file"""
        self.children = collections.OrderedDict()
        """Datasets generated by this linked file"""
        self.prefix = ''
        """Dataset prefix"""
        self.conf = option.ConfigurationProxy()
        """Additional configuration parameters"""
        self.instr = option.ConfigurationProxy()
        """Instrument configuration"""
        self.cycle = []
        """Thermal cycle"""
        self.header = []
        """Available column names"""
        self.name = 'linkedfile'
        self.instrument = False
        """Instrument which produced the file"""
        self.title = 'default'
        """File title"""
#		self.filename=params.filename
        self.basename = os.path.basename(unicode(params.filename))

    def saveToFile(self, fileobj, relpath=None):
        """Save the link to the document file."""
        params = [repr(self._getSaveFilename(relpath))]
        if self.prefix:
            params.append('prefix=' + repr(self.prefix))
        if self.instr:
            params.append('uid=' + repr(self.instr.measure['uid']))
        fileobj.write('ImportMisura(%s)\n' % (', '.join(params)))

    def createOperation(self):
        """Returns the operation needed for data reloading"""
        from operation import OperationMisuraImport
        return OperationMisuraImport
