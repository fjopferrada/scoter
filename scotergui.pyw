#!/usr/bin/env python
# -*- coding: utf-8 -*-

# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = >
# Copyright 2014 Pontus Lurcock
#
# This file is part of Scoter.
#
# Scoter is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Scoter is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Scoter.  If not, see <http://www.gnu.org/licenses/>.
# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = <

import wx
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas
from matplotlib.figure import Figure
from scoter import Scoter, ScoterConfig
import os.path
import forms
import threading
import logging
import time

class ScoterApp(wx.App):
    """An interactive GUI for Scoter.
    
    ScoterGui provides a user-friendly desktop interface to the Scoter program.
    """
    
    def OnInit(self):
        """Initialize the program and display the main window."""
        self.parent_dir = os.path.dirname(os.path.realpath(__file__))
        self.scoter = Scoter()
        self.default_scoter_config = ScoterConfig()
        self.SetVendorName("talvi.net") # may as well adopt the Java convention
        self.SetAppName("Scoter")
        self.lastdir_record = ""
        self.lastdir_config = ""
        self.series_truncations = [[-1, -1], [-1, -1]] # [[targ st, targ end], [rec st, rec end]]

        mf = self.main_frame = forms.MainFrame(None)

        icon_bundle = wx.IconBundle()
        icon_bundle.AddIcon(wx.Icon(self._rel_path("appicon16.png"), wx.BITMAP_TYPE_PNG))
        icon_bundle.AddIcon(wx.Icon(self._rel_path("appicon32.png"), wx.BITMAP_TYPE_PNG))
        icon_bundle.AddIcon(wx.Icon(self._rel_path("appicon64.png"), wx.BITMAP_TYPE_PNG))
        mf.SetIcons(icon_bundle) 
        
        self.axes = []
        self.figure_canvas = []
        for panel in (0,1):
            for subpanel in (0,1):
                self.add_figure(panel, subpanel)

        self.axes_results_sa, self.canvas_results_sa = \
            self.make_results_figures(mf.panel_resultsplot)
        self.axes_results_match, self.canvas_results_match = \
            self.make_results_figures(mf.panel_resultsplot_match)
        
        #self.read_params_from_wxconfig()
        
        progress_figure = Figure()
        progress_figure.set_size_inches(1, 1)
        self.progress_axes = progress_figure.add_axes([0.05, 0.2, 0.93, 0.7])
        self.progress_canvas = FigureCanvas(mf.panel_progressplot, -1, progress_figure)
        mf.panel_progressplot.GetSizer().Add(self.progress_canvas, 1, wx.EXPAND | wx.ALL)
        
        bind = mf.Bind
        bind(wx.EVT_BUTTON, self.read_record_clicked, mf.button_read_d18o_record)
        bind(wx.EVT_BUTTON, self.read_record_clicked, mf.button_read_d18o_target)
        bind(wx.EVT_BUTTON, self.read_record_clicked, mf.button_read_rpi_record)
        bind(wx.EVT_BUTTON, self.read_record_clicked, mf.button_read_rpi_target)
        bind(wx.EVT_BUTTON, self.clear_record_clicked, mf.button_clear_d18o_record)
        bind(wx.EVT_BUTTON, self.clear_record_clicked, mf.button_clear_d18o_target)
        bind(wx.EVT_BUTTON, self.clear_record_clicked, mf.button_clear_rpi_record)
        bind(wx.EVT_BUTTON, self.clear_record_clicked, mf.button_clear_rpi_target)        
        bind(wx.EVT_BUTTON, self.correlate, mf.button_correlate)
        bind(wx.EVT_MENU, self.quit, mf.menuitem_quit)
        bind(wx.EVT_MENU, self.about, mf.menuitem_about)
        bind(wx.EVT_MENU, self.save_config_to_file, mf.menuitem_save_config)
        bind(wx.EVT_MENU, self.open_read_config_dialog, mf.menuitem_read_config)
        bind(wx.EVT_MENU, self.reset_config, mf.menuitem_reset_config)
        bind(wx.EVT_BUTTON, self.abort_simann, mf.button_abort)
        mf.Bind(wx.EVT_CLOSE, self.quit)
        
        for i in range(4):
            self.figure_canvas[i].mpl_connect("button_press_event", self.click_on_series)
        
        notebook = mf.Notebook
        notebook.SetSelection(0)
        mf.SetDropTarget(ConfigFileDropTarget(self))
        mf.Center()
        mf.Show()
        
        # Ugly hack to force Windows to draw graphs at correct size.
        width, height = mf.GetSize()
        mf.SetSize((width+1,height))
        mf.SetSize((width-1,height))
        
        self.about_frame = AboutScoter(self)
        self.update_gui_from_wxconfig()
        self.plot_series()
        return True
    
    def _rel_path(self, filename):
        """Resolve a filename relative to the parent directory of this script."""
        return os.path.join(self.parent_dir, filename)
    
    def click_on_series(self, event):
        """Respond to a mouse click on a data series plot."""
        for i in range(4):
            if self.figure_canvas[i] == event.canvas:
                truncs = self.series_truncations[i%2]
                if event.button == 1:
                    truncs[0] = event.xdata
                elif event.button == 2:
                    truncs[0] = truncs[1] = -1
                elif event.button == 3:
                    truncs[1] = event.xdata
                    if truncs[0] == -1: truncs[0] = 0
                if truncs[0] > -1 and truncs[1] > -1 and truncs[0] > truncs[1]:
                    truncs[0], truncs[1] = truncs[1], truncs[0]
        self.plot_series()
    
    def make_results_figures(self, panel):
        """Create the figures for the correlation results"""
        figure = Figure()
        figure.set_size_inches(1, 1) # the FigureCanvas uses this as a minimum size
        axes = (figure.add_subplot(211), figure.add_subplot(212))
        axes[0].invert_yaxis() # δ18O is conventionally plotted increasing downward.
        canvas = FigureCanvas(panel, -1, figure)
        panel.GetSizer().Add(canvas, 1, wx.EXPAND | wx.ALL)
        return axes, canvas
    
    def add_figure(self, page, panel):
        """Create a figure for a data series plot.
        
        Args:
            page: 0 for the d18O page, 1 for the RPI page
            panel: 0 for the record panel, 1 for the target panel
        """
        panel_obj = getattr(self.main_frame, "DataPanel%d%d" % (page, panel))
        figure = Figure()
        figure.set_size_inches(1, 1) # the FigureCanvas uses this as a minimum size
        axes = figure.add_axes([0.05, 0.2, 0.93, 0.7])
        axes.set_xlabel("Depth" if panel==0 else "Time")
        axes.set_ylabel("$\delta^{18}\mathrm{O}$" if page==0 else "RPI")
        if page==0: axes.invert_yaxis()
        self.axes.append(axes)
        figure_canvas = FigureCanvas(panel_obj, -1, figure)
        self.figure_canvas.append(figure_canvas)
        sizer = panel_obj.GetSizer()
        figure_canvas.SetDropTarget(DataSeriesFileDropTarget(self, page, panel))
        sizer.Add(figure_canvas, 1, wx.EXPAND | wx.ALL)

    def plot_results_sa(self):
        """Plot the results of a simulated annealing correlation."""
        for record_type in (0, 1):
            axes = self.axes_results_sa[record_type]
            axes.clear()
            target = self.scoter.warp_sa.series[1].series[record_type]
            if target != None and self.scoter.series[0][record_type] != None:
                axes.plot(target.data[0], target.data[1])
                aligned = self.scoter.aligned_sa[record_type]
                axes.plot(aligned.data[0], aligned.data[1])
                axes.autoscale()
        self.canvas_results_sa.draw()
    
    def plot_results_match(self):
        """Plot the results of a match correlation."""
        for record_type in (0, 1):
            axes = self.axes_results_match[record_type]
            axes.clear()
            target = self.scoter.series_preprocessed[1][record_type]
            if target != None and self.scoter.series[0][record_type] != None:
                axes.plot(target.data[0], target.data[1])
                aligned = self.scoter.aligned_match[record_type]
                axes.plot(aligned.data[0], aligned.data[1])
                axes.autoscale()
        self.canvas_results_sa.draw()

    def plot_series(self):
        """Plot all the currently loaded input data series."""
        for dataset in (0,1):
            for record_type in (0,1):
                index = 2 * record_type + dataset
                trunc = self.series_truncations[dataset]
                axes = self.axes[index]
                axes.clear()
                series = self.scoter.series[dataset][record_type]
                if series is not None:
                    xs = series.data[0]
                    ys = series.data[1]
                    axes.plot(xs, ys, color="blue")
                    if trunc[0] != -1: axes.axvline(trunc[0], color="green")
                    if trunc[1] != -1: axes.axvline(trunc[1], color="red")
                    if trunc[0] != -1 and trunc[1] != -1:
                        axes.axvspan(trunc[0], trunc[1], color="yellow")
                self.figure_canvas[index].draw()
    
    def clear_record_clicked(self, event):
        """Respond to a click on one of the "Clear Record" buttons."""
        eo = event.GetEventObject()
        fr = self.main_frame
        if eo == fr.button_clear_d18o_record:
            index, record_type = 0, 0
        elif eo == fr.button_clear_rpi_record:
            index, record_type = 0, 1
        elif eo == fr.button_clear_d18o_target:
            index, record_type = 1, 0
        elif eo == fr.button_clear_rpi_target:
            index, record_type = 1, 1
        else:
            index, record_type = -1, -1
        assert(0 <= index <= 1)
        assert(0 <= record_type <= 1)
        self.scoter.clear_data(index, record_type)
        self.plot_series()
    
    def read_record_clicked(self, event):
        """Respond to a click on one of the "Read Record" buttons."""
        eo = event.GetEventObject()
        fr = self.main_frame
        if eo == fr.button_read_d18o_record:
            index, record_type = 0, 0
        elif eo == fr.button_read_rpi_record:
            index, record_type = 0, 1
        elif eo == fr.button_read_d18o_target:
            index, record_type = 1, 0
        elif eo == fr.button_read_rpi_target:
            index, record_type = 1, 1
        else:
            index, record_type = -1, -1
        assert(0 <= index <= 1)
        assert(0 <= record_type <= 1)
        dialog = wx.FileDialog(self.main_frame, "Choose a file", self.lastdir_record,
                               "", "*.*", wx.OPEN)
        if dialog.ShowModal() == wx.ID_OK:
            leafname = dialog.GetFilename()
            dirname = dialog.GetDirectory()
            self.lastdir_record = dirname
            filename = os.path.join(dirname, leafname)
            self.scoter.read_data(index, record_type, filename)
            self.series_truncations[index] = [-1, -1]
            self.plot_series()
        dialog.Destroy()
    
    def read_record_dragged(self, page, panel, filenames):
        self.scoter.read_data(panel, page, filenames[0])
        self.series_truncations[panel] = [-1, -1]
        self.plot_series()
    
    def correlate_sa(self):
        """Perform a simulated annealing correlation"""
        self.progress_axes.clear()
        self.progress_percentage = 0
        self.progress_lines = []
        for _ in 0, 1:
            xs = range(self.params.nblocks)
            ys = range(self.params.nblocks)
            self.progress_lines.append(self.progress_axes.plot(xs, ys)[0])

        self.simann_abort_flag = False
        # avoid multiple simultaneous live plot updates
        self.simann_redraw_queued = False
        thread = threading.Thread(target = self.scoter.correlate_sa,
                                  args = (None, self.params, self))
        thread.start()

        self.soln_current = None
        self.soln_new = None
        self.main_frame.text_progress.SetLabel("Simulated annealing in progress…")
        self.main_frame.Notebook.SetSelection(4)
    
    def correlate(self, event):
        """Correlate the data using both simulated annealing and the match program."""
        self.read_params_from_gui()
        self.scoter.preprocess(self.params)
        self.correlate_sa()
        thread = threading.Thread(target = self.correlate_match,
                                  args = (self.params,))
        thread.start()
    
    def abort_simann(self, event):
        """Handle a click on the simulated annealing abort button."""
        self.simann_abort_flag = True
    
    def redraw_sa_live_plot(self):
        """Update the live plot of simulated annealing progress."""
        scale = 1.
        logger.debug("Solution: "+str(self.soln_current))
        if self.soln_current != None:
            soln_current, soln_new = self.soln_current, self.soln_new
            for i, soln in ((0, soln_current), (1, soln_new)):
                xs, ys = soln.get_coords()
                self.progress_lines[i].set_xdata([x * scale for x in xs])
                self.progress_lines[i].set_ydata([y * scale for y in ys])
                self.progress_canvas.draw()
        self.simann_redraw_queued = False
            
    def simann_callback_update(self, soln_current, soln_new, percentage):
        """Callback to update simulated annealing live display.
        
        During simulated annealing, this method is called periodically by
        the Scoter object during simulated annealing."""
        percentage_int = int(percentage)
        # We avoid excessive GUI updates by rounding to the nearest whole percentage,
        # caching the value, and only updating the bar when it changes.
        if percentage_int == self.progress_percentage: return
        self.progress_percentage = percentage_int
        wx.CallAfter(self.main_frame.simann_progress_gauge.SetValue, percentage_int)
        self.soln_current = soln_current
        self.soln_new = soln_new
        if not self.simann_redraw_queued:
            self.simann_redraw_queued = True
            wx.CallAfter(self.redraw_sa_live_plot)
        time.sleep(.01) # yield thread
        
    def simann_callback_finished(self, status):
        """Callback to deal with completion of simulated annealing.
        
        This method is called by the Scoter object when simulated annealing is
        complete."""
        if status == "completed":
            wx.CallAfter(self.main_frame.text_progress.SetLabel, "Correlation complete.")
            wx.CallAfter(self.plot_results_sa)
            wx.CallAfter(self.main_frame.Notebook.SetSelection, 5)
            wx.CallAfter(self.main_frame.simann_progress_gauge.SetValue, 0)
        elif status == "aborted":
            wx.CallAfter(self.main_frame.text_progress.SetLabel, "Correlation aborted.")
        else:
            wx.CallAfter(self.main_frame.text_progress.SetLabel,
                         "Correlation finished with unrecognized status: "+status)
    
    def simann_check_abort(self):
        """Callback to notify Scoter when user aborts simulated annealing.
        
        This function returns True if the user has clicked on "Abort". It is polled
        at regular intervals by the Scoter simulated annealing thread.
        """
        return self.simann_abort_flag
        
    def correlate_match(self, params):
        """Perform a correlation using the external match program."""
        self.scoter.correlate_match(self.params)
        wx.CallAfter(self.match_finished_callback)
    
    def match_finished_callback(self):
        """A callback to be called after a match correlation has been completed.
        
        Currently just plots the match results."""
        self.plot_results_match()
        
    def quit(self, event):
        """Quit the program."""
        self.write_gui_to_wxconfig()
        self.Destroy()
        wx.Exit()
    
    def about(self, event):
        """Show the "About" dialog."""
        wx.AboutBox(self.about_frame)
    
    def save_config_to_file(self, event):
        """Save ScoterGui configuration to a user-specified wx.FileConfig file.
        
        Note that this method saves the current state of the GUI, using a
        wx.FileConfig which can only be read by ScoterGui. It does not produce a
        Python ConfigParser configuration suitable for use by Scoter itself.
        """
        dialog = wx.FileDialog(self.main_frame, "Save configuration to file",
                               self.lastdir_config, "config.cfg",
                               "Configuration files (*.cfg)|*.cfg|All files|*",
                               wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT)
        if dialog.ShowModal() == wx.ID_OK:
            leafname = dialog.GetFilename()
            dirname = dialog.GetDirectory()
            filename = os.path.join(dirname, leafname)
            self.lastdir_config = dirname
            conf = wx.FileConfig(appName = "scoter", vendorName = "talvi.net",
                                 localFilename = filename,
                                 style = wx.CONFIG_USE_LOCAL_FILE)
            self.write_gui_to_wxconfig(conf)
        dialog.Destroy()
        
    def open_read_config_dialog(self, event):
        """Read ScoterGui configuration from a user-specified wx.FileConfig file.
        
        Note that a ScoterGui configuration is different from a Scoter configuration.
        """
        dialog = wx.FileDialog(self.main_frame, "Read configuration from file",
                               self.lastdir_config, "",
                               "Configuration files (*.cfg)|*.cfg|All files|*",
                               wx.FD_OPEN)
        if dialog.ShowModal() == wx.ID_OK:
            leafname = dialog.GetFilename()
            dirname = dialog.GetDirectory()
            filename = os.path.join(dirname, leafname)
            self.read_config_from_file(filename)
            self.lastdir_config = dirname

        dialog.Destroy()
    
    def read_config_from_file(self, filename):
        conf = wx.FileConfig(appName = "scoter", vendorName = "talvi.net",
                             localFilename = filename,
                             style = wx.CONFIG_USE_LOCAL_FILE)
        self.update_gui_from_wxconfig(conf)        
    
    def reset_config(self, event):
        """Reset configuration to default values.
        """
        choice = wx.MessageBox("Are you sure you want to reset all settings to "+
                               "their default values?", "Reset configuration", 
                               wx.YES_NO | wx.ICON_WARNING | wx.NO_DEFAULT)
        if choice == wx.YES:
            wxc = wx.Config("scoter")
            wxc.DeleteAll()
            self.update_gui_from_wxconfig()
    
    def update_gui_from_wxconfig(self, config = None):
        """Update the GUI from a supplied wx.Config object.
        
        Args:
            config: configuration to use; if None, use default values from Scoter.
        """
        logger.debug("Updating GUI from config: %s", str(config))
        mf = self.main_frame
        wxc = config
        if wxc==None: wxc = wx.Config("scoter")
        logger.debug("Reading configuration; %d items", wxc.GetNumberOfEntries())
        d = self.default_scoter_config
        detrend_map = {"none":0, "submean":1, "linear":2}
        mf.preproc_detrend.SetSelection(detrend_map.get(wxc.Read("detrend", d.detrend), "none"))
        mf.preproc_normalize.SetValue(wxc.ReadBool("normalize", d.normalize))
        interp_type = wxc.Read("interp_type", d.interp_type)
        mf.preproc_interp_none.SetValue(interp_type == "none")
        mf.preproc_interp_min.SetValue(interp_type == "min")
        mf.preproc_interp_max.SetValue(interp_type == "max")
        mf.preproc_interp_explicit.SetValue(interp_type == "explicit")
        interp_npoints = wxc.ReadInt("interp_npoints", -1)
        if interp_npoints != -1:
            mf.preproc_interp_npoints.SetValue(interp_npoints)
        mf.corr_common_intervals.SetValue(str(wxc.ReadInt("nblocks", d.nblocks)))
        mf.corr_sa_max_rate.SetValue(str(wxc.ReadInt("max_rate", d.max_rate)))
        mf.corr_sa_max_changes.SetValue(str(wxc.ReadInt("max_changes", d.max_changes)))
        mf.corr_sa_max_steps.SetValue(str(wxc.ReadInt("max_steps", d.max_steps)))
        mf.corr_sa_rate.SetValue(str(wxc.ReadFloat("cooling", d.cooling)))
        mf.corr_sa_temp_final.SetValue(str(wxc.ReadFloat("temp_final", d.temp_final)))
        mf.corr_sa_temp_init.SetValue(str(wxc.ReadFloat("temp_init", d.temp_init)))
        mf.corr_sa_rc_penalty.SetValue(str(wxc.ReadFloat("rc_penalty", d.rc_penalty)))
        mf.corr_sa_seed.SetValue(str(wxc.ReadInt("random_seed", d.random_seed)))
        mf.corr_match_nomatch.SetValue(str(wxc.ReadFloat("match_nomatch", d.match_nomatch)))
        mf.corr_match_speed.SetValue(str(wxc.ReadFloat("match_speed_p", d.match_speed_p)))
        mf.corr_match_tie.SetValue(str(wxc.ReadFloat("match_tie_p", d.match_tie_p)))
        mf.corr_match_target.SetValue(str(wxc.Read("match_target_speed", d.match_target_speed)))
        mf.corr_match_speedchange.SetValue(str(wxc.ReadFloat("match_speedchange_p", d.match_speedchange_p)))
        mf.corr_match_gap.SetValue(str(wxc.ReadFloat("match_gap_p", d.match_gap_p)))
        mf.corr_match_rates.SetValue(str(wxc.Read("match_rates", d.match_rates)))
        mf.corr_match_guessed_path.SetValue(str(self.scoter.default_match_path))
        mf.corr_match_guess_button.SetValue(not wxc.ReadBool("match_use_specified_path", False))
        mf.corr_match_specify_button.SetValue(wxc.ReadBool("match_use_specified_path", False))
        mf.corr_match_specified_path.SetValue(wxc.Read("match_specified_path"))

        self.scoter.read_data(1, 0, wxc.Read("target_d18o_file"))
        self.scoter.read_data(0, 0, wxc.Read("record_d18o_file"))
        self.scoter.read_data(1, 1, wxc.Read("target_rpi_file"))
        self.scoter.read_data(0, 1, wxc.Read("record_rpi_file"))
        self.series_truncations[0][0] = wxc.ReadFloat("target_start", d.target_start)
        self.series_truncations[0][1] = wxc.ReadFloat("target_end", d.target_end)
        self.series_truncations[1][0] = wxc.ReadFloat("record_start", d.record_start)
        self.series_truncations[1][1] = wxc.ReadFloat("record_end", d.record_end)
        
        if wxc.HasEntry("lastdir_record"):
            self.lastdir_record = wxc.Read("lastdir_record", "")
        if wxc.HasEntry("lastdir_config"):
            self.lastdir_config = wxc.Read("lastdir_config", "")
        
        self.plot_series()

    def write_gui_to_wxconfig(self, wxc = None):
        """Write the current state of the GUI to a supplied wx.Config object.
        
        Args:
            config: configuration to use; if None, use wx.Config("scoter").
        """
        mf = self.main_frame
        detrend_opts = ("none", "submean", "linear")
        interp_type = "none"
        if mf.preproc_interp_min.GetValue():
            interp_type = "min"
        elif mf.preproc_interp_max.GetValue():
            interp_type = "max"
        elif mf.preproc_interp_explicit.GetValue():
            interp_type = "explicit"
        mf = self.main_frame
        if wxc == None: wxc = wx.Config("scoter")
        wxc.Write("detrend", detrend_opts[mf.preproc_detrend.GetSelection()])
        wxc.WriteBool("normalize", mf.preproc_normalize.GetValue())
        wxc.WriteInt("max_rate", int(mf.corr_sa_max_rate.GetValue()))
        wxc.Write("interp_type", interp_type)
        wxc.WriteInt("interp_npoints", mf.preproc_interp_npoints.GetValue())
        wxc.WriteInt("nblocks", int(mf.corr_common_intervals.GetValue()))
        wxc.WriteInt("max_rate", int(mf.corr_sa_max_rate.GetValue()))
        wxc.WriteFloat("temp_init", float(mf.corr_sa_temp_init.GetValue()))
        wxc.WriteFloat("temp_final", float(mf.corr_sa_temp_final.GetValue()))
        wxc.WriteFloat("cooling", float(mf.corr_sa_rate.GetValue()))
        wxc.WriteInt("max_changes", int(mf.corr_sa_max_changes.GetValue()))
        wxc.WriteInt("max_steps", int(mf.corr_sa_max_steps.GetValue()))
        wxc.WriteFloat("rc_penalty", float(mf.corr_sa_rc_penalty.GetValue()))
        wxc.WriteInt("random_seed", int(mf.corr_sa_seed.GetValue()))
        wxc.WriteFloat("match_nomatch", float(mf.corr_match_nomatch.GetValue()))
        wxc.WriteFloat("match_speed_p", float(mf.corr_match_speed.GetValue()))
        wxc.WriteFloat("match_tie_p", float(mf.corr_match_tie.GetValue()))
        wxc.Write("match_target_speed", mf.corr_match_target.GetValue())
        wxc.WriteFloat("match_speedchange_p", float(mf.corr_match_speedchange.GetValue()))
        wxc.WriteFloat("match_gap_p", float(mf.corr_match_gap.GetValue()))
        wxc.Write("match_rates", mf.corr_match_rates.GetValue())
        wxc.Write("match_specified_path", mf.corr_match_specified_path.GetValue())
        wxc.WriteBool("match_use_specified_path", mf.corr_match_specify_button.GetValue())
        wxc.Write("target_d18o_file", self.scoter.filenames[1][0])
        wxc.Write("record_d18o_file", self.scoter.filenames[0][0])
        wxc.Write("target_rpi_file", self.scoter.filenames[1][1])
        wxc.Write("record_rpi_file", self.scoter.filenames[0][1])
        wxc.WriteFloat("target_start", self.series_truncations[0][0])
        wxc.WriteFloat("target_end", self.series_truncations[0][1])
        wxc.WriteFloat("record_start", self.series_truncations[1][0])
        wxc.WriteFloat("record_end", self.series_truncations[1][1])
        
        if self.lastdir_record != None:
            wxc.Write("lastdir_record", self.lastdir_record)
        if self.lastdir_config != None:
            wxc.Write("lastdir_config", self.lastdir_config)
        wxc.Flush()

        logger.debug("Wrote configuration; %d items", wxc.GetNumberOfEntries())
        
    def read_params_from_gui(self):
        """Create a ScoterConfig object from the current state of the GUI.
        
        The object is not returned, but is stored as self.params.
        """
        mf = self.main_frame
        detrend_opts = ("none", "submean", "linear")
        interp_type = "none"
        interp_npoints = None
        if mf.preproc_interp_min.GetValue():
            interp_type = "min"
        elif mf.preproc_interp_max.GetValue():
            interp_type = "max"
        elif mf.preproc_interp_explicit.GetValue():
            interp_type = "explicit"
            interp_npoints = mf.preproc_interp_npoints.GetValue()
        if mf.corr_match_guess_button.GetValue():
            match_path = ""
        else:
            match_path = mf.corr_match_specified_path.GetValue()
        trunc = self.series_truncations
        self.params = ScoterConfig(detrend = detrend_opts[mf.preproc_detrend.GetSelection()],
                                   normalize = mf.preproc_normalize.GetValue(),
                                   max_rate = int(mf.corr_sa_max_rate.GetValue()),
                                   interp_type = interp_type,
                                   interp_npoints = interp_npoints,
                                   nblocks = int(mf.corr_common_intervals.GetValue()),
                                   max_changes = float(mf.corr_sa_max_changes.GetValue()),
                                   max_steps = float(mf.corr_sa_max_steps.GetValue()),
                                   temp_init = float(mf.corr_sa_temp_init.GetValue()),
                                   temp_final = float(mf.corr_sa_temp_final.GetValue()),
                                   cooling = float(mf.corr_sa_rate.GetValue()),
                                   rc_penalty = float(mf.corr_sa_rc_penalty.GetValue()),
                                   random_seed = int(mf.corr_sa_seed.GetValue()),
                                   match_nomatch = float(mf.corr_match_nomatch.GetValue()),
                                   match_speed_p = float(mf.corr_match_speed.GetValue()),
                                   match_tie_p = float(mf.corr_match_tie.GetValue()),
                                   match_target_speed = mf.corr_match_target.GetValue(),
                                   match_speedchange_p = float(mf.corr_match_speedchange.GetValue()),
                                   match_gap_p = float(mf.corr_match_gap.GetValue()),
                                   match_rates = mf.corr_match_rates.GetValue(),
                                   match_path = match_path,
                                   target_d18o_file = "",
                                   record_d18o_file = "",
                                   target_rpi_file = "",
                                   record_rpi_file = "",
                                   target_start = trunc[0][0],
                                   target_end = trunc[0][1],
                                   record_start = trunc[1][0],
                                   record_end = trunc[1][1]
                                   )

class DataSeriesFileDropTarget(wx.FileDropTarget):

    def __init__(self, scotergui, page, panel):
        self.scotergui = scotergui
        self.page = page
        self.panel = panel
        wx.FileDropTarget.__init__(self)
 
    def OnDropFiles(self, x, y, filenames):
        self.scotergui.read_record_dragged(self.page, self.panel, filenames)

class ConfigFileDropTarget(wx.FileDropTarget):

    def __init__(self, scotergui):
        self.scotergui = scotergui
        wx.FileDropTarget.__init__(self)

    def OnDropFiles(self, x, y, filenames):
        self.scotergui.read_config_from_file(filenames[0])

class AboutScoter(wx.AboutDialogInfo):
    """An "About" dialog for ScoterGui."""
    
    def __init__(self, scotergui):
        super(AboutScoter, self).__init__()
        self.SetName("Scoter")
        self.SetIcon(wx.Icon(scotergui._rel_path("appicon64.png"), wx.BITMAP_TYPE_PNG))
        self.SetVersion("0.00")
        self.SetWebSite("https://bitbucket.org/pont/scoter")
        self.SetDescription("A program for the correlation of geological records.")
        self.SetCopyright("(C) Pontus Lurcock 2013")
        # Don't use SetLicence since it disables native about boxes on Windows & Mac --
        # see docs for details.
        self.SetDevelopers(("Pontus Lurcock",))

def main():
    logging.basicConfig(level=logging.DEBUG)
    app = ScoterApp()
    app.MainLoop()

logger = logging.getLogger(__name__)
if __name__ == "__main__":
    main()
