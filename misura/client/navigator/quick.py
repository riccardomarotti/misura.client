#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tree visualization of opened misura Files in a document."""
from misura.canon.logger import Log as logging
from veusz.dialogs.plugin import PluginDialog

from veusz import document
from PyQt4.QtCore import Qt
from PyQt4 import QtGui, QtCore

import functools
from .. import _
from ..filedata import MisuraDocument
from ..filedata import OperationMisuraImport
from ..filedata import DatasetEntry
from ..filedata import getFileProxy
from ..filedata import axis_selection
import numpy as np

ism = isinstance


def docname(ds):
    """Get dataset name by searching in parent document data"""
    for name, obj in ds.document.data.iteritems():
        if obj == ds:
            return name
    return None


def node(func):
    """Decorator for functions which should get currentIndex node if no arg is passed"""
    @functools.wraps(func)
    def node_wrapper(self, *a, **k):
        n = False
        keyword = True
        # Get node from named parameter
        if k.has_key('node'):
            n = k['node']
        # Or from the first unnamed argument
        elif len(a) >= 1:
            n = a[0]
            keyword = False
        # If node was not specified, get from currentIndex
        if n is False:
            n = self.model().data(self.currentIndex(), role=Qt.UserRole)
        elif isinstance(n, document.Dataset):
            n = docname(n)

        # If node was expressed as/converted to string, get its corresponding
        # tree entry
        if isinstance(n, str) or isinstance(n, unicode):
            logging.debug('%s %s', 'traversing node', n)
            n = str(n)
            n = self.model().tree.traverse(n)

        if keyword:
            k['node'] = n
        else:
            a = list(a)
            a[0] = n
            a = tuple(a)
        logging.debug(
            '%s %s %s %s', '@node with', n, type(n), isinstance(n, unicode))
        return func(self, *a, **k)
    return node_wrapper


def nodes(func):
    """Decorator for functions which should get a list of currentIndex nodes if no arg is passed"""
    @functools.wraps(func)
    def node_wrapper(self, *a, **k):
        n = []
        keyword = True
        # Get node from named parameter
        if k.has_key('nodes'):
            n = k['nodes']
        # Or from the first unnamed argument
        elif len(a) >= 1:
            n = a[0]
            keyword = False
        # If node was not specified, get from currentIndex
        if not len(n):
            n = []
            for idx in self.selectedIndexes():
                n0 = self.model().data(idx, role=Qt.UserRole)
                n.append(n0)
        if keyword:
            k['nodes'] = n
        else:
            a = list(a)
            a[0] = n
            a = tuple(a)
        logging.debug(
            '%s %s %s %s %s', '@nodes with', n, type(n), isinstance(n, unicode))
        return func(self, *a, **k)
    return node_wrapper

class QuickOps(object):

    """Quick interface for operations on datasets"""
    _mainwindow = False

    @property
    def mainwindow(self):
        if self._mainwindow is False:
            return self
        return self._mainwindow


    @node
    def deleteChildren(self, node=False):
        """Delete all children of node."""
        logging.debug('%s %s %s', 'deleteChildren', node, node.children)
        for sub in node.children.values():
            if not sub.ds:
                continue
            self.deleteData(sub)
#
    def _load(self, node):
        """Load or reload a dataset"""
        op = OperationMisuraImport.from_dataset_in_file(
            node.path, node.linked.filename)
        self.doc.applyOperation(op)

    @node
    def load(self, node=False):
        logging.debug('%s %s', 'load', node)
        if node.linked is None:
            logging.debug('%s %s', 'Cannot load: no linked file!', node)
            return
        if not node.linked.filename:
            logging.debug('%s %s', 'Cannot load: no filename!', node)
            return
        if len(node.data) > 0:
            logging.debug('%s %s', 'Unloading', node.path)
            # node.ds.data = []
            ds = node.ds
            self.deleteData(node=node)
            # self.deleteData(node=node, remove_dataset=False, recursive=False)
            ds.data = np.array([])
            self.doc.available_data[node.path] = ds
            self.model().pause(False)
            self.doc.setModified()

            return
        self._load(node)
        
    @node
    def plot(self, node=False):
        """Slot for plotting by temperature and time the currently selected entry"""
        pt = self.model().is_plotted(node.path)
        if pt:
            logging.debug('%s %s', 'UNPLOTTING', node)
            self.deleteData(node=node, remove_dataset=False, recursive=False)
            return
        # Load if no data
        if len(node.data) == 0:
            self.load(node)
        yname = node.path

        from misura.client import plugin
        # If standard page, plot both T,t
        page = self.model().page
        if page.startswith('/temperature/') or page.startswith('/time/'):
            logging.debug('%s %s', 'Quick.plot', page)
            # Get X temperature names
            xnames = self.xnames(node, page='/temperature')
            assert len(xnames) > 0
            p = plugin.PlotDatasetPlugin()
            p.apply(self.cmd, {
                    'x': xnames, 'y': [yname] * len(xnames), 'currentwidget': '/temperature/temp'})

            # Get time datasets
            xnames = self.xnames(node, page='/time')
            assert len(xnames) > 0
            p = plugin.PlotDatasetPlugin()
            p.apply(self.cmd, {
                    'x': xnames, 'y': [yname] * len(xnames), 'currentwidget': '/time/time'})
        else:
            if page.startswith('/report'):
                page = page + '/temp'
            logging.debug('%s %s', 'Quick.plot on currentwidget', page)
            xnames = self.xnames(node, page=page)
            assert len(xnames) > 0
            p = plugin.PlotDatasetPlugin()
            p.apply(
                self.cmd, {'x': xnames, 'y': [yname] * len(xnames), 'currentwidget': page})
        self.doc.setModified()

    @node
    def deleteData(self, node=False, remove_dataset=True, recursive=True):
        """Delete a dataset and all depending graphical widgets."""
        self.model().pause(0)
        if not node:
            return True
        node_path = node.path
        # Remove and exit if dataset was only in available_data
        if self.doc.available_data.has_key(node_path):
            self.doc.available_data.pop(node_path)
            if not self.doc.data.has_key(node_path):
                return True
        # Remove and exit if no plot is associated
        if not self.model().plots['dataset'].has_key(node_path):
            if remove_dataset:
                self.doc.deleteDataset(node_path)
                self.doc.setModified()

            return True

        plots = self.model().plots['dataset'][node_path]
        # Collect involved graphs
        graphs = []
        # Collect plots to be removed
        remplot = []
        # Collect axes which should be removed
        remax = []
        # Collect objects which refers to xData or yData
        remobj = []
        # Remove associated plots
        for p in plots:
            p = self.doc.resolveFullWidgetPath(p)
            g = p.parent
            if g not in graphs:
                graphs.append(g)
            remax.append(g.getChild(p.settings.yAxis))
            remplot.append(p)

        # Check if an ax is referenced by other plots
        for g in graphs:
            for obj in g.children:
                if obj.typename == 'xy':
                    y = g.getChild(obj.settings.yAxis)
                    if y is None:
                        continue
                    # If the axis is used by an existent plot, remove from the
                    # to-be-removed list
                    if y in remax and obj not in remplot:
                        remax.remove(y)
                    continue
                # Search for xData/yData generic objects

                for s in ['xData', 'yData', 'xy']:
                    o = getattr(obj.settings, s, None)
                    refobj = g.getChild(o)
                    if refobj is None:
                        continue
                    if refobj not in plots + [node_path]:
                        continue
                    if obj not in remplot + remax + remobj:
                        remobj.append(obj)

        # Remove object and unreferenced axes
        for obj in remplot + remax + remobj:
            logging.debug('%s %s %s', 'Removing obj', obj.name, obj.path)
            obj.parent.removeChild(obj.name)
        # Finally, delete dataset
        if remove_dataset:
            self.doc.deleteDataset(node_path)
            logging.debug('%s %s', 'deleted', node_path)

        # Recursive call over derived datasets
        if recursive:
            for sub in node.children.itervalues():
                self.deleteData(sub, remove_dataset, recursive)

        self.doc.setModified()

        return True

    @nodes
    def deleteDatas(self, nodes=[]):
        """Call deleteData on each selected node"""
        for n in nodes:
            self.deleteData(node=n)


    def widget_path_for(self, node):
        result = '/'
        full_path = self.doc.model.is_plotted(node.path)
        if full_path:
            result = full_path[0]

        return result

    def xnames(self, y, page=False):
        """Get X dataset name for Y node y, in `page`"""
        logging.debug('%s %s %s %s', 'XNAMES', y, type(y), y.path)
        logging.debug('%s %s', 'y.linked', y.linked)
        logging.debug('%s %s', 'y.parent.linked', y.parent.linked)

        if page == False:
            page = self.model().page
        lk = y.linked if y.linked else y.parent.linked

        xname = axis_selection.get_best_x_for(y.path, lk.prefix, self.doc.data, page)

        return [xname]

    def dsnode(self, node):
        """Get node and corresponding dataset"""
        ds = node
        if isinstance(node, DatasetEntry):
            ds = node.ds
        return ds, node

