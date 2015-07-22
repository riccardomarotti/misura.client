#!/usr/bin/python
# -*- coding: utf-8 -*-
from misura.canon.logger import Log as logging
from threading import Lock
from traceback import format_exc

from .. import widgets, _
from ..live import registry
from ..database import ProgressBar
from misura.canon.csutil import lockme

from PyQt4 import QtGui, QtCore
qm = QtGui.QMessageBox


class Controls(QtGui.QToolBar):

    """Start/stop toolbar"""
    mute = False
    motor = False
    coolAct = False
    isRunning = None
    """Local running status"""
    closingTest = 0
    """Local closingTest status"""
    paused = False
    """Do not update actions"""
    _lock = False
    """Multithreading lock"""
    started = QtCore.pyqtSignal()
    stopped = QtCore.pyqtSignal()
    stopped_nosave = QtCore.pyqtSignal()
    closingTest_kid = False
    stop_mode = True
    stop_message = ''

    def __init__(self, remote, parent=None):
        QtGui.QToolBar.__init__(self, parent)
        self._lock = Lock()
        self.remote = remote
        logging.debug('%s', 'Controls: init')
        self.server = remote.parent()
        self.iniAct = self.addAction('New', self.new)
        self.startAct = self.addAction('Start', self.start)
        self.stopAct = self.addAction('Stop', self.stop)
        self.name = self.remote['devpath'].lower()

        if self.name != 'kiln':
            self.coolAct = self.addAction('Cool', self.stop_kiln)

        logging.debug('%s %s', 'Controls: ', self.name)
        if self.name == 'post':
            self.addAction('Machine Database', parent.showIDB)
            self.addAction('Test File', parent.openFile)
            self.addAction('Misura3 Database', parent.showDB3)
        self.isRunning = self.server['isRunning']
        self.closingTest = self.remote['closingTest']
        self.updateActions()
        logging.debug('%s', 'Controls end init')
        self.stopped.connect(self.hide_prog)
        self.stopped_nosave.connect(self.hide_prog)
        self.started.connect(self.hide_prog)
        self.connect(self, QtCore.SIGNAL('aboutToShow()'), self.updateActions)
        self.connect(
            self, QtCore.SIGNAL('warning(QString,QString)'), self.warning)
        self.closingTest_kid = self.remote.gete('closingTest')['kid']
        registry.system_kids.add(self.closingTest_kid)
        registry.system_kid_changed.connect(self.system_kid_slot)

    @lockme
    def system_kid_slot(self, kid):
        """Slot processing system_kid_changed signals from KidRegistry.
        Calls updateActions if /isRunning is received."""
        logging.debug('%s %s', 'system_kid_slot: received', kid)
        if kid == '/isRunning':
            #			if not self._lock.acquire(False):
            #				logging.debug("Controls.system_kid_slot: Impossible to acquire lock")
            #				return
            self.updateActions()
#			self._lock.release()
        elif kid == self.closingTest_kid:
            if self.remote['closingTest'] != 0:
                self.closingTest = self.remote['closingTest']
                logging.debug(
                    'Waiting closingTest... %s', self.remote['closingTest'])
                return
            if self.closingTest == 0:
                print 'Local already closed!'
                return
            if self.server['isRunning']:
                print 'Remote isRunning!'
                return
            endStatus = self.remote.measure['endStatus']
            if self.stop_mode:
                self.stopped.emit()
                self.emit(QtCore.SIGNAL('warning(QString,QString)'),
                          _('Measurement stopped and saved'),
                          _('Current measurement was stopped and its data has been saved. \n') + endStatus)
            else:
                self.stopped_nosave.emit()
                self.emit(QtCore.SIGNAL('warning(QString,QString)'),
                          _('Measurement data discarded!'),
                          _('Current measurement was stopped and its data has been deleted. \n') + endStatus)
            self.isRunning = False

    @property
    def tasks(self):
        """Shortcut to pending tasks dialog"""
        return registry.tasks

    def updateActions(self):
        """Update status visualization and notify third-party changes"""
        if self.paused:
            return self.isRunning
        if self.parent().fixedDoc:
            return False
        # Always reconnect in case it is called in a different thread
        rem = self.server.copy()
        rem.connect()
        r = rem['isRunning']
        r = bool(r)
        self.stopAct.setEnabled(r)
        if self.coolAct:
            self.coolAct.setEnabled(r)
        self.startAct.setEnabled(r ^ 1)
        self.iniAct.setEnabled(r ^ 1)
        if self.isRunning is not None and self.isRunning != r:
            sig = False
            logging.debug(
                '%s %s %s', 'Controls.updateActions', self.isRunning, r)
            if r:
                msg = 'A new test was started'
                sig = self.started
            else:
                msg = 'Finished test'
#				sig=self.stopped
            QtGui.QMessageBox.warning(self, msg, msg)
            # Emit after message
            if sig:
                sig.emit()
#		# Locally remember remote status
#		self.isRunning=r
        return r

    def enterEvent(self, ev):
        self.updateActions()
        return

    def _async(self, method, *a, **k):
        """Execute `method` in global thread pool, passing `*a`,`**k` arguments."""
        r = widgets.RunMethod(method, *a, **k)
        QtCore.QThreadPool.globalInstance().start(r)
        return True

    def _sync(self, method, *a, **k):
        """Synchronously execute `method`,passing `*a`,`**k` arguments."""
        method(*a, **k)
        return True

    def warning(self, title, msg=False):
        """Display a warning message box and update actions"""
        if not self.mute:
            if not msg:
                msg = title
            qm.warning(self, title, msg)
        self.updateActions()

    _prog = False

    @property
    def prog(self):
        if not self._prog:
            self._prog = ProgressBar()
        return self._prog

    msg = ''

    def show_prog(self, msg):
        self.msg = msg
        self.tasks.jobs(0, msg)
        self.tasks.setFocus()

    def hide_prog(self):
        self.tasks.done(self.msg)

    def _start(self):
        # Renovate the connection: we are in a sep thread!
        self.paused = True
        rem = self.remote.copy()
        rem.connect()
        try:
            msg = rem.start_acquisition()
            self.started.emit()
        except:
            msg = format_exc()
            logging.debug('%s', msg)
        self.paused = False
        self.started.emit()
        if not self.mute:
            self.emit(QtCore.SIGNAL('warning(QString,QString)'),
                      _('Start Acquisition'),
                      _('Result: ') + msg)

    def start(self):
        self.mainWin = self.parent()
        self.mDock = self.mainWin.measureDock
        self.measureTab = self.mDock.widget()
        self.measureTab.checkCurve()
        if not self.validate():
            return False
        if self.updateActions():
            self.warning(
                _('Already running'), _('Acquisition is already running. Nothing to do.'))
            return False
        self.isRunning = True
        self._async(self._start)
        self.show_prog(_("Starting new test"))
        return True

    def _stop(self, mode):
        self.paused = True
        rem = self.remote.copy()
        rem.connect()
        try:
            self.stop_message = rem.stop_acquisition(mode)
        except:
            self.stop_message = format_exc()
        self.stop_mode = mode
        self.paused = False

    def stop(self):
        if not self.updateActions():
            self.warning(
                _('Already stopped'), _('No acquisition is running. Nothing to do.'))
            return
        if not self.mute:
            btn = qm.question(self, _('Save the test'),  _('Do you want to save this measurement?'),
                              qm.Save | qm.Discard | qm.Abort, qm.Save)
            if btn == qm.Abort:
                qm.information(self, _('Nothing done.'),  _(
                    'Action aborted. The measurement maybe still running.'))
                return False
        else:
            btn = qm.Discard
        self.isRunning = False
        if btn == qm.Discard:
            self.stopped_nosave.emit()
            self._async(self._stop, False)
        else:
            self._async(self._stop, True)
        self.show_prog("Stopping current test")

    def stop_kiln(self):
        """Stop thermal cycle without interrupting the acquisition"""
        # Disable auto-stop on thermal cycle end
        self.remote.measure.setFlags('onKilnStopped', {'enabled': False})
        self.server.kiln['analysis'] = False
        dur = self.remote.measure['duration']
        elp = self.remote.measure['elapsed']
        msg = _('Thermal cycle interrupted')
        if dur > 0:
            rem = (dur * 60 - elp) / 60.
            qm.information(self, msg,
                           _('Thermal cycle interrupted.\nThe test will finish in {:.1f} minutes.').format(rem))
        else:
            self.warning(msg,
                         _('Thermal cycle interrupted, but no test termination is set: acquisition  may continue indefinitely. \nManually interrupt or set a maximum test duration.'))

    def new(self):
        self.parent().init_instrument()

    def validate(self):
        """Show a confirmation dialog immediately before starting a new test"""
        # TODO: generalize
        if self.remote['devpath'] in ['horizontal', 'vertical', 'flex']:
            val, st = QtGui.QInputDialog.getDouble(self, _("Confirm initial sample dimension"),
                                                   _("Initial dimension (micron)"),
                                                   self.remote.sample0['initialDimension'])
            if not st:
                return False
            self.remote.sample0['initialDimension'] = val
        return True


class MotionControls(QtGui.QToolBar):

    """Motion toolbar"""
    mute = False
    motor = False
    # cycleNotSaved=False

    def __init__(self, remote, parent=None):
        QtGui.QToolBar.__init__(self, parent)
        self.remote = remote
        self.server = remote.parent()

        if self.server.kiln['motorStatus'] >= 0:
            self.kmotor = widgets.build(
                self.server, self.server.kiln, self.server.kiln.gete('motorStatus'))
            self.kmotor.label_widget.setText('Furnace:')
            self.kmotor.lay.insertWidget(0, self.kmotor.label_widget)
            self.addWidget(self.kmotor)

        paths = {}
        # Collect all focus paths
        for pic, win in self.parent().cameras.itervalues():
            logging.debug('%s', pic)
            logging.debug('%s', pic.remote)
            logging.debug('%s', pic.remote.encoder)
            logging.debug('%s', pic.remote.encoder.focus)

            obj = pic.remote.encoder.focus.role2dev('motor')
            if not obj:
                continue
            paths[obj['fullpath']] = obj
        for obj in paths.itervalues():
            self.add_focus(obj)

    def add_focus(self, obj):
        # 		slider=widgets.MotorSlider(self.server,obj,self.parent())
        slider = widgets.build(self.server, obj, obj.gete('goingTo'))
        slider.lay.insertWidget(0, slider.label_widget)
        slider.label_widget.setText('    Focus:')
        self.addWidget(slider)
