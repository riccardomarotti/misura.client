#!/usr/bin/python
# -*- coding: utf-8 -*-
import unittest
from misura.client.procedure import flags as thermal_cycle_flags
from misura.client.procedure import row as thermal_cycle_row

from PyQt4 import QtCore


class FakeIndex():

    def __init__(self, row_index, column_index, is_valid):
        self.row_index = row_index
        self.column_index = column_index
        self.is_valid = is_valid

    def row(self):
        return self.row_index

    def column(self):
        return self.column_index

    def isValid(self):
        return self.is_valid


class FakeTermalCurveModel():

    def __init__(self, dat, row_modes=['any mode', 'another mode']):
        self.fake_dat = dat
        self.fake_row_modes = row_modes

    @property
    def dat(self):
        return self.fake_dat

    @property
    def row_modes(self):
        return self.fake_row_modes

    def mode_of_column(self, column):
        return 'any mode'


class TestTermalCycleFlags(unittest.TestCase):

    def test_should_not_be_editable_when_item_is_not_valid(self):
        not_valid_index = FakeIndex(None, None, False)

        not_editable = QtCore.Qt.ItemFlags(QtCore.Qt.ItemIsEnabled)
        self.assertEqual(
            not_editable, thermal_cycle_flags.execute(None, not_valid_index))

    def test_should_not_be_editable_when_you_are_in_the_temp_column_and_time_is_negative(self):
        row_index = 0
        column_index = 12386
        valid_index = FakeIndex(row_index, column_index, True)
        dat = [[-1]]

        not_editable = QtCore.Qt.ItemFlags(QtCore.Qt.ItemIsEnabled)
        self.assertEqual(not_editable, thermal_cycle_flags.execute(
            FakeTermalCurveModel(dat), valid_index))

    def test_should_not_be_editable_when_you_are_in_the_first_row_and_column_different_from_time(self):
        row_index = 0
        column_index = thermal_cycle_row.colTIME
        valid_index = FakeIndex(row_index, column_index, True)
        dat = [[123, 1]]

        not_editable = QtCore.Qt.ItemFlags(QtCore.Qt.ItemIsEnabled)
        self.assertEqual(not_editable, thermal_cycle_flags.execute(
            FakeTermalCurveModel(dat), valid_index))

    def test_temperature_should_not_be_editable_when_rate_is_zero(self):
        row_index = 1
        column_index = thermal_cycle_row.colTEMP
        valid_index = FakeIndex(row_index, column_index, True)
        dat = [[], [123, 321, 0, 132]]

        not_editable = QtCore.Qt.ItemFlags(QtCore.Qt.ItemIsEnabled)
        self.assertEqual(not_editable, thermal_cycle_flags.execute(
            FakeTermalCurveModel(dat), valid_index))

    def test_temperature_should_be_editable_when_rate_is_zero_for_first_row(self):
        row_index = 0
        column_index = thermal_cycle_row.colTEMP
        valid_index = FakeIndex(row_index, column_index, True)
        dat = [[123, 321, 0, 132]]

        editable = QtCore.Qt.ItemFlags(
            QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEditable | QtCore.Qt.ItemIsEnabled)
        self.assertEqual(editable, thermal_cycle_flags.execute(
            FakeTermalCurveModel(dat), valid_index))

    def test_nothing_should_be_editalble_when_offline(self):
        row_index = 0
        column_index = thermal_cycle_row.colTEMP
        valid_index = FakeIndex(row_index, column_index, True)
        dat = [[123, 321, 0, 132]]

        not_editable = QtCore.Qt.ItemFlags(QtCore.Qt.ItemIsEnabled)
        is_live = False

        self.assertEqual(not_editable, thermal_cycle_flags.execute(
            FakeTermalCurveModel(dat, ['any mode']), valid_index, is_live=is_live))

    def test_rate_is_not_editable_when_not_int_rate_mode(self):
        row_index = 1
        column_index = thermal_cycle_row.colRATE
        valid_index = FakeIndex(row_index, column_index, True)
        dat = [[], [123, 321, 80, 132]]
        modes = ['any mode', 'points']

        not_editable = QtCore.Qt.ItemFlags(QtCore.Qt.ItemIsEnabled)

        self.assertEqual(not_editable, thermal_cycle_flags.execute(FakeTermalCurveModel(dat, modes), valid_index))

    def test_temperature_is_always_editable(self):
        row_index = 1
        column_index = thermal_cycle_row.colTEMP
        valid_index = FakeIndex(row_index, column_index, True)
        dat = [[], [123, 321, 80, 132]]
        modes = ['any mode', 'any mode']

        editable = QtCore.Qt.ItemFlags(
            QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEditable | QtCore.Qt.ItemIsEnabled)

        self.assertEqual(editable, thermal_cycle_flags.execute(FakeTermalCurveModel(dat, modes), valid_index))



if __name__ == "__main__":
    unittest.main(verbosity=2)
