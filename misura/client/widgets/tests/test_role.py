#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests role selector widget."""
import unittest
from misura.client import widgets
from misura.canon import option
from PyQt4 import QtGui
app=False
print 'Importing',__name__
main=__name__=='__main__'

#TODO: generalize a widget testing  framework

def setUpModule():
	print 'setUpModule',__name__
	global app
	app=QtGui.QApplication([])

def tearDownModule():
	global app
	print 'Quitting app'
	app.quit()
	print 'tearDownModule',__name__
	
	
class Role(unittest.TestCase):
	@classmethod
	def setUpClass(cls):
		cls.root=option.ConfigurationProxy({
										'self':{'role':{'current':['/dev/','default'],'type':'Role'},
												'roleio':{'options':['/dev/','default','value'],'type':'RoleIO'}
												},
										'dev':{'self':{
													'name':{'type':'String'},
													'value':{'attr':['History'],'type':'Integer'},
													'value2':{'current':2,'attr':['History'],'unit':'celsius','type':'Integer'},
													}
											}
										})
		cls.root.validate()
		cls.root.dev.validate()
	
	def test_role(self):
		w=widgets.build(self.root, self.root, self.root.gete('role'))
		self.assertEqual(w.current, ['/dev/', 'default'])
		e=widgets.RoleEditor(w)
		self.assertEqual(e.tree.current_fullpath(), '/dev/')
		self.assertEqual(e.config.itemData(e.config.currentIndex()), 'default')
		self.assertFalse(hasattr(e, 'io'))
		if main and False:
			w.show()
			QtGui.qApp.exec_()
			print 'Selected on exit:', w.current
					
	def test_io(self):
		w=widgets.build(self.root, self.root, self.root.gete('roleio'))
		self.assertEqual(w.prop['options'], ['/dev/', 'default', 'value'])
		e=widgets.RoleEditor(w)
		self.assertEqual(e.tree.current_fullpath(), '/dev/')
		ci=e.config.currentIndex()
		self.assertEqual(e.config.itemData(ci), 'default')
		ei=e.io.currentIndex()
		self.assertEqual(e.io.itemData(ei), 'value')
		e.io.setCurrentIndex(ei-1)
		nval=e.io.itemData(e.io.currentIndex())
		e.apply()
# 		self.assertEqual(w.prop['options'][-1], nval)
		if main:
			w.show()
			QtGui.qApp.exec_()
			print 'Selected on exit:', w.current
		
		
		
if __name__ == "__main__":
	unittest.main(verbosity=2)  
	
	
