#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
from series import Series
from simann import Annealer, AdaptiveSchedule
from block import Bwarp, Bseries
from plot import WarpPlotter
from match import MatchConf, MatchSeriesConf
import logging
import math
import random
import shutil
import tempfile
from collections import namedtuple
import ConfigParser
import argparse

def _find_executable_noext(leafname):
    """Helper function for find_executable."""
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
    """Look for an executable on the current system path.
    
    For the name "foo.bar", this function will first try to find an
    executable with exactly that name; if this is not found, it will
    look for "foo.bar.exe"; if this is not found either, it will look
    for "foo".
    
    Args:
        leafname: the name of the executable file (extension optional)
    Returns:
        the full path of the executable, or None if it cannot be found
    """
    path = _find_executable_noext(leafname)
    if (path == None):
        path = _find_executable_noext(leafname+".exe")
    if (path == None):
        path = _find_executable_noext(os.path.splitext(leafname)[0])
    return path


ScoterConfigBase = namedtuple("ScoterConfigBase",
    "nblocks, interp_type, interp_npoints, detrend, " + 
    "normalize, max_rate, make_pdf, live_display, precalc, " + 
    "temp_init, temp_final, cooling, max_changes, max_steps, " + 
    "rc_penalty, random_seed, match_nomatch, match_speed_p, " + 
    "match_tie_p, match_target_speed, match_speedchange_p, " + 
    "match_gap_p, match_rates, match_path, " + 
    "target_d18o_file, record_d18o_file, " + 
    "target_rpi_file, record_rpi_file, " + 
    "target_start, target_end, " + 
    "record_start, record_end")

class ScoterConfig(ScoterConfigBase):
    """A configuration for Scoter.
    
    This class encapsulates all the information required for a Scoter
    run.    
    """
    
    def __new__(cls, nblocks = 64,
                  interp_type = "min",
                  interp_npoints = -1, # TODO check this doesn't break anything
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
                  match_rates = "1:4,1:3,1:2,2:3,3:4,1:1,4:3,3:2,2:1,3:1,4:1",
                  match_path = "", # empty string => look for match on current path
                  target_d18o_file = "",
                  record_d18o_file = "",
                  target_rpi_file = "",
                  record_rpi_file = "",
                  target_start = -1,
                  target_end = -1,
                  record_start = -1,
                  record_end = -1,
                  ):
        if interp_npoints == -1: interp_npoints = None
        return super(ScoterConfig, cls).__new__\
            (cls, nblocks, interp_type, interp_npoints, detrend,
             normalize, max_rate, make_pdf, live_display, precalc,
             temp_init, temp_final, cooling, max_changes, max_steps,
             rc_penalty, random_seed, match_nomatch, match_speed_p,
             match_tie_p, match_target_speed, match_speedchange_p,
             match_gap_p, match_rates, match_path,
             target_d18o_file, record_d18o_file,
             target_rpi_file, record_rpi_file,
             target_start, target_end, record_start, record_end)
    
    def write_to_file(self, filename):
        """Write this configuration to a ConfigParser file.
        """
        parser = ConfigParser.RawConfigParser()
        cfgdict = self._asdict()
        for key, value in cfgdict.items():
            parser.set("DEFAULT", key, value)
        with open(filename, "wb") as fh:
            parser.write(fh)
    
    @classmethod
    def read_from_file(cls, filename):
        """Create a new ScoterConfig from a ConfigParser file.
        
        Args:
            filename: full path to ConfigParser file containing a
                Scoter configuration
        
        Returns:
            a ScoterConfig initialized from the supplied file            
        """
        default_config = ScoterConfig()
        default_dict = default_config._asdict()
        cp = ConfigParser.RawConfigParser(default_dict)
        cp.read(filename)
        s = "DEFAULT"
        return ScoterConfig(
            nblocks = cp.getint(s, "nblocks"),
            interp_type = cp.get(s, "interp_type"),
            interp_npoints = cp.getint(s, "interp_npoints"),
            detrend = cp.get(s, "detrend"),
            normalize = cp.getboolean(s, "normalize"),
            max_rate = cp.getint(s, "max_rate"),
            make_pdf = cp.getboolean(s, "make_pdf"),
            live_display = cp.getboolean(s, "live_display"),
            precalc = cp.getboolean(s, "precalc"),
            temp_init = cp.getfloat(s, "temp_init"),
            temp_final = cp.getfloat(s, "temp_final"),
            cooling = cp.getfloat(s, "cooling"),
            max_changes = cp.getint(s, "max_changes"),
            max_steps = cp.getint(s, "max_steps"),
            rc_penalty = cp.getfloat(s, "rc_penalty"),
            random_seed = cp.getint(s, "random_seed"),
            match_nomatch = cp.getfloat(s, "match_nomatch"),
            match_speed_p = cp.getfloat(s, "match_speed_p"),
            match_tie_p = cp.getfloat(s, "match_tie_p"),
            match_target_speed = cp.get(s, "match_target_speed"),
            match_speedchange_p = cp.getfloat(s, "match_speedchange_p"),
            match_gap_p = cp.getfloat(s, "match_gap_p"),
            match_rates = cp.get(s, "match_rates"),
            match_path = cp.get(s, "match_path"),
            target_d18o_file = cp.get("target_d18o_file"),
            record_d18o_file = cp.get("record_d18o_file"),
            target_rpi_file = cp.get("target_rpi_file"),
            record_rpi_file = cp.get("record_rpi_file"),
            target_start = cp.getfloat("target_start"),
            target_end = cp.getfloat("target_end"),
            record_start = cp.getfloat("record_start"),
            record_end = cp.getfloat("record_end")
            )

class Scoter:
    """Scoter correlates geological records with reference curves.
    
    This is the central class of the Scoter package, and provides high-level
    methods to control the correlation process: reading data series,
    preprocessing them, and running the actual correlation. It provides a simple
    API suitable for use from the command line, from the companion GUI ScoterGui,
    or from other Python code importing the scoter module. 
    """
    
    def __init__(self):
        self.parent_dir = os.path.dirname(os.path.realpath(__file__))
        self.default_match_path = find_executable("match")
        self._init_data_structures()
    
    def _rel_path(self, filename):
        """Resolve a filename relative to the parent directory of this script."""
        return os.path.join(self.parent_dir, filename)

    def _init_data_structures(self):
        """Initialize data structures."""
        self.series = [[None, None],[None, None]]
    
    def read_data(self, data_set, record_type, filename):
        """Read a data series.
        
        Read a data series (record or target curve) into Scoter.
        
        Args:
            data_set: 0 for record, 1 for target
            record_type: 0 for d18O, 1 for RPI
            filename: full path to data file
        """
        assert(0 <= data_set <= 1)
        assert(0 <= record_type <= 1)
        self.series[data_set][record_type] = Series.read(filename)
    
    def clear_data(self, data_set, record_type):
        """Clear a data series.
        
        Remove a previously read data series (record or target curve) from Scoter.
        
        Args:
            data_set: 0 for record, 1 for target
            record_type: 0 for d18O, 1 for RPI
        """
        assert(0 <= data_set <= 1)
        assert(0 <= record_type <= 1)
        self.series[data_set][record_type] = None        
    
    def _read_test_data(self):
        self.read_data(0, 0, self._rel_path("data-lr04.txt")) #self._rel_path("data-iso1306.txt"))
        self.read_data(0, 1, self._rel_path("data-piso.txt")) #self._rel_path("data-rpi1306.txt"))
        self.read_data(1, 0, self._rel_path("data-lr04.txt"))
        self.read_data(1, 1, self._rel_path("data-piso.txt"))
        
    def preprocess(self, config):
        """Preprocess data sets in preparation for correlation.
        
        Args:
            config: a ScoterConfig object
        """
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
        if config.interp_type == "min":
            interp_npoints = min(series_npointss)
        elif config.interp_type == "max":
            interp_npoints = min(series_npointss)
        elif config.interp_type == "explicit":
            assert(hasattr(config, "interp_npoints"))
            interp_npoints = config.interp_npoints
        
        record_start = config.record_start if config.record_start > -1 else 0
        target_start = config.target_start if config.target_start > -1 else 0
        
        record_end = min([s.end() for s in series_picked[0]] +
                            ([config.record_end] if config.record_end > -1 else []))
        target_end = min([s.end() for s in series_picked[1]] +
                            ([config.target_end] if config.target_end > -1 else []))
        
        series_truncated = [map(lambda s: s.clip((record_start, record_end)), series_picked[0]),
                            map(lambda s: s.clip((target_start, target_end)), series_picked[1])]
        
        def preproc(series):
            result = series
            if config.detrend == "submean":
                result = result.subtract_mean()
            elif config.detrend == "linear":
                result = result.detrend()
            if interp_npoints != None: result = result.interpolate(interp_npoints)
            if config.normalize: result = result.scale_std_to(1.0)
            return result

        self.series_preprocessed = [map(preproc, series_truncated[0]),
                               map(preproc, series_truncated[1])]

    def correlate_sa(self, known_line, config, callback_obj):
        """Perform a correlation using simulated annealing.
        
        Args:
            known_line: known correlation curve (for display when testing) (optional)
            config: a ScoterConfig object
            callback_obj: callback object to monitor progress (optional)
        """
        #if config.multiscale > -1:
        #    return solve_sa_multiscale(series0, series1, config.nblocks, known_line, config)
        
        random_generator = random.Random(config.random_seed)
        n_record_types = len(self.series_preprocessed[0])
        
        starting_warp = Bwarp(Bseries(self.series_preprocessed[0], config.nblocks),
                              Bseries(self.series_preprocessed[1], config.nblocks),
                              max_rate = config.max_rate,
                              rc_penalty = config.rc_penalty,
                              rnd = random_generator)
        
        starting_warp.max_rate = config.max_rate
        
        # Set up warp plotter if needed
        plotter = None
        if config.live_display:
            plotter = WarpPlotter(config.nblocks, known_line, 100,
                                  pdf_file = 'dsaframes-1.pdf' if config.make_pdf else None)
        
        ltemp_max = math.log(config.temp_init)
        
        def callback(soln_current, soln_new, schedule):
            if callback_obj != None:
                callback_obj.simann_callback_update(soln_current, soln_new,
                                                    (ltemp_max - math.log(schedule.temp)) / ltemp_max * 100)
                return callback_obj.simann_check_abort()
            if plotter != None:
                plotter.replot(soln_current, soln_new, schedule.step)
        
        # Create and run the simulated annealer.

        schedule = AdaptiveSchedule(config.temp_init, config.temp_final,
                                    config.max_changes, config.max_steps, rate = config.cooling)

        finished_ok = True
        if config.precalc:
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
    
    def correlate_match(self, config):
        """Perform a correlation using the external match program.
        
        Args:
            config: a ScoterConfig object
        """
        
        dir_path = tempfile.mkdtemp("", "scoter", None)
        
        match_params = dict(
        nomatch = config.match_nomatch,
        speedpenalty = config.match_speed_p,
        targetspeed = config.match_target_speed,
        speedchange = config.match_speedchange_p,
        tiepenalty = config.match_tie_p,
        gappenalty = config.match_gap_p,
        speeds = config.match_rates
        )

        match_conf =  MatchConf(MatchSeriesConf(self.series_preprocessed[0],
                                                intervals = config.nblocks),
                                MatchSeriesConf(self.series_preprocessed[1],
                                                intervals = config.nblocks),
                            match_params)
        match_path = self.default_match_path if config.match_path == "" else config.match_path
        logging.debug("Match path: %s", match_path)
        match_result = match_conf.run_match(match_path, dir_path, False)
        self.aligned_match = match_result.series1
        shutil.rmtree(dir_path, ignore_errors = True)

def main():
    logging.basicConfig(level=logging.DEBUG)
    parser = argparse.ArgumentParser(description="Correlate geological records.")
    parser.add_argument("configuration", metavar="filename", type=str, nargs=1,
                   help="a Scoter configuration file")
    args = parser.parse_args()
    config = ScoterConfig.read_from_file(args.configuration)
    print config._asdict()
    #config = ScoterConfig()
    #config.write_to_file("testconfig")

logger = logging.getLogger(__name__)
if __name__ == "__main__":
    main()

