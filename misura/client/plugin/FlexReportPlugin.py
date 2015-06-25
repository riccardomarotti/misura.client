#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tools and plugins for Veusz, providing Misura Thermal Analysis functionality"""
from ReportPlugin import ReportPlugin
from utils import OperationWrapper
import veusz.plugins as plugins

class FlexReportPlugin(OperationWrapper,plugins.ToolsPlugin):
	# a tuple of strings building up menu to place plugin on
	menu = ('Misura','Report')
	# unique name for plugin
	name = 'Report'
	# name to appear on status tool bar
	description_short = 'Create Report'
	# text to appear in dialog box
	description_full = 'Create Report on new page'

	def __init__(self, sample = None):
		self.report_plugin = ReportPlugin(self.add_shapes, sample)

	def apply(self, cmd, fields):
		self.report_plugin.apply(cmd, fields, 'report_flex.vsz', 'd')

	@property
	def fields(self):
		return self.report_plugin.fields

	def add_shapes(self, sample, toset, page, dict_toset, smp_path, test, doc):
		pass
		
plugins.toolspluginregistry.append(FlexReportPlugin)
