#!/usr/bin/env python
# -*- coding: utf-8 -*-

import wx
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas
from matplotlib.figure import Figure
from scoter import Scoter
import os.path
import forms
import threading

class ScoterApp(wx.App):
    
    def OnInit(self):
        
        self.scoter = Scoter()
        self.scoter.read_test_data()
        self.SetVendorName("talvi.net") # may as well adopt the Java convention
        self.SetAppName("Scoter")

        self.main_frame = forms.MainFrame(None)

        icon_bundle = wx.IconBundle()
        icon_bundle.AddIcon(wx.Icon("appicon16.png", wx.BITMAP_TYPE_PNG))
        icon_bundle.AddIcon(wx.Icon("appicon32.png", wx.BITMAP_TYPE_PNG))
        icon_bundle.AddIcon(wx.Icon("appicon64.png", wx.BITMAP_TYPE_PNG))
        self.main_frame.SetIcons(icon_bundle) 
        
        self.axes = []
        self.figure_canvas = []
        for panel in (0,1):
            for subpanel in (0,1):
                self.add_figure(panel, subpanel)

        results_figure = Figure()
        results_figure.set_size_inches(1, 1) # the FigureCanvas uses this as a minimum size
        self.result_axes = []
        self.result_axes.append(results_figure.add_subplot(211))
        self.result_axes[-1].invert_yaxis()
        self.result_axes.append(results_figure.add_subplot(212))
        self.results_canvas = FigureCanvas(self.main_frame.panel_resultsplot, -1, results_figure)
        self.main_frame.panel_resultsplot.GetSizer().Add(self.results_canvas, 1, wx.EXPAND | wx.ALL)
        
        progress_figure = Figure()
        progress_figure.set_size_inches(1, 1)
        self.progress_axes = progress_figure.add_axes([0.05, 0.2, 0.93, 0.7])
        self.progress_canvas = FigureCanvas(self.main_frame.panel_progressplot, -1, progress_figure)
        self.main_frame.panel_progressplot.GetSizer().Add(self.progress_canvas, 1, wx.EXPAND | wx.ALL)
        

        bind = self.main_frame.Bind
        bind(wx.EVT_BUTTON, self.read_record, self.main_frame.button_read_d18o_record)
        bind(wx.EVT_BUTTON, self.read_record, self.main_frame.button_read_d18o_target)
        bind(wx.EVT_BUTTON, self.read_record, self.main_frame.button_read_rpi_record)
        bind(wx.EVT_BUTTON, self.read_record, self.main_frame.button_read_rpi_target)
        bind(wx.EVT_BUTTON, self.clear_record, self.main_frame.button_clear_d18o_record)
        bind(wx.EVT_BUTTON, self.clear_record, self.main_frame.button_clear_d18o_target)
        bind(wx.EVT_BUTTON, self.clear_record, self.main_frame.button_clear_rpi_record)
        bind(wx.EVT_BUTTON, self.clear_record, self.main_frame.button_clear_rpi_target)        
        bind(wx.EVT_BUTTON, self.correlate, self.main_frame.button_correlate)
        bind(wx.EVT_MENU, self.quit, self.main_frame.menuitem_quit)
        bind(wx.EVT_MENU, self.about, self.main_frame.menuitem_about)
        bind(wx.EVT_BUTTON, self.abort, self.main_frame.button_abort)
        
        notebook = self.main_frame.Notebook
        notebook.SetSelection(0)
        self.main_frame.Center()
        self.main_frame.Show()
        
        # Ugly hack to force Windows to draw graphs at correct size.
        width, height = self.main_frame.GetSize()
        self.main_frame.SetSize((width+1,height))
        self.main_frame.SetSize((width-1,height))
        
        self.about_frame = AboutScoter()
        self.plot_series()
        return True
    
    def add_figure(self, page, panel):
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
        sizer.Add(figure_canvas, 1, wx.EXPAND | wx.ALL)

    def plot_results(self):
        for record_type in (0, 1):
            axes = self.result_axes[record_type]
            axes.clear()
            #axes.set_ylim([0, 1]) # ensures axes are right way up before we invert them!
            target = self.scoter.series[1][record_type] # only interested in the target
            target = self.scoter.bwarp_annealed.series[1].series[record_type]
            if target != None and self.scoter.series[0][record_type] != None:
                axes.plot(target.data[0], target.data[1])
                tuned = self.scoter.dewarped[record_type]
                axes.plot(tuned.data[0], tuned.data[1])
                axes.autoscale()
                #if record_type == 0: axes.invert_yaxis()
        self.results_canvas.draw()

    def plot_series(self):
        for dataset in (0,1):
            for record_type in (0,1):
                index = 2 * record_type + dataset
                axes = self.axes[index]
                axes.clear()
                series = self.scoter.series[dataset][record_type]
                if series is not None:
                    xs = series.data[0]
                    ys = series.data[1]
                    axes.plot(xs, ys)
                    #if record_type == 0:
                        #axes.invert_yaxis()
                        # d18O records are conventionally plotted decreasing-up
                self.figure_canvas[index].draw()
    
    def clear_record(self, event):
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
    
    def read_record(self, event):
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
        dialog = wx.FileDialog(self.main_frame, "Choose a file", "", "", "*.*", wx.OPEN)
        if dialog.ShowModal() == wx.ID_OK:
            leafname = dialog.GetFilename()
            dirname = dialog.GetDirectory()
            filename = os.path.join(dirname, leafname)
            dialog.Destroy()
            self.scoter.read_data(index, record_type, filename)
            self.plot_series()
    
    def correlate(self, event):
        params = self.read_params_from_gui()
        params.live_display = False
        params.precalc = False
        params.make_pdf = False
        params.nblocks = 64
        params.max_rate = 4

        # self.scoter.solve_sa(None, params, self)
        # self.plot_results()
        self.progress_axes.clear()
        self.progress_percentage = 0
        self.progress_lines = []
        for _ in 0, 1:
            xs = range(params.nblocks)
            ys = range(params.nblocks)
            self.progress_lines.append(self.progress_axes.plot(xs, ys)[0])

        self.simann_abort_flag = False
        thread = threading.Thread(target = self.scoter.solve_sa,
                                  args = (None, params, self))
        thread.start()

        self.soln_current = None
        self.soln_new = None
        self.timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self._redraw_plot, self.timer)
        self.timer.Start(100, oneShot = wx.TIMER_ONE_SHOT)

        self.main_frame.text_progress.SetLabel("Simulated annealing in progress…")
        self.main_frame.Notebook.SetSelection(4)
    
    def abort(self, event):
        self.simann_abort_flag = True
    
    def _redraw_plot(self, event):
        scale = 1.
        if self.soln_current == None: return
        soln_current, soln_new = self.soln_current, self.soln_new
        for i, soln in ((0, soln_current), (1, soln_new)):
            xs, ys = soln.get_coords()
            self.progress_lines[i].set_xdata([x * scale for x in xs])
            self.progress_lines[i].set_ydata([y * scale for y in ys])
        #wx.CallAfter(self.progress_canvas.draw)
        self.progress_canvas.draw()
        #wx.WakeUpIdle()
        self.timer.Start(10, oneShot = wx.TIMER_ONE_SHOT)
            
    def simann_callback_update(self, soln_current, soln_new, percentage):
        percentage_int = int(percentage)
        # We avoid excessive GUI updates by rounding to the nearest whole percentage,
        # caching the value, and only updating the bar when it changes.
        if percentage_int == self.progress_percentage: return
        self.progress_percentage = percentage_int
        wx.CallAfter(self.main_frame.simann_progress_gauge.SetValue, percentage_int)
        self.soln_current = soln_current
        self.soln_new = soln_new
        #wx.EVT_IDLE(self._redraw_plot, soln_current, soln_new)
        
    def simann_callback_finished(self, status):
        self.timer.Stop()
        if status == "completed":
            wx.CallAfter(self.main_frame.text_progress.SetLabel, "Correlation complete.")
            wx.CallAfter(self.plot_results)
            wx.CallAfter(self.main_frame.Notebook.SetSelection, 5)
            wx.CallAfter(self.main_frame.simann_progress_gauge.SetValue, 0)
        elif status == "aborted":
            wx.CallAfter(self.main_frame.text_progress.SetLabel, "Correlation aborted.")
        else:
            wx.CallAfter(self.main_frame.text_progress.SetLabel,
                         "Correlation finished with unrecognized status: "+status)
    
    def simann_check_abort(self):
        return self.simann_abort_flag
        
    def quit(self, event):
        self.Destroy()
        wx.Exit()
    
    def about(self, event):
        wx.AboutBox(self.about_frame)
    
    def read_params_from_gui(self):
        class Params(object):
            pass
        p = Params()
        
        mf = self.main_frame
        detrend_opts = ("none", "submean", "linear")
        p.detrend = detrend_opts[mf.preproc_detrend.GetSelection()]
        p.normalize = mf.preproc_normalize.GetValue()
        if mf.preproc_interp_min.GetValue():
            p.interp_type = "min"
        elif mf.preproc_interp_max.GetValue():
            p.interp_type = "max"
        elif mf.preproc_interp_explicit.GetValue():
            p.interp_type = "explicit"
            p.interp_npoints = mf.preproc_interp_npoints.GetValue()
        else:
            p.interp_type = "none"

        return p

class AboutScoter(wx.AboutDialogInfo):
    
    def __init__(self):
        super(AboutScoter, self).__init__()
        self.SetName("Scoter")
        self.SetIcon(wx.Icon("appicon64.png", wx.BITMAP_TYPE_PNG))
        self.SetVersion("0.00")
        self.SetWebSite("https://bitbucket.org/pont/scoter")
        self.SetDescription("A program for the correlation of geological records.")
        self.SetCopyright("(C) Pontus Lurcock 2013")
        # Don't use SetLicence since it disables native about boxes on Windows & Mac --
        # see docs for details.
        self.SetDevelopers(("Pontus Lurcock",))

def main():
    app = ScoterApp()
    app.MainLoop()

if __name__ == "__main__":
    main()
