#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Widget builder"""
from traceback import format_exc
import functools

from PyQt4 import QtGui

from misura.canon.logger import Log as logging

from .. import _


def build(server, remObj, prop, parent=None):
    """Build a property widget based on a property dict"""
    # FIXME: horrible! change package layout to fix this!
    from aBoolean import aBoolean
    from aButton import aButton
    from aChooser import aChooser, async_aChooser
    from aDict import aDict
    from aMeta import aMeta
    from aMaterial import aMaterial
    from aNumber import aNumber
    from aProgress import aProgress, RoleProgress
    from aString import aString
    from aScript import aScript
    from aTable import aTable
    from aProfile import aProfile
    from aTime import aTime, aDelay
    from aFileList import aFileList
    from presets import PresetManager
    from role import Role,  RoleIO
    from cycle import ThermalCycleChooser
    arg = (server, remObj, prop, parent)
    A = prop.get('attr', [])
    T = prop['type']
    if 'Hidden' in A + [T]:
        return False
    obj = False
    try:
        if T in ['String', 'ReadOnly', 'Date', 'FilePath']:
            if prop['handle'] == 'material':
                obj = aMaterial(*arg)
            else:
                obj = aString(*arg)
        elif T == 'FileList':
            obj = aFileList(*arg)
        elif T == 'TextArea':
            obj = aString(server, remObj, prop, parent, extended=True)
        elif T == 'Script':
            obj = aScript(server, remObj, prop, parent)
        elif T == 'Boolean':
            obj = aBoolean(*arg)
        elif T in ['Chooser', 'Menu', 'FileList']:
            choosers = {'motorStatus': async_aChooser}
            chooser = choosers.get(prop['handle'], aChooser)
            obj = chooser(*arg)
        elif T == 'Preset':
            obj = PresetManager(remObj, parent=parent)
        elif T in ['Integer', 'Float']:
            obj = aNumber(*arg)
        elif T == 'Time':
            if prop['kid'] == '/delay':
                obj = aDelay(*arg)
            else:
                obj = aTime(*arg)
        elif T == 'Progress':
            obj = aProgress(*arg)
        elif T == 'Meta':
            obj = aMeta(*arg)
        elif T == 'Button':
            obj = aButton(*arg)
        elif T == 'ThermalCycle':
            obj = ThermalCycleChooser(server.kiln, parent=parent)
        elif T == 'Role':
            obj = Role(*arg)
        elif T == 'RoleIO':
            obj = RoleIO(*arg)
        elif T == 'Table':
            obj = aTable(*arg)
        elif T == 'Profile':
            obj = aProfile(*arg)
        elif prop['kid'] == '/progress':
            obj = RoleProgress(*arg)
    except:
        logging.debug('Building ', prop, 'of', remObj, 'error:')
        logging.debug(format_exc())
        if obj:
            obj.hide()
            obj.close()
            del obj
        return False
    return obj


def build_aggregate_view(root, targets, devs, handle=False):
    w = QtGui.QWidget()
    lay = QtGui.QFormLayout()
    w.setLayout(lay)
    for t in targets:
        if t != handle:
            lay.addRow(QtGui.QLabel(_('Aggregation Target: ') + t))
        for fullpath in devs[t]:
            dev = root.toPath(fullpath)
            wg = build(root, dev, dev.gete(t), parent=w)
            wg.label_widget.setText(
                '{} ({}): {}'.format(dev['name'], dev['devpath'], _(wg.prop['name'])))
            lay.addRow(wg.label_widget, wg)
    win = QtGui.QScrollArea()
    win.setWidgetResizable(True)
    win.setWidget(w)
    return win



def build_aggregation_menu(root, dev, menu, target='name', win_map=False):
    if win_map is False:
        win_map = {}
    dmenu = menu.addMenu('{} ({})'.format(dev['name'], dev['devpath']))
    dmenu.addAction(_('View'), functools.partial(
        explore_child_aggregate, dev, target, win_map))
    nav_menu = dmenu.addMenu(_('Navigator'))
    f = functools.partial(
        root.navigator.build_menu_from_configuration, dev, nav_menu)
    nav_menu.menuAction().hovered.connect(f)
    return dmenu


def build_recursive_aggregation_menu(root, main_dev, aggregation, handles_map, menu, menu_map=False, win_map=False, col=None):
    """Resolve aggregation chain"""
    if menu_map is False:
        menu_map = {}  # dev:menu
    if win_map is False:
        win_map = {}
    
    fullpath = main_dev['fullpath']
    handle = handles_map.get(fullpath)
    f, targets, values, devs, foo = main_dev.collect_aggregate(aggregation, handle)
    
    if fullpath+'::list' not in menu_map:
        act = menu.addAction(_('List aggregated options'), 
                       functools.partial(list_aggregate, main_dev, aggregation, handle, win_map))
        menu_map[fullpath+'::list'] = act 
        menu.addSeparator()
        
    for t in targets:
        if col is not None:
            devs = [devs[col]]
        for fullpath in devs[t]:
            dev = root.toPath(fullpath)
            if not dev:
                continue
            t = handles_map.get(fullpath, t)
            # Special target to explicitly skip the device
            if t == '#SKIP#':
                continue
            # Get a cached menu
            dmenu = menu_map.get(fullpath, False)
            if not dmenu:
                dmenu = build_aggregation_menu(
                    root, dev, menu, target=t, win_map=win_map)
                menu_map[fullpath] = dmenu
            prop = dev.gete(t)
            agg = prop.get('aggregate', "")
            if not agg:
                continue
            dmenu.addSeparator()
            handles_map[fullpath] = t
            # Dynamically create deeper layers on request
            f = functools.partial(build_recursive_aggregation_menu,
                root, dev, agg, handles_map, dmenu, menu_map=menu_map, win_map=win_map)
            dmenu.menuAction().hovered.connect(f)


def explore_child_aggregate(dev, target, win_map={}):
    from ..conf import Interface
    win = Interface(dev.root, dev)
    win.setWindowTitle(
        _('Explore aggregation: {} ({})').format(dev['name'], dev['devpath']))
    win_map[dev['fullpath']] = win
    win.show()
    win.highlight_option(target)
    
def list_aggregate(dev, aggregate, handle, win_map={}):
    f, targets, values, devs, foo = dev.collect_aggregate(aggregate, handle)
    win = build_aggregate_view(dev.root, targets, devs, handle)
    win.setWindowTitle(_('Explore aggregation: {} ({})').format(dev['name'], handle))
    win.show()
    win_map[id(win)] = win     
    return win


if __name__ == '__main__':
    import sys
    from misura.client import iutils, network

    iutils.initApp()
    network.getConnection('localhost:3880')
    srv = network.manager.remote
    qb = QtGui.QWidget()
    lay = QtGui.QFormLayout()
    wgs = []
#    wgs.append(build(srv, srv.hsm, srv.hsm.gete('comment')))
#    wgs.append(aString(srv, srv.hsm, srv.hsm.describe()['comment'], extended=True))
#    wgs.append(aBoolean(srv, srv, srv.describe()['eq_hsm']))
#    wgs.append(aChooser(srv, srv.beholder.idx0, srv.beholder.idx0.gete('Pre-Processing:Flip')))
#    wgs.append(aNumber(srv, srv.beholder.idx0, srv.beholder.idx0.gete('brightness')))
#    wgs.append(aDict(srv, srv.hsm,srv.hsm.gete('Test_Softening')))
#    wgs.append(Role(srv, srv.hsm,srv.hsm.gete('camera')))
#    wgs.append(PresetManager(srv))
#    wgs.append(ThermalCycleChooser(srv.kiln))
#    wgs.append(ServerSelector())
#    wgs.append(ConnectionStatus())
#    wgs.append(aTable(srv, srv.simulator.flexion,srv.simulator.flexion.gete('MultiLayer_material')))
    wgs.append(aProfile(srv, srv.hsm.sample0, srv.hsm.sample0.gete('profile')))
    for wg in wgs:
        logging.debug(wg)
        lay.addRow(wg.label, wg)
    qb.setLayout(lay)
    qb.show()
    sys.exit(QtGui.qApp.exec_())
