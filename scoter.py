#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
from series import Series
from simann import Annealer, AdaptiveSchedule
from block import Bwarp, Bseries
from plot import WarpPlotter
from match import MatchConf, MatchSeriesConf
import math
import random
import shutil
import tempfile
from collections import namedtuple

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

arg_names = \
    "nblocks, interp_type, interp_npoints, detrend, "+\
    "normalize, max_rate, make_pdf, live_display, precalc, "+\
    "temp_init, temp_final, cooling, max_changes, max_steps, "+\
    "rc_penalty, random_seed, match_nomatch, match_speed_p, "+\
    "match_tie_p, match_target_speed, match_speedchange_p, "+\
    "match_gap_p, match_rates"

ScoterConfigBase = namedtuple("ScoterConfigBase", arg_names)

class ScoterConfig(ScoterConfigBase):
    
    def __new__(cls, nblocks = 64,
                  interp_type = "min",
                  interp_npoints = None,
                  detrend = "linear",
                  normalize = True,
                  max_rate = 4,
                  make_pdf = False,
                  live_display = False,
                  precalc = False,
                  temp_init = 1.0e3,
                  temp_final = 1.0,
                  cooling = 0.95,
                  max_changes = 5,
                  max_steps = 200,
                  rc_penalty = 0.,
                  random_seed = 42,
                  match_nomatch = 1e12,
                  match_speed_p = 0.0,
                  match_tie_p = 100,
                  match_target_speed = "1:1",
                  match_speedchange_p = 1.0,
                  match_gap_p = 1,
                  match_rates = "1:4,1:3,1:2,2:3,3:4,1:1,4:3,3:2,2:1,3:1,4:1"
                ):
        if interp_npoints == -1: interp_npoints = None
        return super(ScoterConfig, cls).__new__\
            (cls, nblocks, interp_type, interp_npoints, detrend,
             normalize, max_rate, make_pdf, live_display, precalc,
             temp_init, temp_final, cooling, max_changes, max_steps,
             rc_penalty, random_seed, match_nomatch, match_speed_p,
             match_tie_p, match_target_speed, match_speedchange_p,
             match_gap_p, match_rates)

class Scoter:
    
    def __init__(self):
        self.parent_dir = os.path.dirname(os.path.realpath(__file__))
        self.match_path = find_executable("match")
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
        
    def preprocess(self, args):
        
        # make sure we actually have enough data to work with
        
        assert((self.series[0][0] != None and self.series[1][0] != None) or
               (self.series[0][1] != None and self.series[1][1] != None))
        
        # Each series is a tuple of parallel records of different parameters

        series_picked = [[], []]
        for record_type in (0, 1):
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
        
        bottom_record = min([s.end() for s in series_picked[0]])
        bottom_target = min([s.end() for s in series_picked[1]])
        
        series_truncated = [map(lambda s: s.truncate(bottom_record), series_picked[0]),
                            map(lambda s: s.truncate(bottom_target), series_picked[1])]
        
        def preproc(series):
            result = series
            if args.detrend == "submean":
                result = result.subtract_mean()
            elif args.detrend == "linear":
                result = result.detrend()
            if interp_npoints != None: result = result.interpolate(interp_npoints)
            if args.normalize: result = result.scale_std_to(1.0)
            return result

        self.series_preprocessed = [map(preproc, series_truncated[0]),
                               map(preproc, series_truncated[1])]

    def correlate_sa(self, known_line, args, callback_obj):
        #if args.multiscale > -1:
        #    return solve_sa_multiscale(series0, series1, args.nblocks, known_line, args)
        
        random_generator = random.Random(args.random_seed)
        n_record_types = len(self.series_preprocessed[0])
        
        starting_warp = Bwarp(Bseries(self.series_preprocessed[0], args.nblocks),
                              Bseries(self.series_preprocessed[1], args.nblocks),
                              max_rate = args.max_rate,
                              rc_penalty = args.rc_penalty,
                              rnd = random_generator)
        
        starting_warp.max_rate = args.max_rate
        
        # Set up warp plotter if needed
        plotter = None
        if args.live_display:
            plotter = WarpPlotter(args.nblocks, known_line, 100,
                                  pdf_file = 'dsaframes-1.pdf' if args.make_pdf else None)
        
        ltemp_max = math.log(args.temp_init)
        
        def callback(soln_current, soln_new, schedule):
            if callback_obj != None:
                callback_obj.simann_callback_update(soln_current, soln_new,
                                                    (ltemp_max - math.log(schedule.temp)) / ltemp_max * 100)
                return callback_obj.simann_check_abort()
            if plotter != None:
                plotter.replot(soln_current, soln_new, schedule.step)
        
        # Create and run the simulated annealer.

        schedule = AdaptiveSchedule(args.temp_init, args.temp_final,
                                    args.max_changes, args.max_steps, rate = args.cooling)

        finished_ok = True
        if args.precalc:
            bwarp_annealed = starting_warp
        else:
            annealer = Annealer(starting_warp, random_generator)
            finished_ok = annealer.run(schedule, logging = False, restarts = 0,
                    callback = callback)
            if not finished_ok:
                callback_obj.simann_callback_finished("aborted")
                return "aborted"
            bwarp_annealed = annealer.soln_best
        
        # Apply the annealed antiwarp to the warped data
        if plotter: plotter.finish()
        bwarp_annealed.name = 'Sim. Ann.'
        bwarp_annealed.printself()
        self.aligned_sa = []
        self.aligned_sa.append(bwarp_annealed.apply(1, 0))
        if (n_record_types == 2):
            self.aligned_sa.append(bwarp_annealed.apply(1, 1))
    
        self.warp_sa = bwarp_annealed
        callback_obj.simann_callback_finished("completed")
        return "completed"
    
    def correlate_match(self, args):
        
        dir_path = tempfile.mkdtemp("", "scoter", None)
        
        match_params = dict(
        nomatch = args.match_nomatch,
        speedpenalty = args.match_speed_p,
        targetspeed = args.match_target_speed,
        speedchange = args.match_speedchange_p,
        tiepenalty = args.match_tie_p,
        gappenalty = args.match_gap_p,
        speeds = args.match_rates
        )
        # NB 1:1 temporarily removed for testing purposes

        match_conf =  MatchConf(MatchSeriesConf(self.series_preprocessed[0], intervals = args.nblocks),
                            MatchSeriesConf(self.series_preprocessed[1], intervals = args.nblocks),
                            match_params)

        match_result = match_conf.run_match("/usr/local/bin/match", dir_path, False)
        
        self.aligned_match = match_result.series1
        
        shutil.rmtree(dir_path, ignore_errors = True)















