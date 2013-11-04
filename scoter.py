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
        self.read_data(0, 0, self.rel_path("data-lr04.txt")) #self.rel_path("data-iso1306.txt"))
        self.read_data(0, 1, self.rel_path("data-piso.txt")) #self.rel_path("data-rpi1306.txt"))
        self.read_data(1, 0, self.rel_path("data-lr04.txt"))
        self.read_data(1, 1, self.rel_path("data-piso.txt"))

    def solve_sa(self, known_line, args):
    
        #if args.multiscale > -1:
        #    return solve_sa_multiscale(series0, series1, nblocks, known_line, args)
    
        nblocks = args.nblocks
        
        # make sure we actually have enough data to work with
        
        assert((self.series[0][0] != None and self.series[1][0] != None) or
               (self.series[0][1] != None and self.series[1][1] != None))
        
        # Each series is a tuple of parallel records of different parameters

        series_picked = [[], []]
        for record_type in (0,1):
            # Do we have this record type in both our data-sets?
            if self.series[0][record_type] != None and self.series[1][record_type] != None:
                # If so, interpolate and store for matching
                series_picked[0].append(self.series[0][record_type])
                series_picked[1].append(self.series[1][record_type])

        # series_picked will now be something like
        # [[record_d18O, record_RPI] , [target_d18O, target_RPI]]
        # or for a non-tandem match something like
        # [[record_d18O] , [target_d18O]]

        series_picked_flat = series_picked[0] + series_picked[1]
        series_npointss = [s.npoints() for s in series_picked_flat]
        interp_npoints = None
        if args.interp_type == "min":
            interp_npoints = min(series_npointss)
        elif args.interp_type == "max":
            interp_npoints = min(series_npointss)
        elif args.interp_type == "explicit":
            assert(hasattr(args, "interp_npoints"))
            interp_npoints = args.interp_npoints
        
        print "interpolating to", interp_npoints
        
        def interpolate(series):
            if interp_npoints == None:
                return series
            else:
                return series.interpolate(interp_npoints)
        
        series_interp = [map(interpolate, series_picked[0]),
                         map(interpolate, series_picked[1])]
        
        starting_warp = Bwarp(Bseries(series_interp[0], nblocks),
                              Bseries(series_interp[1], nblocks),
                              rc_penalty = 2.5)
            
        starting_warp.max_rate = args.max_rate
        
        # Set up warp plotter if needed
        plotter = None
        if args.live_display:
            plotter = WarpPlotter(nblocks, known_line, 100,
                                  pdf_file = 'dsaframes-1.pdf' if args.make_pdf else None)
        
        # Create and run the simulated annealer.
        # Parameters for artificial test:
        schedule = AdaptiveSchedule(1.0e3, 1, 5, 200, rate = 0.99)
        # # Parameters for 1306
        # schedule = AdaptiveSchedule(1.0e5, 1.0e-0, 50, 500, rate = 0.99)
        if args.precalc:
            bwarp_annealed = starting_warp
        else:
            annealer = Annealer(starting_warp)
            annealer.run(schedule, logging = False, restarts = 0,
                    callback = plotter.replot if plotter else None)
            annealer.output_scores('/home/pont/scores.txt')
            bwarp_annealed = annealer.soln_best
        
        # Apply the annealed antiwarp to the warped data
        if plotter: plotter.finish()
        bwarp_annealed.name = 'Sim. Ann.'
        bwarp_annealed.printself()
        dewarped = bwarp_annealed.apply(1)
    
        self.dewarped = dewarped
        self.bwarp_annealed = bwarp_annealed

    def correlate(self, method):
        args = None
        warp_line = None
        self.solve_sa(warp_line, args)
        