#!/usr/bin/python
# -*- coding: utf-8 -*-
"""misura Configuration Manager"""
import os
from misura.canon.logger import get_module_logging
logging = get_module_logging(__name__)
import sqlite3
import re
from traceback import format_exc, print_exc

from PyQt4 import QtCore

from misura.canon import option
from misura.canon import csutil
from misura.canon.option import ao
from misura.canon.indexer import Indexer
from misura.canon.plugin import clientconf_update_functions
import units

import parameters as params
from . import _
from copy import deepcopy

default_misuradb_path = os.path.expanduser("~/MisuraData/misuradb")

default_desc = {}

ao(default_desc, 'lang', **{'name': "Client Language",
                            'current': 'sys',
                            'type': 'Chooser',
                            'options': ['sys', 'en', 'it', 'fr', 'es', 'ru']
                            })
ao(default_desc, 'refresh', **{'name': 'Remote Server Refresh Rate (ms)',
                               'current': 2000, 'max': 20000,   'min': 100, 'type': 'Integer'})

ao(default_desc, 'database', **
   {'name': 'Default Database', 'current': default_misuradb_path, 'type': 'FilePath'})
ao(default_desc, 'hserver', **
   {'name': 'Recent Servers', 'current': 5, 'max': 20, 'min': 0, 'type': 'Integer'})
ao(default_desc, 'saveLogin', **
   {'name': 'Save User/Password by Default', 'current': True, 'type': 'Boolean'})
ao(default_desc, 'autoConnect', **
   {'name': 'Auto-connect to last server used',
    'current': True, 'type': 'Boolean'})

ao(default_desc, 'authLevel', 'Chooser', 2, 'Authorization level when opening test files', 
   values=range(6), options=['guest', 'basic', 'user', 'tech', 'maint', 'admin'])

ao(default_desc, 'hdatabase', **
   {'name': 'Recent Database Files', 'current': 10, 'max': 100, 'min': 1, 'type': 'Integer'})
ao(default_desc, 'hfile', **{'name': 'Recent Test Files',
                             'current': 15, 'max': 100, 'min': 1, 'type': 'Integer'})
ao(default_desc, 'hm3database', **
   {'name': 'Recent Misura3 Databases', 'current': 10, 'max': 100, 'min': 1, 'type': 'Integer'})

ao(default_desc, 'logdir', **{'name': 'Log files directory',
                              'current': os.path.expanduser("~/MisuraData/log"),
                              'type': 'FilePath'})
ao(default_desc, 'loglevel', **{'name': 'Logging Level', 'current': 30,
                                'max': 50, 'min': -1, 'step': 10, 'type': 'Integer', 'parent': 'logdir'})
ao(default_desc, 'lognotify', **{'name': 'Popup notification level', 'current': 40,
                                'max': 50, 'min': -1, 'step': 10, 'type': 'Integer', 'parent': 'logdir'})
ao(default_desc, 'logsize', **{'name': 'Size of each log file', 'current':
                               2048, 'min': 0, 'unit': 'kilobyte', 'type': 'Integer', 'parent': 'logdir'})
ao(default_desc, 'lognumber', **{'name': 'Max number of logfiles to be kept',
                                 'current': 50, 'min': 0, 'type': 'Integer', 'parent': 'logdir'})

ao(default_desc, 'templates', **{'name': 'Templates directory',
                              'current': os.path.expanduser("~/MisuraData/templates"),
                              'type': 'FilePath'})


u = [[k, v] for k, v in units.user_defaults.iteritems()]
ao(default_desc, 'units', 'Table', [
   [('Dimension', 'String'), ('Unit', 'String')]] + u, 'Measurement units')

ao(default_desc, 'rule', 'Section', 'Dataset Rules', 'Dataset Rules')

rule_exc = r'''^(/summary/)?beholder/
^(/summary/)?hydra/
/analyzer/
/autoroi/
/iA$
/iB$
/iC$
/iD$'''
ao(default_desc, 'rule_exc', 'TextArea', rule_exc, 'Ignore datasets')

rule_inc = ''
ao(default_desc, 'rule_inc', 'TextArea', rule_inc, 'Force inclusion')

rule_load = r'''hsm/sample\d/h$
hsm/sample\d/Vol$
/sample\d/d$
.*/T$
^(/summary/)?kiln/S$
^(/summary/)?kiln/P$'''
ao(default_desc, 'rule_load', 'TextArea', rule_load, 'Force loading')

rule_unit = [
    [('Rule', 'String'), ('Unit', 'String')],
    [r'/hsm/sample\d/h$', 'percent'],
    [r'/hsm/sample\d/Vol$', 'percent'],
    [r'/vertical/sample\d/d$', 'percent'],
    [r'/horizontal/sample\d/d$', 'percent']
]
ao(default_desc, 'rule_unit', 'Table', rule_unit, 'Dataset units')

rule_plot = r'''hsm/sample\d/Vol$
/sample\d/d$
^(/summary/)?kiln/T$'''
ao(default_desc, 'rule_plot', 'TextArea', rule_plot, 'Auto Plot')

rule_style = [[('Rule', 'String'), ('Range', 'String'), ('Scale', 'Float'),
               ('Color', 'String'), ('Line', 'String'), ('Marker', 'String')],
              ['/kiln/T$', '', 1, 'red', '', '']
              ]
ao(default_desc, 'rule_style', 'Table', rule_style, 'Formatting')


ao(default_desc, 'm3', 'Section', 'Data import', 'Data import')
ao(default_desc, 'm3_enable', 'Boolean', True, 'Enable Misura 3 database interface')
ao(default_desc, 'm3_plugins', 'TextArea', '', 'Import plugins by name')


ao(default_desc, 'recent_server', 'Table', attr=['Hidden'], current=[[('Address', 'String'),('User', 'String'), ('Password','String'), ('MAC', 'String'),('Serial', 'String'), ('Name', 'String')], ])
ao(default_desc, 'recent_database', 'Table', attr=['Hidden'], current=[[('Path', 'String'),('Name','String')], ])
ao(default_desc, 'recent_file', 'Table', attr=['Hidden'], current=[[('Path', 'String'),('Name','String')], ])
ao(default_desc, 'recent_m3database', 'Table', attr=['Hidden'], current=[[('Path', 'String'),('Name','String')], ])


recent_tables = 'server,database,file,m3database'.split(',')


def tabname(name):
    if name in recent_tables:
        return 'recent_' + name
    return name


class RulesTable(object):

    """Helper object for matching a string in a list of rules."""

    def __init__(self, tab=[]):
        self.set_table(tab)

    def set_table(self, tab):
        self.rules = []
        self.rows = []
        self.tab = tab
        for row in tab:
            if len(row) <= 1:
                logging.debug('skipping malformed rule', row)
                logging.debug('skipping malformed rule', row)
            if isinstance(row[0], tuple):
                # Skip header row
                continue
            r = row[0]
            if len(r) == 0:
                logging.debug('skipping empty rule', row)
                continue
            r = re.compile(r.replace('\n', '|'))
            self.rules.append(r)
            self.rows.append(row[1:])

    def __call__(self, s, latest=False):
        """Return the row corresponding to the first rule matching the string `s`"""
        f = False
        for i, r in enumerate(self.rules):
            if r is False:
                continue
            if r.search(s):
                f = self.rows[i]
                if not latest:
                    return f
        # No match found
        return f


class ConfDb(option.ConfigurationProxy, QtCore.QObject):
    _Method__name = 'CONF'
    conn = False
    path = ''
    index = False

    def __init__(self, path=False):
        QtCore.QObject.__init__(self)
        option.ConfigurationProxy.__init__(self)
        self.store = option.SqlStore()
        if not path:
            return None
        # Load/create
        self.known_uids = {}
        self.default_desc = deepcopy(default_desc)
        self.load(path)

    _rule_style = RulesTable()

    @property
    def rule_style(self):
        """A RulesTable for styles"""
        if not self._rule_style:
            self._rule_style = RulesTable(self['rule_style'])
        return self._rule_style

    _rule_dataset = RulesTable()

    @property
    def rule_dataset(self):
        """A special RulesTable collecting dataset loading behaviors."""
        if not self._rule_dataset:
            tab = [[('header placeholder'), ('retn')],
                   [self['rule_exc'], 1],  # exclude
                   [self['rule_inc'], 2],  # create
                   [self['rule_load'], 3],  # load
                   [self['rule_plot'], 4],  # plot
                   ]
            self._rule_dataset = RulesTable(tab)
        return self._rule_dataset

    _rule_unit = RulesTable()

    @property
    def rule_unit(self):
        if not self._rule_unit:
            self._rule_unit = RulesTable(self['rule_unit'])
        return self._rule_unit

    def reset_rules(self):
        self._rule_style = False
        self._rule_dataset = False
        self._rule_unit = False

    def load_configuration(self, cursor):
        # Configuration table
        conf_table_exists = cursor.execute(
            "select 1 from sqlite_master where type='table' and name='conf'").fetchone()
        loaded = False
        if conf_table_exists:
            try:
                stored_desc = self.store.read_table(cursor, 'conf')
                desc = default_desc.copy()
                desc.update(stored_desc)
                self.desc = desc
                logging.debug('Loaded configuration', self.desc)
                loaded=True
            except:
                logging.error(format_exc())
        if not loaded:
            logging.debug('Recreating client configuration')
            for key, val in default_desc.iteritems():
                self.store.desc[key] = option.Option(**val)
            self.desc = self.store.desc
            self.store.write_table(cursor, "conf")
        # Apply authorization level
        option.ConfigurationProxy._readLevel = self['authLevel']
        option.ConfigurationProxy._writeLevel = self['authLevel']
            
    def migrate_desc(self):
        """Migrate saved newdesc to current hard-coded configuration structure default_desc"""
        desc_ret = {}
        for key, val in self.desc.iteritems():
            if self.default_desc.has_key(key):
                saved_opt = option.Option(**val)
                coded_opt = option.Option(**self.default_desc[key])
                saved_opt.migrate_from(coded_opt)
                desc_ret[key] = saved_opt
        self.desc = desc_ret 
        
    def add_option(self, *a, **k):
        """When a new option is defined, add also to default_desc definition"""
        out = option.ConfigurationProxy.add_option(self, *a, **k)
        self.default_desc[out['handle']] = out.entry
        return out
            
    def load(self, path=False):
        """Load an existent client configuration database, or create a new one."""
        logging.debug('LOAD', path)
        self.index = False
        self.close()
        if path:
            self.path = path
            csutil.ensure_directory_existence(path)
        self.conn = sqlite3.connect(
            self.path, detect_types=sqlite3.PARSE_DECLTYPES)
        self.conn.text_factory = unicode
        cursor = self.conn.cursor()
        
        self.load_configuration(cursor)
        cursor.close()
        
        self.conn.commit()
        
        # Forget recent tables defined with old headers
        for tname in recent_tables:
            tname = 'recent_'+tname
            if self[tname][0]!=default_desc[tname]['current'][0]:
                self[tname] = default_desc[tname]['current']
        
        self.emit(QtCore.SIGNAL('load()'))
        
        for key in ['logdir', 'templates']:
            if not os.path.exists(self[key]):
                logging.debug('Creating configured directory', key, self[key])
                try:
                    os.makedirs(self[key])
                except:
                    logging.error(format_exc())
        
        
        self.reset_rules()
        self.create_index()



    def create_index(self):
        self.index = False
        path = self['database']
        if path.strip() == '':
            path = default_misuradb_path
            self['database'] = path
            self.save()

        if path and os.path.exists(path):
            logging.debug('Creating indexer at', path)
            self.index = Indexer(path)
            return True
        else:
            logging.debug('Default database not found:', path)
            return False

    def clean_rules(self):
        for rule in ['rule_load', 'rule_exc', 'rule_inc']:
            self[rule] = self[rule].strip()

    def save(self, path=False):
        """Save to an existent client configuration database."""
        logging.debug('SAVING')
        cursor = self.conn.cursor()
        self.clean_rules()
        self.store.write_table(cursor, 'conf', desc=self.desc)
        cursor.close()
        self.conn.commit()
        self.reset_rules()
        self.create_index()

    def mem(self, name, *arg):
        """Memoize a recent datum"""
        logging.debug("mem ", name, arg)
        tname = tabname(name)
        tab = self[tname]
        # Avoid saving duplicate values
        arg = list(unicode(a) for a in arg)
        # Adjust headers
        if len(arg)<len(tab[0]):
            arg += [''] * (len(tab[0])-len(arg))
        # Update order
        if arg in tab:
            tab.remove(arg)
        tab.append(arg)
        
        lim = self.desc['h' + name]['current']
        if len(tab)-1 > lim:
            tab.pop(1) # preserve header
        setattr(self, tname, tab)
        self.emit(QtCore.SIGNAL('mem()'))
        self.save()
        return True

    def rem(self, name, key):
        """Forget a recent datum"""
        key = str(key)
        tname = tabname(name)
        tab = self[tname]
        # Keys list
        v = [r[0] for r in tab[1:]]
        if key not in v:
            return False
        i = v.index(key)
        tab.pop(i+1) # preserve the header
        self[tname] = tab
        self.emit(QtCore.SIGNAL('rem()'))
        self.save()
        return True

    def close(self):
        if self.conn:
            self.conn.close()

    def mem_file(self, path, name=''):
        self.mem('file', path, name)

    def rem_file(self, path):
        self.rem('file', path)

    def mem_database(self, path, name=''):
        self.mem('database', path, name)

    def rem_database(self, path):
        self.rem('database', path)

    def mem_m3database(self, path, name=''):
        self.mem('m3database', path, name)

    def rem_m3database(self, path):
        self.rem('m3database', path)

    def found_server(self, addr):
        addr = str(addr)
        v = [r[0] for r in self['recent_server'][1:]]
        # Check if the found server was already saved with its own user and
        # password
        print 'found_server', addr, r
        if addr in v:
            return False
        # Otherwise, save it with empty user and password
        self.mem('server', addr, '', '')
        return True

    def logout(self, addr):
        addr = str(addr)
        v = [r[0] for r in self['recent_server'][1:]]
        if addr not in v:
            return False
        # Change order so that it becomes the most recent
        i = v.index(addr)
        entry = self['recent_server'][i+1]
        # TODO: this looses password!!!
        self.rem('server', addr)
        self.mem('server', *entry)
        return True

    # TODO: accettare serial e name e altro...
    def mem_server(self, addr, user='', password='', mac='', name='', save=True):
        # Remove entries with empty user/password
        addr, user, password, mac, name = str(addr), str(user), str(password), str(mac), str(name)
        if not save:
            user = ''
            password = ''
        logging.debug('mem_server', addr, user, password, mac, name)
        return self.mem('server', addr, user, password, mac, name)

    def rem_server(self, addr):
        self.rem('server', addr)

    def get_from_key(self, table_name, key):
        """Returns username and passwords used to login"""
        for entry in self[table_name][1:]:
            if entry[0] == key:
                return entry
        return ['']*len(self[table_name][0])

    def resolve_uid(self, uid):
        """Search file path corresponding to uid across default database and recent databases"""
        if not uid:
            logging.debug('no uid')
            return False
        known = self.known_uids.get(uid, False)
        if known:
            logging.debug( 'UID was known %s',known)
            return known, False
        else:
            logging.debug('Uid not previously known %s',uid)
        if self.index:
            dbPath = self.index.dbPath
            file_path = self.index.searchUID(uid)
            if file_path:
                logging.debug('uid found in default db', uid, file_path)
                return file_path, dbPath
        else:
            dbPath = False
        file_path = False
        recent = self['recent_database'][1:]
        # Add also implicit m3 databases
        if self['m3_enable']:
            for r in self['recent_m3database'][1:]:
                path = r[0]
                path = os.path.dirname(path)
                path = os.path.join(path, 'm4', 'database.sqlite')
                if not os.path.exists(path):
                    continue
                recent.append((path, 0))
        # Scan all recent db
        for path in recent:
            path = path[0]
            if path == dbPath:
                continue
            if not os.path.exists(path):
                logging.debug('Skip db:', path)
                continue
            try:
                db = Indexer(path)
            except:
                logging.info('Db open error: \n',format_exc())
                continue
            file_path = db.searchUID(uid)
            if file_path:
                dbPath = path
                break
            logging.debug('UID not found:', uid, path)
        if not file_path:
            return False
        self.known_uids[self.uid] = file_path
        return file_path, dbPath

    def last_directory(self, category):
        """Return most recently used directory for files in `category`"""
        tab = self['recent_' + category][1:]
        logging.debug('new: tab', category, tab)
        d = ''
        if len(tab) > 0:
            print tab
            d = os.path.dirname(tab[-1][0])
        return d

import importlib
def activate_plugins(confdb):
    plugins = confdb['m3_plugins'].splitlines()
    for plug in plugins:
        plug = plug.replace('\n','')
        print 'Plugging: ', plug
        try:
            importlib.import_module(plug)
        except:
            print_exc()
    # Add client configurations defined in 3rd parties
    print 'updating clientconf', clientconf_update_functions
    for update_func in clientconf_update_functions:
        update_func(confdb)
    confdb.migrate_desc()

settings = QtCore.QSettings(
    QtCore.QSettings.NativeFormat, QtCore.QSettings.UserScope, 'Expert System Solutions', 'Misura 4')
# Set the configuration db
cf = str(settings.value('/Configuration'))
if cf == '' or not os.path.exists(cf):
    confdb = ConfDb(params.pathConf)
elif os.path.exists(cf):
    params.set_pathConf(cf)
    confdb = ConfDb(path=cf)
settings.setValue('/Configuration', confdb.path)
#activate_plugins(confdb)
