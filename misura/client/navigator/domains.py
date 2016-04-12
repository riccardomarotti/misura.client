#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tree visualization of opened misura Files in a document."""
from misura.canon.logger import Log as logging
from misura.canon.dataimport import navigator_domains

from veusz.dialogs.plugin import PluginDialog

from veusz import document
from PyQt4.QtCore import Qt
from PyQt4 import QtGui

import functools
from .. import _
from ..filedata import MisuraDocument
from ..filedata import DatasetEntry
from ..filedata import getFileProxy

ism = isinstance


from .quick import node, nodes


class NavigatorDomain(object):
    def __init__(self, navigator):
        self.navigator = navigator
        
    @property
    def model(self):
        """Hack to allow nodes() decorator"""
        return self.navigator.model
    
    def currentIndex(self, *a, **k):
        return self.navigator.currentIndex(*a, **k)
    
    def selectedIndexes(self, *a, **k):
        return self.navigator.selectedIndexes(*a, **k)
    
    @property
    def mainwindow(self):
        return self.navigator.mainwindow
    
    @property
    def doc(self):
        return self.navigator.doc
    
    def xnames(self,*a,**k):
        return self.navigator.xnames(*a,**k)
    
    def dsnode(self, *a, **k):
        return self.navigator.dsnode(*a, **k)
    
    def plot(self, *a, **k):
        return self.navigator.plot(*a, **k)
    
    def is_loaded(self, node):
        return (node.ds is not False) and (len(node.ds) > 0)
    
    def is_plotted(self, node):
        if not self.is_loaded(node):
            return False
        return len(self.model().is_plotted(node.path)) > 0
        
    def check_node(self, node):
        """Check if node pertain to this domain"""
        return True
    
    def check_nodes(self, nodes):
        """Check if multiple nodes selection pertain to this domain"""
        return True
    
    def add_file_menu(self, menu, node):
        return True
    
    def build_file_menu(self, menu, node):
        if not self.check_node(node):
            return False
        return self.add_file_menu(menu, node)  
    
    def add_sample_menu(self, menu, node):
        return True
    
    def build_sample_menu(self, menu, node):
        if not self.check_node(node):
            return False
        return self.add_sample_menu(menu, node)  
    
    def add_group_menu(self, menu, node):
        return True
    
    def build_group_menu(self, menu, node):
        if not self.check_node(node):
            return False
        return self.add_group_menu(menu, node)  
    
    def add_dataset_menu(self, menu, node):
        return True
    
    def build_dataset_menu(self, menu, node):
        if not self.check_node(node):
            return False
        return self.add_dataset_menu(menu, node)  
    
    def add_derived_dataset_menu(self, menu, node):
        return True
    
    def build_derived_dataset_menu(self, menu, node):
        if not self.check_node(node):
            return False
        return self.add_derived_dataset_menu(menu, node)  
    
    def add_multiary_menu(self, menu, nodes):
        return True
    
    def build_multiary_menu(self, menu, nodes):
        if not self.check_nodes(node):
            return False
        return self.add_multiary_menu(menu, nodes)
    
class DataNavigatorDomain(NavigatorDomain):
        
    @node
    def change_rule(self, node=False, act=0):
        """Change current loading rule"""
        # TODO: change_rule
        pass

    @node
    def viewFile(self, node=False):
        if not node.linked:
            return False
        doc = MisuraDocument(node.linked.filename)
        from misura.client import browser
        browser.TestWindow(doc).show()

    @node
    def closeFile(self, node=False):
        # FIXME: model no longer have a "tests" structure.
        lk = node.linked
        if not lk:
            logging.debug('%s %s', 'Node does not have linked file', node.path)
            return False
        for ds in self.doc.data.values():
            if ds.linked == lk:
                self.navigator.deleteData(ds)

        self.model().refresh(True)

    @node
    def reloadFile(self, node=False):
        logging.debug('%s', 'RELOADING')
        if not node.linked:
            return False
        logging.debug('%s', node.linked.reloadLinks(self.doc))


    def load_version(self, LF, version):
        # FIXME: VERSIONING!
        logging.debug('%s', 'LOAD VERSION')
        LF.params.version = version
        LF.reloadLinks(self.doc)

        fl = self.model().files
        logging.debug('%s %s', 'got linked files', self.model().files[:])

    @node
    def commit(self, node=False):
        """Write datasets to linked file. """
        name, st = QtGui.QInputDialog.getText(
            self, "Version Name", "Choose a name for the data version you are saving:")
        if not st:
            logging.debug('%s', 'Aborted')
            return
        logging.debug('%s %s', 'Committing data to', node.filename)
        node.commit(unicode(name))

    def add_load(self, menu, node):
        """Add load/unload action"""
        self.act_load = menu.addAction(_('Load'), self.navigator.load)
        self.act_load.setCheckable(True)
        is_loaded = True
        if node.linked is None:
            self.act_load.setVisible(False)
        else:
            is_loaded = (node.ds is not False) and (len(node.ds) > 0)
            self.act_load.setChecked(is_loaded)
        return is_loaded
    
    @node
    def keep(self, node=False):
        """Inverts the 'keep' flag on the current dataset,
        causing it to be saved (or not) on the next file commit."""
        ds, node = self.dsnode(node)
        cur = getattr(ds, 'm_keep', False)
        ds.m_keep = not cur
    
    def add_keep(self, menu, node):
        temporary_disabled = True
        return temporary_disabled
        """Add on-file persistence action"""
        self.act_keep = menu.addAction(
            _('Saved on test file'), self.keep)
        self.act_keep.setCheckable(True)
        self.act_keep.setChecked(node.m_keep)
        
    @node
    def save_on_current_version(self, node=False):
        proxy = getFileProxy(node.linked.filename)
        prefix = node.linked.prefix
        try:
            proxy.save_data(node.ds.m_col, node.ds.data, self.model().doc.data[prefix + "t"].data)
        except Exception as e:
            message = "Impossible to save data.\n\n" + str(e)
            QtGui.QMessageBox.warning(None,'Error', message)
        proxy.close()
        
    @node
    def overwrite(self, node=False):
        """Overwrite the parent dataset with a derived one."""
        ds, node = self.dsnode()
        from misura.client import plugin
        p = plugin.OverwritePlugin(
            a=node.parent.path, b=node.path, delete=True)
        d = PluginDialog(self.mainwindow, self.doc, p, plugin.OverwritePlugin)
        self.mainwindow.showDialog(d)
    
    def add_rules(self, menu, node):
        """Add loading rules sub menu"""
        menu = menu.addMenu(_('Rules'))
        self.act_rule = []
        self.func_rule = []

        def gen(name, idx):
            f = functools.partial(self.change_rule, act=1)
            act = menu.addAction(_(name), f)
            act.setCheckable(True)
            self.act_rule.append(act)
            self.func_rule.append(f)

        gen('Ignore', 1)
        gen('Force', 2)
        gen('Load', 3)
        gen('Plot', 4)

        # Find the highest matching rule
        r = confdb.rule_dataset(node.path, latest=True)
        if r:
            r = r[0]
        if r > 0:
            self.act_rule[r - 1].setChecked(True)
        
    def add_file_menu(self, menu, node):
        menu.addAction(_('View'), self.viewFile)
        menu.addAction(_('Reload'), self.reloadFile)
        menu.addAction(_('Close'), self.closeFile)
        return True
        
    def add_sample_menu(self, menu, node):
        menu.addAction(_('Delete'), self.navigator.deleteChildren)
        return True
             
    def add_dataset_menu(self, menu, node):
        self.add_load(menu, node)
        self.add_keep(menu, node)
        menu.addAction(('Save on current version'), self.save_on_current_version)
        self.add_rules(menu, node)
        menu.addAction(_('Delete'), self.navigator.deleteData)
        return True
    
    def add_derived_dataset_menu(self, menu, node):
        self.add_keep(menu, node)
        menu.addAction(_('Delete'), self.navigator.deleteData)
        # menu.addAction(_('Overwrite parent'), self.overwrite)
        
    def add_multiary_menu(self, menu, nodes):
        menu.addAction(_('Delete selection'), self.navigator.deleteDatas)
        
from ..clientconf import confdb
class PlottingNavigatorDomain(NavigatorDomain):
    def check_node(self, node):
        if not node.ds:
            return False
        is_loaded = len(node.ds) > 0
        return is_loaded
    
    @node
    def thermalLegend(self, node=False):
        """Write thermal cycle onto a text label"""
        from misura.client import plugin
        p = plugin.ThermalCyclePlugin(test=node)
        d = PluginDialog(
            self.mainwindow, self.doc, p, plugin.ThermalCyclePlugin)
        self.mainwindow.showDialog(d)
    
    @node
    def intercept(self, node=False):
        """Intercept all curves derived/pertaining to the current object"""
        if ism(node, DatasetEntry):
            dslist = [node.path]
        elif hasattr(node, 'datasets'):
            # FIXME: needs paths
            dslist = node.children.keys()
        else:
            dslist = []
        from misura.client import plugin
        xnames = self.xnames(node, page='/time')
        xnames.append('')
        p = plugin.InterceptPlugin(target=dslist, axis='X', critical_x=xnames[0])
        d = PluginDialog(self.mainwindow, self.doc, p, plugin.InterceptPlugin)
        self.mainwindow.showDialog(d)   
        
    def add_plotted(self, menu, node, is_plotted=False):
        """Add plot/unplot action"""
        self.act_plot = menu.addAction(_('Plot'), self.plot)
        self.act_plot.setCheckable(True)
        self.act_plot.setChecked(is_plotted)
    
    @node
    def colorize(self, node=False):
        """Set/unset color markers."""
        plotpath = self.model().is_plotted(node.path)
        if not len(plotpath) > 0:
            return False
        x = self.xnames(node)[0]
        from misura.client import plugin
        p = plugin.ColorizePlugin(curve=plotpath[0], x=x)
        d = PluginDialog(self.mainwindow, self.doc, p, plugin.ColorizePlugin)
        self.mainwindow.showDialog(d)
        

    @node
    def save_style(self, node=False):
        """Save current curve color, style, marker and axis ranges and scale."""
        # TODO: save_style
        pass

    @node
    def delete_style(self, node=False):
        """Delete style rule."""
        # TODO: delete_style
        pass
    
    style_menu = False
    def add_styles(self, menu, node):
        """Styles sub menu"""
        plotpath = self.model().is_plotted(node.path)
        if not len(plotpath) > 0:
            return
        if not self.style_menu:
            self.style_menu = menu.addMenu(_('Style'))
        self.style_menu.clear()
        
        wg = self.doc.resolveFullWidgetPath(plotpath[0])
        self.act_color = self.style_menu.addAction(
            _('Colorize'), self.colorize)
        self.act_color.setCheckable(True)

        self.act_save_style = self.style_menu.addAction(
            _('Save style'), self.save_style)
        self.act_save_style.setCheckable(True)
        self.act_delete_style = self.style_menu.addAction(
            _('Delete style'), self.delete_style)
        if len(wg.settings.Color.points):
            self.act_color.setChecked(True)
        if confdb.rule_style(node.path):
            self.act_save_style.setChecked(True)
        
    def build_file_menu(self, menu, node):
        menu.addAction(_('Thermal Legend'), self.thermalLegend)
        menu.addAction(_('Intercept all curves'), self.intercept)
        return True
        
    def add_sample_menu(self, menu, node):
        menu.addAction(_('Intercept all curves'), self.intercept)
        menu.addAction(_('Delete'), self.navigator.deleteChildren)
        return True
             
    def add_dataset_menu(self, menu, node):
        is_plotted = self.is_plotted(node) >0 
        self.add_plotted(menu, node, is_plotted)
        if is_plotted:
            menu.addAction(_('Intercept this curve'), self.intercept)
            self.add_styles(menu, node)
        return True
        
    add_derived_dataset_menu = add_dataset_menu
    
    
    @nodes
    def synchronize(self, nodes=[]):
        from misura.client import plugin

        reference_curve_full_path = self.navigator.widget_path_for(nodes[0])
        translating_curve_full_path = self.navigator.widget_path_for(nodes[1])

        sync_plugin = plugin.SynchroPlugin(
            reference_curve_full_path, translating_curve_full_path)

        dialog = PluginDialog(
            self.mainwindow, self.doc, sync_plugin, plugin.SynchroPlugin)
        self.mainwindow.showDialog(dialog)

    def add_multiary_menu(self, menu, nodes):
        menu.addAction(_('Synchronize curves'), self.synchronize)
    
class MathNavigatorDomain(NavigatorDomain):
    def check_node(self, node):
        if not node.ds:
            return False
        istime = node.path == 't' or node.path.endswith(':t')
        is_loaded = len(node.ds) > 0
        return (not istime) and is_loaded
    
    @node
    def edit_dataset(self, node=False):
        """Slot for opening the dataset edit window on the currently selected entry"""
        ds, y = self.dsnode(node)
        name = node.path
        logging.debug('%s %s', 'name', name)
        dialog = self.mainwindow.slotDataEdit(name)
        if ds is not y:
            dialog.slotDatasetEdit()

    @node
    def smooth(self, node=False):
        """Call the SmoothDatasetPlugin on the current node"""
        ds, node = self.dsnode(node)
        w = max(5, len(ds.data) / 50)
        from misura.client import plugin
        p = plugin.SmoothDatasetPlugin(
            ds_in=node.path, ds_out=node.m_name + '/sm', window=int(w))
        d = PluginDialog(
            self.mainwindow, self.doc, p, plugin.SmoothDatasetPlugin)
        self.mainwindow.showDialog(d)

    @node
    def coefficient(self, node=False):
        """Call the CoefficientPlugin on the current node"""
        ds, node = self.dsnode(node)
        w = max(5, len(ds.data) / 50)
        ds_x = self.xnames(node, '/temperature')[0]
        ini = getattr(ds, 'm_initialDimension', 0)
        if getattr(ds, 'm_percent', False):
            ini = 0. # No conversion if already percent
        from misura.client import plugin
        p = plugin.CoefficientPlugin(
            ds_y=node.path, ds_x=ds_x, ds_out=node.m_name + '/cf', smooth=w, percent=ini)
        d = PluginDialog(
            self.mainwindow, self.doc, p, plugin.CoefficientPlugin)
        self.mainwindow.showDialog(d)

    @node
    def derive(self, node=False):
        """Call the DeriveDatasetPlugin on the current node"""
        ds, node = self.dsnode(node)
        w = max(5, len(ds.data) / 50)

        ds_x = self.xnames(node, "/time")[0]  # in current page

        from misura.client import plugin
        p = plugin.DeriveDatasetPlugin(
            ds_y=node.path, ds_x=ds_x, ds_out=node.m_name + '/d', smooth=w)
        d = PluginDialog(
            self.mainwindow, self.doc, p, plugin.DeriveDatasetPlugin)
        self.mainwindow.showDialog(d)
        
        
    def add_dataset_menu(self, menu, node):
        menu.addAction(_('Edit'), self.edit_dataset)
        menu.addAction(_('Smoothing'), self.smooth)
        menu.addAction(_('Derivatives'), self.derive)
        menu.addAction(_('Linear Coefficient'), self.coefficient)
        
    @nodes
    def correct(self, nodes=[]):
        """Call the CurveOperationPlugin on the current nodes"""
        ds0, node0 = self.dsnode(nodes[0])
        T0 = node0.linked.prefix + 'kiln/T'
        ds1, node1 = self.dsnode(nodes[1])
        T1 = node1.linked.prefix + 'kiln/T'
        from misura.client import plugin
        p = plugin.CurveOperationPlugin(
            ax=T0, ay=node0.path, bx=T1, by=node1.path)
        # TODO: TC comparison?
        d = PluginDialog(
            self.mainwindow, self.doc, p, plugin.CurveOperationPlugin)
        self.mainwindow.showDialog(d)
        
    def add_multiary_menu(self, menu, nodes):
        menu.addAction(_('Correct'), self.correct)
        
        
class MeasurementUnitsNavigatorDomain(NavigatorDomain):
    def check_node(self, node):
        if not node.ds:
            return False
        return len(node.ds) > 0

    @node
    def setInitialDimension(self, node=False):
        """Invoke the initial dimension plugin on the current entry"""
        logging.debug('%s %s %s', 'Searching dataset name', node, node.path)
        n = self.doc.datasetName(node.ds)
        ini = getattr(node.ds, 'm_initialDimension', False)
        if not ini:
            ini = 100.
        xname = self.xnames(node)[0]
        logging.debug('%s %s %s', 'Invoking InitialDimensionPlugin', n, ini)
        from misura.client import plugin
        p = plugin.InitialDimensionPlugin(ds=n, ini=ini, ds_x = xname)
        d = PluginDialog(
            self.mainwindow, self.doc, p, plugin.InitialDimensionPlugin)
        self.mainwindow.showDialog(d)

    @node
    def convertPercentile(self, node=False):
        """Invoke the percentile plugin on the current entry"""
        n = self.doc.datasetName(node.ds)
        from misura.client import plugin
        p = plugin.PercentilePlugin(ds=n, propagate=True)
        d = PluginDialog(self.mainwindow, self.doc, p, plugin.PercentilePlugin)
        self.mainwindow.showDialog(d)

    @node
    def set_unit(self, node=False, convert=False):
        logging.debug('%s %s %s %s', 'set_unit:', node, node.unit, convert)
        if node.unit == convert or not convert or not node.unit:
            logging.debug('%s', 'set_unit: Nothing to do')
            return
        n = self.doc.datasetName(node.ds)
        from misura.client import plugin
        p = plugin.UnitsConverterTool(ds=n, convert=convert, propagate=True)
        d = PluginDialog(
            self.mainwindow, self.doc, p, plugin.UnitsConverterTool)
        self.mainwindow.showDialog(d)
    
    def add_percentile(self, menu, node):
        """Add percentile conversion action"""
        self.act_percent = menu.addAction(
            _('Set Initial Dimension'), self.setInitialDimension)
        self.act_percent = menu.addAction(
            _('Percentile'), self.convertPercentile)
        self.act_percent.setCheckable(True)
        self.act_percent.setChecked(node.m_percent)
        
    def add_unit(self, menu, node):
        """Add measurement unit conversion menu"""
        self.units = {}
        u = node.unit
        if not u:
            return
        un = menu.addMenu(_('Units'))
        kgroup, f, p = units.get_unit_info(u, units.from_base)
        same = units.from_base.get(kgroup, {u: lambda v: v}).keys()
        logging.debug('%s %s', kgroup, same)
        for u1 in same:
            p = functools.partial(self.set_unit, convert=u1)
            act = un.addAction(_(u1), p)
            act.setCheckable(True)
            if u1 == u:
                act.setChecked(True)
            # Keep reference
            self.units[u1] = (act, p)
        
    def add_dataset_menu(self, menu, node):
        self.add_percentile(menu, node)
        self.add_unit(menu, node)
        
        
navigator_domains.update((PlottingNavigatorDomain, MathNavigatorDomain, DataNavigatorDomain,))
