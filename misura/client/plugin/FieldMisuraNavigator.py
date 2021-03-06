#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tools and plugins for Veusz, providing Misura Thermal Analysis functionality"""
import veusz.plugins as plugins
from PyQt4 import QtGui, QtCore

# FIXME: FieldMisuraNavigator should take dataset names!


class FieldMisuraNavigator(plugins.Field):

    """Misura Navigator to select"""

    def __init__(self, name, descr=None, depth='sample', cols=1, default=None):
        """name: name of field
        descr: description to show to user
        depth: dataset, sample, file
        """
        plugins.Field.__init__(self, name, descr=descr)
        self.depth = depth
        self.cols = cols
        self.default = default
        self.model = None
        self.view = None
        self.selection = None

    def makeControl(self, doc, currentwidget):
        l = QtGui.QLabel(self.descr)
        c = QtGui.QTreeView()
        otm = doc.model
        c.setModel(otm)
        c.hideColumn(1)

        # Do the predefined selection
        obj = self.default
        if obj is None:
            return (l, c)

        self.selection = otm.index_path(obj)[-1]
        self.model = otm
        self.view = c
        self.model.modelReset.connect(self.restore_selection)
        self.restore_selection()
        return (l, c)

    def restore_selection(self):
        self.view.selectionModel().setCurrentIndex(
                    self.selection, QtGui.QItemSelectionModel.Select)
        self.view.scrollTo(self.selection)

    def getControlResults(self, cntrls):
        nav = cntrls[1]
        idx = nav.currentIndex()
        node = nav.model().data(idx, role=QtCore.Qt.UserRole)
        return node

plugins.FieldMisuraNavigator = FieldMisuraNavigator
