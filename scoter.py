#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os.path
from series import Series

class Scoter:
    
    def __init__(self):
        self.parent_dir = os.path.dirname(os.path.realpath(__file__))
        self._init_data_structures()
        self.read_test_data()
    
    def rel_path(self, filename):
        return os.path.join(self.parent_dir, filename)

    def _init_data_structures(self):
        self.series = [[None, None],[None, None]]
    
    def read_data(self, series, subseries, filename):
        assert(0 <= series <= 1)
        assert(0 <= subseries <= 1)
        self.series[series][subseries] = Series.read(filename)
    
    def read_test_data(self):
        leafname = "1306 isotopes.txt"
        self.read_data(0, 0, self.rel_path(leafname))

    def correlate(self, method):
        pass
    