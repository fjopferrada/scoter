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
import os
import forms
import threading
import logging
import shutil
import sys
import subprocess
import tempfile
import zipfile

# Attribute names for last used directories for file dialogs.
# These also serve as keys in the wxConfig file.
_last_dirs = tuple(map(lambda x: "lastdir_"+x,
                       ("record", "config", "export_scoter")))
# mapps role to its index
_roledict = {"record" : 0, "target" : 1}
# maps parameter to its index
_paramdict = {"d18o" : 0, "rpi" : 1}
# map limit to its index
_limitdict = {"start" : 0, "end" : 1}

_gui_text_fields = (
# name of widget           ScoterConfig field     type   description
("preproc_weight_d18o",    "weight_d18o",         float, "δ18O weight"),
("preproc_weight_rpi",     "weight_rpi",          float, "RPI weight"),
("corr_sa_intervals",      "sa_intervals",        int,   "SA intervals"),
("corr_sa_temp_init",      "temp_init",           float, "Initial temperature"),
("corr_sa_temp_final",     "temp_final",          float, "Final temperature"),
("corr_sa_cooling",        "cooling",             float, "Cooling rate"),
("corr_sa_max_changes",    "max_changes",         int,   "Changes threshold"),
("corr_sa_max_steps",      "max_steps",           int,   "Steps threshold"),
("corr_sa_seed",           "random_seed",         int,   "Random seed"),
("corr_sa_rc_penalty",     "rc_penalty",          float, "SA rate change penalty"),
("corr_sa_max_rate",       "max_rate",            int,   "SA maximum rate"),
("corr_match_nomatch",     "match_nomatch",       float, "No match penalty"),
("corr_match_speed_p",     "match_speed_p",       float, "Speed penalty"),
("corr_match_tie_p",       "match_tie_p",         float, "Tie penalty"),
("corr_match_target",      "match_target_speed",  str,   "Target speed"),
("corr_match_speedchange", "match_speedchange_p", float, "Speed change penalty"),
("corr_match_gap",         "match_gap_p",         float, "Gap penalty"),
("corr_match_intervals",   "match_intervals",     int,   "Match intervals"),
("corr_match_rates",       "match_rates",         str,   "Match rates")
)

class ScoterApp(wx.App):
    """An interactive GUI for Scoter.
    
    ScoterGui provides a user-friendly desktop interface to the Scoter program.
    """
    
    def OnInit(self):
        """Initialize the program and display the main window."""
        sys.excepthook = self.exception_handler
        install_thread_excepthook()
        self.debug = ""
        self.parent_dir = os.path.dirname(os.path.realpath(__file__))
        self.scoter = Scoter()
        self.default_scoter_config = ScoterConfig()
        self.SetVendorName("talvi.net") # may as well adopt the Java convention
        self.SetAppName("Scoter")
        self.series_truncations = [[-1, -1], [-1, -1]] # [[targ st, targ end], [rec st, rec end]]

        mf = self.main_frame = forms.MainFrame(None)

        self.licence_dialog = forms.LicenceDialog(mf)
        with open(self._rel_path("COPYING")) as fh:
            lines = fh.readlines()
            self.licence_dialog.text_licence.SetValue("".join(lines))
        
        self.bundle_dialog = forms.SaveBundleDialog(mf)

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
        
        for parameter in "d18o", "rpi":
            for role in "record", "target":
                for limit in "start", "end":
                    handler = self.make_limit_change_handler(limit, parameter, role)
                    widget = getattr(mf, "text_%s_%s_%s" % (parameter, role, limit))
                    bind(wx.EVT_TEXT_ENTER, handler, widget)
                for action in "read", "clear":
                    handler = self.make_click_handler(action, parameter, role)
                    widget = getattr(mf, "button_%s_%s_%s" % (action, parameter, role))
                    bind(wx.EVT_BUTTON, handler, widget)
                    
        bind(wx.EVT_BUTTON, self.correlate, mf.button_correlate)
        bind(wx.EVT_MENU, self.quit, mf.menuitem_quit)
        bind(wx.EVT_MENU, self.about, mf.menuitem_about)
        bind(wx.EVT_MENU, self.open_user_guide, mf.menuitem_userguide)
        bind(wx.EVT_MENU, self.show_save_wxconfig_dialog, mf.menuitem_save_config)
        bind(wx.EVT_MENU, self.show_read_config_dialog, mf.menuitem_read_config)
        bind(wx.EVT_MENU, self.reset_config, mf.menuitem_reset_config)
        bind(wx.EVT_MENU, self.revert_config, mf.menuitem_revert_config)
        bind(wx.EVT_MENU, self.show_licence, mf.menuitem_show_licence)
        bind(wx.EVT_MENU, self.show_export_scoter_dialog, mf.menuitem_export_scoter)
        bind(wx.EVT_MENU, self.show_export_bundle_dialog, mf.menuitem_export_bundle)
        bind(wx.EVT_BUTTON, self.abort_simann, mf.button_abort)
        self.licence_dialog.Bind(wx.EVT_BUTTON,
             lambda e: self.licence_dialog.Show(False),
             self.licence_dialog.button_close)
        self.bundle_dialog.Bind(wx.EVT_BUTTON,
            lambda e: self.bundle_dialog.EndModal(wx.ID_OK),
            self.bundle_dialog.button_create)
        self.bundle_dialog.Bind(wx.EVT_BUTTON,
            lambda e: self.bundle_dialog.EndModal(wx.ID_CANCEL),
            self.bundle_dialog.button_cancel)
        mf.Bind(wx.EVT_CLOSE, self.quit)
        
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
    
    def exception_handler(self, type, value, traceback):
        wx.MessageBox(str(value),
                      "Exception",
                      wx.OK | wx.ICON_ERROR)
    
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
        figure.set_size_inches(1, 1) # FigureCanvas uses this as minimum size
        axes = (figure.add_subplot(211), figure.add_subplot(212))
        axes[0].invert_yaxis() # δ18O usually plotted increasing downward.
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
        figure.set_size_inches(1, 1) # FigureCanvas uses this as a minimum size
        axes = figure.add_axes([0.05, 0.2, 0.93, 0.7])
        axes.set_xlabel("Depth" if panel==0 else "Time")
        axes.set_ylabel("$\delta^{18}\mathrm{O}$" if page==0 else "RPI")
        if page==0: axes.invert_yaxis()
        self.axes.append(axes)
        figure_canvas = FigureCanvas(panel_obj, -1, figure)
        figure_canvas.mpl_connect("button_press_event", self.click_on_series)
        self.figure_canvas.append(figure_canvas)
        sizer = panel_obj.GetSizer()
        figure_canvas.SetDropTarget(DataSeriesFileDropTarget(self, page, panel))
        sizer.Add(figure_canvas, 1, wx.EXPAND | wx.ALL)

    def plot_results_sa(self):
        """Plot the results of a simulated annealing correlation."""
        logging.debug("Plotting SA results")
        for record_type in range(self.scoter.n_record_types):
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
        logging.debug("Plotting Match results")
        for record_type in range(self.scoter.n_record_types):
            axes = self.axes_results_match[record_type]
            axes.clear()
            target = self.scoter.series_preprocessed[1][record_type]
            if (target != None and self.scoter.series[0][record_type] != None and
                hasattr(self.scoter, "aligned_match")):
                axes.plot(target.data[0], target.data[1])
                aligned = self.scoter.aligned_match[record_type]
                axes.plot(aligned.data[0], aligned.data[1])
                axes.autoscale()
        self.canvas_results_match.draw()

    def plot_series(self):
        """Plot all the currently loaded input data series.
        
        Also update displayed filenames and clipping limits for series.
        """
        for role in (0,1):
            for parameter in (0,1):
                paraname = ("d18o","rpi")[parameter]
                rolename = ("record","target")[role]
                widget_prefix = "text_%s_%s_" % (paraname, rolename)
                fn_widget = getattr(self.main_frame,
                                    widget_prefix + "filename")
                maxlen = 40
                filename = self.scoter.filenames[role][parameter]
                if len(filename) > maxlen:
                    filename = u"…" + filename[-maxlen:]
                fn_widget.SetValue(filename)
                index = 2 * parameter + role
                trunc = self.series_truncations[role]
                axes = self.axes[index]
                getattr(self.main_frame, widget_prefix + "start").SetValue("")
                getattr(self.main_frame, widget_prefix + "end").SetValue("")
                axes.clear()
                series = self.scoter.series[role][parameter]
                if series is not None:
                    xs = series.data[0]
                    ys = series.data[1]
                    axes.plot(xs, ys, color="blue")
                    if trunc[0] != -1:
                        axes.axvline(trunc[0], color="green")
                        widget = getattr(self.main_frame, widget_prefix + "start")
                        widget.SetValue(str(trunc[0]))
                    if trunc[1] != -1:
                        axes.axvline(trunc[1], color="red")
                        widget = getattr(self.main_frame, widget_prefix + "end")
                        widget.SetValue(str(trunc[1]))
                    if trunc[0] != -1 and trunc[1] != -1:
                        axes.axvspan(trunc[0], trunc[1], color="yellow")
                self.figure_canvas[index].draw()

    def make_limit_change_handler(self, limit, parameter, role):
        def handler(event):
            self.series_limit_changed(event, limit, parameter, role)
        return handler

    def series_limit_changed(self, event, limit, parameter, role):
        """Respond to a change in a series limit text box."""
        widget_name = "text_%s_%s_%s" % (parameter, role, limit)
        widget = getattr(self.main_frame, widget_name)
        value_str = widget.GetValue()
        role_ = _roledict[role]
        parameter_ = _paramdict[parameter]
        limit_ = _limitdict[limit]
        prev_value = self.series_truncations[role_][limit_]
        value = None
        try:
            value = float(value_str)
            if self.scoter.series[role_][parameter_] == None:
                wx.MessageBox("There is no data for this series, so you can't change its limits.",
                              "Invalid limit", 
                              wx.OK | wx.ICON_ERROR)
                value = None
            elif value < 0:
                wx.MessageBox("Limits must be positive.",
                              "Invalid limit", 
                              wx.OK | wx.ICON_ERROR)
                value = None
            elif value > self.scoter.series[role_][parameter_].end():
                wx.MessageBox("Limits cannot be beyond the end of the series.",
                              "Invalid limit", 
                              wx.OK | wx.ICON_ERROR)
                value = None
        except ValueError:
            wx.MessageBox("‘%s’ is not a valid number." % value_str,
                          "Invalid limit", 
                          wx.OK | wx.ICON_ERROR)
        if value == None:
            widget.SetValue(str(prev_value))
            return
        limits = self.series_truncations[role_]
        limits[limit_] = value
        if limits[0] > limits[1]:
            limits[0], limits[1] = limits[1], limits[0] 
        self.plot_series()

    def make_click_handler(self, action, parameter, role):
        def handler(event):
            self.series_button_clicked(event, action, parameter, role)
        return handler
    
    def series_button_clicked(self, event, action, parameter, role):
        """Respond to a click on one of the Read or Clear buttons."""
        logger.debug("%s %s %s" % (action, parameter, role))
        parameter_ = _paramdict[parameter]
        parameter_display = ("δ18O", "RPI")[parameter_]
        role_ = _roledict[role]
        if action == "read":
            dialog = wx.FileDialog(self.main_frame,
                                   "Select file for %s %s" % (parameter_display, role),
                                   self.lastdir_record,
                                   "", "*.*", wx.OPEN)
            if dialog.ShowModal() == wx.ID_OK:
                leafname = dialog.GetFilename()
                dirname = dialog.GetDirectory()
                self.lastdir_record = dirname
                filename = os.path.join(dirname, leafname)
                self.scoter.read_data(role_, parameter_, filename)
                self.plot_series()
            dialog.Destroy()
        else: # clear record
            self.scoter.clear_data(role_, parameter_)
            if (not self.scoter.has_series(role_, 0) and
                not self.scoter.has_series(role_, 1)):
                # no data for this role, so clear its clipping limits
                self.series_truncations[role_] = [-1, -1]
            self.plot_series()
    
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
            xs = range(self.scoterconfig.sa_intervals)
            ys = range(self.scoterconfig.sa_intervals)
            self.progress_lines.append(self.progress_axes.plot(xs, ys)[0])

        self.simann_abort_flag = False
        # avoid multiple simultaneous live plot updates
        self.simann_redraw_queued = False
        thread = threading.Thread(target = self.scoter.correlate_sa,
                                  args = (None, self.scoterconfig, self))
        thread.start()

        self.soln_current = None
        self.soln_new = None
        self.main_frame.text_progress.SetLabel("Simulated annealing in progress…")
        self.main_frame.Notebook.SetSelection(4)
    
    def correlate(self, event):
        """Correlate the data using both simulated annealing and the match program.
        
        If neither correlation type is currently selected, an error dialog will be
        displayed to the user."""
        
        if (not self.main_frame.corr_sa_active.GetValue() and
            not self.main_frame.corr_match_active.GetValue()):
            wx.MessageBox("At least one of the two correlation methods must be selected.",
                          "No method selected", 
                          wx.OK | wx.ICON_ERROR)
            return

        success = self.make_scoterconfig_from_gui()
        if not success: return
        self.scoter.preprocess(self.scoterconfig)
        if self.scoterconfig.sa_active:
            self.correlate_sa()
        if self.scoterconfig.match_active:
            thread = threading.Thread(target = self.correlate_match,
                                      args = (self.scoterconfig,))
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
            # Disabled until I can get it working properly
            # wx.CallAfter(self.redraw_sa_live_plot)
        #time.sleep(.01) # yield thread
        
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
        match_result = self.scoter.correlate_match(self.scoterconfig)
        wx.CallAfter(self.match_callback_finished, match_result)
    
    def match_callback_finished(self, result):
        """A callback to be called after a match correlation has been completed.
        
        Checks for errors during Match run and plots the match results."""
        if result.error:
            dialog = wx.MessageDialog(self.main_frame, result.stderr, 'Error running the Match program', 
                                      wx.OK | wx.ICON_ERROR)
            dialog.ShowModal()
        else:
            self.plot_results_match()
            if not self.scoterconfig.sa_active:
                self.main_frame.Notebook.SetSelection(6)
        
    def quit(self, event):
        """Quit the program."""
        try:
            self.write_gui_to_wxconfig()
            self.Destroy()
        finally:
            wx.Exit()
    
    def about(self, event):
        """Show the "About" dialog."""
        wx.AboutBox(self.about_frame)
    
    def open_user_guide(self, event):
        """Open the user guide using an external program."""
        
        # Oddly, no cross-platform way to do this until http://bugs.python.org/issue3177
        # is resolved. Six years and counting...
        path = self._rel_path("user-guide/user-guide.html")
        path = os.path.normpath(path)
        if sys.platform.startswith("win32"):
            os.startfile(path) #@UndefinedVariable
        elif sys.platform.startswith("darwin"):
            cmd = ["open", path]
            subprocess.Popen(cmd)
        elif os.name == "posix":
            cmd = ["xdg-open", path]
            subprocess.Popen(cmd)
    
    def show_licence(self, event):
        self.licence_dialog.Centre()
        self.licence_dialog.Show()
    
    def show_export_scoter_dialog(self, event):
        success = self.make_scoterconfig_from_gui()
        if not success: return
        dialog = wx.FileDialog(self.main_frame, "Export plain Scoter configuration",
                               self.lastdir_export_scoter, "plain.cfg",
                               "Configuration files (*.cfg)|*.cfg|All files|*",
                               wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT)
        if dialog.ShowModal() == wx.ID_OK:
            leafname = dialog.GetFilename()
            dirname = dialog.GetDirectory()
            filename = os.path.join(dirname, leafname)
            self.lastdir_export_scoter = dirname
            self.make_scoterconfig_from_gui()
            self.scoterconfig.write_to_file(filename)
        dialog.Destroy()

    def zipdir(self, path, filename):
        zipf = zipfile.ZipFile(filename, "w", zipfile.ZIP_DEFLATED)
        for root, dirs, files in os.walk(path): #@UnusedVariable
            for file_ in files:
                zipf.write(os.path.join(root, file_),
                           os.path.join("scoter-bundle", 
                           os.path.relpath(os.path.join(root, file_), path)))
        zipf.close()

    def make_bundle(self, path, include_scoter = False, include_results = False):
        """Write a stand-alone bundle to a directory.
        
        The bundle contains a Scoter configuration, the input data, and
        (optionally) the Scoter program itself."""
        
        # files constituting the non-interactive version of Scoter
        scoter_files = ("block.py", "COPYING", "match.py", "plot.py", "scoter.py",
                        "series.py", "simann.py")
        files_to_copy = (("readme-bundle", ("README.TXT",)),
                         ("readme-data", ("data", "README.TXT")),
                         ("readme-results", ("results", "README.TXT")),
                         ("readme-scoter", ("scoter", "README.TXT"))
                         )

        # create directories
        if not os.path.exists(path): os.mkdir(path)
        os.mkdir(os.path.join(path, "data"))
        os.mkdir(os.path.join(path, "results"))
        
        # extra/differing configuration options for ScoterConfig
        filename_dict = {"output_dir" : "results"}
        
        # write data files
        for role in (0,1):
            for parameter in (0,1):
                paraname = ("d18o","rpi")[parameter]
                rolename = ("record","target")[role]
                series = self.scoter.series[role][parameter]
                if series is not None:
                    filename = os.path.join("data",
                                            "%s_%s.data" % (rolename, paraname))
                    series.write(os.path.join(path, filename))
                    filename_dict["%s_%s_file" % (rolename, paraname)] = filename
                    
        # write configuration
        config = self.scoterconfig._replace(**filename_dict)
        config_path = os.path.join(path, "scoter.cfg")
        config.write_to_file(config_path)
        
        # write shell script
        with open(os.path.join(path, "run-scoter.sh"), "w") as fh:
            fh.write("#!/usr/bin/env sh\n\n")
            if include_scoter:
                fh.write("python2 scoter/scoter.py scoter.cfg")
            else:
                fh.write("scoter scoter.cfg")
        
        # write Windows batch script
        with open(os.path.join(path, "run-scoter.cmd"), "w") as fh:
            # TODO
            if include_scoter:
                fh.write("python2 scoter\\scoter.py scoter.cfg")
            else:
                fh.write("scoter scoter.cfg")
        
        # copy program if requested
        if include_scoter:
            scoter_dir = os.path.join(path, "scoter")
            os.mkdir(scoter_dir)
            for filename in scoter_files:
                shutil.copy2(self._rel_path(filename), scoter_dir)

        # copy canned readme files
        for source_file, dest_path in files_to_copy:
            source_path = os.path.join(self.parent_dir, "bundle-files", source_file)
            dest_dir = os.path.join(path, *dest_path[:-1])
            # scoter directory may not exist, so we have to check
            if os.path.isdir(dest_dir):
                shutil.copy2(source_path, os.path.join(dest_dir, dest_path[-1]))

        # write GUI configuration
        wxc = wx.FileConfig(appName = "scoter", vendorName = "talvi.net",
                                 localFilename = os.path.join(path, "scotergui.cfg"),
                                 style = wx.CONFIG_USE_LOCAL_FILE)
        self.write_gui_to_wxconfig(wxc)

        # generate results if requested
        if include_results:
            # TODO show progress dialog here
            
            logger.info("Generating results for bundle.")
            scoter = Scoter()
            scoter.perform_complete_correlation(config_path)

    def show_export_bundle_dialog(self, event):
        success = self.make_scoterconfig_from_gui()
        if not success: return
        self.bundle_dialog.Centre()
        if self.bundle_dialog.ShowModal() == wx.ID_CANCEL:
            return
        bundle_type = self.bundle_dialog.choice_bundle_type.GetSelection()
        include_scoter = self.bundle_dialog.check_include_scoter.GetValue()
        include_results = self.bundle_dialog.check_include_results.GetValue()
        if bundle_type == 0: # zip file
            dialog = wx.FileDialog(self.main_frame, "Create bundle as zip file",
                                   "", # default path
                                   "bundle.zip",
                                   "Zip files (*.zip)|*.zip|All files|*",
                                   wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT)
            response = dialog.ShowModal()
            if response == wx.ID_OK:
                bundle_path = tempfile.mkdtemp("", "scoter", None)
                zip_path = dialog.GetPath()
                dialog.Destroy()
        else:
            while True:
                dialog = wx.DirDialog(self.main_frame, "Select or create a bundle folder",
                                  "", # default path
                                  wx.DD_DEFAULT_STYLE,
                                  wx.DefaultPosition,
                                  wx.DefaultSize,
                                  "name" # not used according to wx docs
                                  )
                response = dialog.ShowModal()
                if response != wx.ID_OK: break
                bundle_path = dialog.GetPath()
                dialog.Destroy()
                if os.listdir(bundle_path) == []: # empty dir, OK to procees
                    break
                else: # non-empty directory
                    wx.MessageBox("You cannot put a bundle in a non-empty folder. "
                                  "Please select an empty folder or create a new one.",
                                  "Bundle creation error",
                                  wx.OK | wx.ICON_ERROR)

        if response != wx.ID_OK: return
        self.make_bundle(bundle_path, include_scoter, include_results)
        if bundle_type == 0: # 0 is zip, 1 is folder
            # zip the temporary directory
            self.zipdir(bundle_path, zip_path)
            # remove the temporary directory
            shutil.rmtree(bundle_path, ignore_errors = True)
        
        bundle_name = os.path.basename(zip_path if bundle_type==0 else bundle_path)
        wx.MessageBox(u"The bundle ‘%s’ was created successfully. " %
                      bundle_name,
                      "Bundle created",
                      wx.OK | wx.ICON_INFORMATION)
    
    def show_save_wxconfig_dialog(self, event):
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
        
    def show_read_config_dialog(self, event):
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
            self.read_wxconfig_from_file(filename)
            self.lastdir_config = dirname

        dialog.Destroy()
    
    def read_wxconfig_from_file(self, filename):
        conf = wx.FileConfig(appName = "scoter", vendorName = "talvi.net",
                             localFilename = filename,
                             style = wx.CONFIG_USE_LOCAL_FILE)
        self.update_gui_from_wxconfig(conf)        
    
    def revert_config(self, event):
        """Revert configuration to its state when Scoter was started.
        
        This is done by simply re-reading from the wx configuration API.
        """
        choice = wx.MessageBox("Are you sure you want to revert all settings to "
                               "their previous values? Any changes made during "
                               "this session will be lost.", "Revert configuration", 
                               wx.YES_NO | wx.ICON_WARNING | wx.NO_DEFAULT)
        if choice == wx.YES:
            self.update_gui_from_wxconfig()

    def reset_config(self, event):
        """Reset configuration to default values.
        """
        choice = wx.MessageBox("Are you sure you want to reset all settings to "
                               "their default values?", "Reset configuration",
                               wx.YES_NO | wx.ICON_WARNING | wx.NO_DEFAULT)
        if choice == wx.YES:
            wxc = wx.Config("scoter")
            wxc.DeleteAll()
            self.update_gui_from_wxconfig()
    
    def update_gui_from_wxconfig(self, config = None):
        """Update the GUI from a supplied wx.Config object.
        
        Args:
            config: configuration to use; if None, use the Config object associated
            with the name "scoter". For any values missing from the wx configuration,
            default values from the ScoterConfig class are used.
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
        for wxfield, scoterfield, _, _ in _gui_text_fields:
            widget = getattr(mf, wxfield)
            widget.SetValue(wxc.Read(scoterfield, str(getattr(d, scoterfield))))
        mf.preproc_interp_active.SetValue(wxc.ReadBool("interp_active", d.interp_active))
        interp_npoints_type = wxc.Read("interp_npoints_type", "min")
        mf.preproc_interp_min.SetValue(interp_npoints_type == "min")
        mf.preproc_interp_max.SetValue(interp_npoints_type == "max")
        mf.preproc_interp_explicit.SetValue(interp_npoints_type == "explicit")
        interp_npoints = wxc.ReadInt("interp_npoints", -1)
        if interp_npoints != -1:
            mf.preproc_interp_npoints.SetValue(interp_npoints)
        mf.preproc_interp_type.SetStringSelection(wxc.Read("interp_type", d.interp_type))
        mf.corr_sa_active.SetValue(wxc.ReadBool("sa_active", d.sa_active))
        mf.corr_match_active.SetValue(wxc.ReadBool("match_active", d.match_active))
        mf.corr_match_guessed_path.SetValue(str(self.scoter.default_match_path))
        mf.corr_match_guess_button.SetValue(not wxc.ReadBool("match_use_specified_path", False))
        mf.corr_match_specify_button.SetValue(wxc.ReadBool("match_use_specified_path", False))
        mf.corr_match_specified_path.SetValue(wxc.Read("match_specified_path"))
        self.debug = wxc.Read("Debug", "")

        self.scoter.read_data(1, 0, wxc.Read("target_d18o_file"))
        self.scoter.read_data(0, 0, wxc.Read("record_d18o_file"))
        self.scoter.read_data(1, 1, wxc.Read("target_rpi_file"))
        self.scoter.read_data(0, 1, wxc.Read("record_rpi_file"))
        self.series_truncations[1][0] = wxc.ReadFloat("target_start", d.target_start)
        self.series_truncations[1][1] = wxc.ReadFloat("target_end", d.target_end)
        self.series_truncations[0][0] = wxc.ReadFloat("record_start", d.record_start)
        self.series_truncations[0][1] = wxc.ReadFloat("record_end", d.record_end)
        
        for lastdir in _last_dirs:
            setattr(self, lastdir, wxc.Read(lastdir, ""))
        
        self.plot_series()

    def write_gui_to_wxconfig(self, wxc = None):
        """Write the current state of the GUI to a supplied wx.Config object.
        
        Args:
            config: configuration to use; if None, use wx.Config("scoter").
        """
        mf = self.main_frame
        detrend_opts = ("none", "submean", "linear")
        interp_npoints_type = "min" # default in case (impossibly) no radio button selected
        if mf.preproc_interp_min.GetValue():
            interp_npoints_type = "min"
        elif mf.preproc_interp_max.GetValue():
            interp_npoints_type = "max"
        elif mf.preproc_interp_explicit.GetValue():
            interp_npoints_type = "explicit"
        mf = self.main_frame
        if wxc == None: wxc = wx.Config("scoter")
        for wxfield, scoterfield, _, _ in _gui_text_fields:
            widget = getattr(mf, wxfield)
            wxc.Write(scoterfield, widget.GetValue())
        wxc.Write("detrend", detrend_opts[mf.preproc_detrend.GetSelection()])
        wxc.WriteBool("normalize", mf.preproc_normalize.GetValue())
        wxc.WriteBool("interp_active", mf.preproc_interp_active.GetValue())
        wxc.Write("interp_type", mf.preproc_interp_type.GetStringSelection())
        wxc.Write("interp_npoints_type", interp_npoints_type)
        wxc.WriteInt("interp_npoints", mf.preproc_interp_npoints.GetValue())
        wxc.WriteBool("sa_active", mf.corr_sa_active.GetValue())
        wxc.WriteBool("match_active", mf.corr_match_active.GetValue())
        wxc.Write("match_specified_path", mf.corr_match_specified_path.GetValue())
        wxc.WriteBool("match_use_specified_path", mf.corr_match_specify_button.GetValue())
        wxc.Write("target_d18o_file", self.scoter.filenames[1][0])
        wxc.Write("record_d18o_file", self.scoter.filenames[0][0])
        wxc.Write("target_rpi_file", self.scoter.filenames[1][1])
        wxc.Write("record_rpi_file", self.scoter.filenames[0][1])
        wxc.WriteFloat("target_start", self.series_truncations[1][0])
        wxc.WriteFloat("target_end", self.series_truncations[1][1])
        wxc.WriteFloat("record_start", self.series_truncations[0][0])
        wxc.WriteFloat("record_end", self.series_truncations[0][1])
        wxc.Write("debug", self.debug)
        
        for lastdir in _last_dirs:
            wxc.Write(lastdir, getattr(self, lastdir))

        wxc.Flush()

        logger.debug("Wrote configuration; %d items", wxc.GetNumberOfEntries())
        
    def make_scoterconfig_from_gui(self):
        """Create a ScoterConfig object from the current state of the GUI.
        
        The object is not returned, but is stored as self.scoterconfig.
        
        Returns:
            True if the parameters were successfully read from the GUI;
            False if there was a problem.
        """
        mf = self.main_frame
        detrend_opts = ("none", "submean", "linear")
        interp_type = mf.preproc_interp_type.GetStringSelection()
        interp_npoints = None
        if mf.preproc_interp_min.GetValue():
            interp_npoints = -2
        elif mf.preproc_interp_max.GetValue():
            interp_npoints = -1
        elif mf.preproc_interp_explicit.GetValue():
            interp_npoints = mf.preproc_interp_npoints.GetValue()
        if mf.corr_match_guess_button.GetValue():
            match_path = ""
        else:
            match_path = mf.corr_match_specified_path.GetValue()

        # Create a parameter dictionary containing the "special" parameters
        # which don't fit the _gui_text_fields paradigm.
        pdict = dict(detrend = detrend_opts[mf.preproc_detrend.GetSelection()],
                     normalize = mf.preproc_normalize.GetValue(),
                     interp_type = interp_type,
                     interp_npoints = interp_npoints,
                     sa_active = mf.corr_sa_active.GetValue(),
                     match_active = mf.corr_match_active.GetValue(),
                     match_path = match_path,
                     debug = self.debug)
        
        # Add the "pass-through" parameters, which go directly from a
        # wx text field to a Scoter parameter, possibly via a float or int parse.
        for widget_name, field, type_, desc in _gui_text_fields:
            value_string = getattr(mf, widget_name).GetValue()
            try:
                value = type_(value_string)
                pdict[field] = value
            except ValueError:
                dialog = wx.MessageDialog(self.main_frame,
                                          "‘%s’ is not a valid setting for ‘%s’" %
                                          (value_string, desc),
                                          "Configuration error", 
                                          wx.OK | wx.ICON_ERROR)
                dialog.ShowModal()
                return False
        
        # Empty strings for data series filenames, since they've already been set.
        for role in _roledict:
            for param in _paramdict:
                pdict["%s_%s_file" % (role, param)] = ""
        
        # Set the limit parameters from the values in the series_truncations array.
        for role, rolenum in _roledict.items():
            for limit, limitnum in _limitdict.items():
                pdict["%s_%s" % (role, limit)] = \
                    self.series_truncations[rolenum][limitnum]
        
        self.scoterconfig = ScoterConfig(**pdict)
        return True

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
        self.scotergui.read_wxconfig_from_file(filenames[0])

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

def install_thread_excepthook():
    """
    Workaround for sys.excepthook thread bug http://bugs.python.org/issue1230540
    by Jonathan Ellis.
    Call once from __main__ before creating any threads.
    If using psyco, call psycho.cannotcompile(threading.Thread.run)
    since this replaces a new-style class method.
    """
    import sys
    run_old = threading.Thread.run
    def run(*args, **kwargs):
        try:
            run_old(*args, **kwargs)
        except (KeyboardInterrupt, SystemExit):
            raise
        except:
            sys.excepthook(*sys.exc_info())
    threading.Thread.run = run

def main():
    logging.basicConfig(level=logging.DEBUG)
    
    app = ScoterApp()
    app.MainLoop()

logger = logging.getLogger(__name__)
if __name__ == "__main__":
    main()
