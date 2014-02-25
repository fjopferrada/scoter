# -*- coding: utf-8 -*-

import os, subprocess
from series import Series
        
class MatchSeriesConf:
    """Configuration for a series in a run of the match program.
    Note that more than one series may be specified (as a tuple)."""
    def __init__(self, series, intervals = 200, gapfile = None,
                 begin = None, end = None):
        if isinstance(series, Series):
            self.series = (series,)
        else:
            # assume a tuple or other iterable
            self.series = series
        if begin != None: self.begin = begin
        else: self.begin = max([s.positions()[0] for s in self.series])
        if end != None: self.end = end
        else: self.end = min([s.positions()[-1] for s in self.series])
        self.intervals = intervals
        self.gapfile = gapfile

    def writep(self, fh, num, name, value):
        fh.write('%-16s%s\n' % ('%s%d' % (name, num), str(value)))

    def write(self, fh, num):
        self.writep(fh, num, 'series',
                    ' '.join(map(lambda x: x.name, self.series)))
        self.writep(fh, num, 'begin', self.begin)
        self.writep(fh, num, 'end', self.end)
        self.writep(fh, num, 'numintervals', self.intervals)
        if self.gapfile != None:
            self.writep(fh, num, 'gapfile', self.gapfile)
    
class MatchConf:
    """Configuration for a run of the match program."""

    def __init__(self, series1, series2, params = {}, tie_points = None):
        self.params = dict(nomatch = 1e9, speedpenalty = 2,
                           targetspeed = '1:1', speedchange = 10,
                           tiepenalty = 6000, gappenalty = 100,
                           speeds = ('1:3,2:5,1:2,3:5,2:3,3:4,4:5,1:1,' +
                                     '5:4,4:3,3:2,5:3,2:1,5:2,3:1'))
        self.name = 'match'
        self.params.update(params)
        self.series1 = series1
        self.series2 = series2
        self.matchfile = self.name+'.match'
        self.logfile = self.name+'.log'
        self.tiefile = self.name+'.tie'
        self.tie_points = tie_points

    def writep(self, fh, name, value):
        if value != None:
            fh.write('%-16s%s\n' % (name, str(value)))

    def write_to(self, fh):
        self.series1.write(fh, 1)
        self.series2.write(fh, 2)
        for key, value in self.params.iteritems():
            self.writep(fh, key, value)
        self.writep(fh, 'matchfile', self.matchfile)
        self.writep(fh, 'logfile', self.logfile)
        if self.tie_points:
            self.writep(fh, 'tiefile', self.tiefile)

    def write_ties(self, path):
        if self.tie_points:
            with open(path, 'w') as fh:
                for a, b in self.tie_points:
                    if (self.series1.series[0].contains(a) and
                        self.series2.series[0].contains(b)):
                        fh.write(" {0:16.7e} {1:16.7e}\n".format(a, b))

    def run_match(self, match_path, dir_path, dummy_run = False):
        """Run the match program with this configuration, in the specified
        directory. If the directory does not exist it will be created."""
        if not os.path.isdir(dir_path):
            os.mkdir(dir_path)
        name = self.name
        conf_path = os.path.join(dir_path, name+'.conf')
        self.write_ties(os.path.join(dir_path, name+'.tie'))
        with open(conf_path, 'w') as fh:
            self.write_to(fh)
        for ss in [self.series1.series, self.series2.series]:
            for s in ss:
                s.write_to_dir(dir_path)
        if not dummy_run:
            p = subprocess.Popen([match_path, name + '.conf'], cwd = dir_path)
            p.wait()
            if p.returncode:
                raise EnvironmentError('Match returned an error (%d) on %s' %
                                       (p.returncode, dir_path))
        return MatchResult(self, dir_path)
        
class MatchResult:
    """The results of a run of the Match program"""

    def __init__(self, match_conf, dir_path):
        self.series1 = []
        for s1 in match_conf.series1.series:
            fn1 = os.path.join(dir_path, s1.name + '.new')
            self.series1.append(Series.read(fn1, name=s1.name+'-tuned',
                                                  col1 = 1, col2 = 2))
        self.match = Series.read(
            os.path.join(dir_path, match_conf.matchfile),
            name = os.path.basename(dir_path)+'-rel', col1 = 1, col2 = 3)
