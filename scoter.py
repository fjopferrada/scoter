#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
from series import Series
from simann import Annealer, AdaptiveSchedule
from block import Bwarp, Bseries
from plot import WarpPlotter

def _find_executable_noext(leafname):
    def is_exe(supplied_path):
        return os.path.isfile(supplied_path) and os.access(supplied_path, os.X_OK)

    supplied_path = os.path.split(leafname)[0]
    if supplied_path:
        if is_exe(leafname):
            return leafname
    else:
        for path in os.environ["PATH"].split(os.pathsep):
            path = path.strip('"')
            exe_file = os.path.join(path, leafname)
            if is_exe(exe_file):
                return exe_file

    return None

def find_executable(leafname):
    path = _find_executable_noext(leafname)
    if (path == None):
        path = _find_executable_noext(leafname+".exe")
    if (path == None):
        path = _find_executable_noext(os.path.splitext(leafname)[0])
    return path

class Scoter:
    
    def __init__(self):
        self.parent_dir = os.path.dirname(os.path.realpath(__file__))
        self.match_path = find_executable("match")
        self_nblocks = 64
        self._init_data_structures()
    
    def rel_path(self, filename):
        return os.path.join(self.parent_dir, filename)

    def _init_data_structures(self):
        self.series = [[None, None],[None, None]]
    
    def read_data(self, data_set, record_type, filename):
        assert(0 <= data_set <= 1)
        assert(0 <= record_type <= 1)
        self.series[data_set][record_type] = Series.read(filename)
    
    def clear_data(self, data_set, record_type):
        assert(0 <= data_set <= 1)
        assert(0 <= record_type <= 1)
        self.series[data_set][record_type] = None        
    
    def read_test_data(self):
        leafname = "1306 isotopes.txt"
        self.read_data(0, 0, self.rel_path(leafname))

    def solve_sa(self, known_line, args):
    
        #if args.multiscale > -1:
        #    return solve_sa_multiscale(series0, series1, nblocks, known_line, args)
    
        series0 = self.series[0]
        series1 = self.series[1]
        nblocks = self.nblocks
    
        starting_warp = Bwarp(Bseries(series0, nblocks),
                              Bseries(series1, nblocks),
                              rc_penalty = 2.5)
            
        starting_warp.max_rate = args.max_rate
        
        # Set up warp plotter if needed
        plotter = None
        if args.live_display:
            plotter = WarpPlotter(nblocks, known_line, 100,
                                  pdf_file = 'dsaframes-1.pdf' if args.make_pdf else None)
        
        # Create and run the simulated annealer.
        # Parameters for artificial test:
        schedule = AdaptiveSchedule(1.0e4, 200, 50, 500, rate = 0.93)
        # # Parameters for 1306
        # schedule = AdaptiveSchedule(1.0e5, 1.0e-0, 50, 500, rate = 0.99)
        if args.precalc:
            bw_ann = starting_warp
        else:
            annealer = Annealer(starting_warp)
            annealer.run(schedule, logging = False, restarts = 0,
                    callback = plotter.replot if plotter else None)
            annealer.output_scores('/home/pont/scores.txt')
            bw_ann = annealer.soln_best
        
        # Apply the annealed antiwarp to the warped data
        if plotter: plotter.finish()
        bw_ann.name = 'Sim. Ann.'
        bw_ann.printself()
        dewarped = bw_ann.apply(1)
        
        with open('/home/pont/cache.txt', 'w') as fh:
            bw_ann.comp.dump(fh)
    
        return dewarped, bw_ann, starting_warp.comp

    def correlate(self, method):
        args = None
        warp_line = None
        dewarped, sa_warp, ccache = \
            self.solve_sa(warp_line, args)
        