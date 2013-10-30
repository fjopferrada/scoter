#!/usr/bin/env python
# -*- coding: utf-8 -*-

import wx
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas
from matplotlib.figure import Figure
from scoter import Scoter
import os.path
import forms

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

        panel_obj = self.main_frame.DataPanel_Results
        figure = Figure()
        figure.set_size_inches(1, 1) # the FigureCanvas uses this as a minimum size
        self.result_axes = figure.add_axes([0.05, 0.2, 0.93, 0.7])
        figure_canvas = FigureCanvas(panel_obj, -1, figure)
        sizer = panel_obj.GetSizer()
        sizer.Add(figure_canvas, 1, wx.EXPAND | wx.ALL)

        bind = self.main_frame.Bind
        bind(wx.EVT_BUTTON, self.read_record, self.main_frame.button_read_d18o_record)
        bind(wx.EVT_BUTTON, self.read_record, self.main_frame.button_read_d18o_target)
        bind(wx.EVT_BUTTON, self.read_record, self.main_frame.button_read_rpi_record)
        bind(wx.EVT_BUTTON, self.read_record, self.main_frame.button_read_rpi_target)
        bind(wx.EVT_BUTTON, self.clear_record, self.main_frame.button_clear_d18o_record)
        bind(wx.EVT_BUTTON, self.clear_record, self.main_frame.button_clear_d18o_target)
        bind(wx.EVT_BUTTON, self.clear_record, self.main_frame.button_clear_rpi_record)
        bind(wx.EVT_BUTTON, self.clear_record, self.main_frame.button_clear_rpi_target)        
        bind(wx.EVT_BUTTON, self.tune, self.main_frame.button_tune)
        bind(wx.EVT_MENU, self.quit, self.main_frame.menuitem_quit)
        bind(wx.EVT_MENU, self.about, self.main_frame.menuitem_about)
        
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
        self.axes.append(axes)
        figure_canvas = FigureCanvas(panel_obj, -1, figure)
        self.figure_canvas.append(figure_canvas)
        sizer = panel_obj.GetSizer()
        sizer.Add(figure_canvas, 1, wx.EXPAND | wx.ALL)

    def plot_results(self):
        axes = self.result_axes
        axes.clear()
        for record_type in (0,):
            target = self.scoter.series[1][record_type] # only interested in the target
            axes.plot(target.data[0], target.data[1])
            tuned = self.scoter.dewarped
            axes.plot(tuned.data[0], tuned.data[1])

    def plot_series(self):
        for dataset in (0,1):
            for rtype in (0,1):
                index = 2 * rtype + dataset
                axes = self.axes[index]
                axes.clear()
                series = self.scoter.series[dataset][rtype]
                if series is not None:
                    xs = series.data[0]
                    ys = series.data[1]
                    axes.plot(xs, ys)
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
    
    def tune(self, event):
        params = self.read_params_from_gui()
        params.live_display = False
        params.precalc = False
        params.make_pdf = False
        params.nblocks = 64
        params.max_rate = 4
        self.scoter.solve_sa(None, params)
        self.plot_results()
        self.main_frame.Notebook.SetSelection(4)
        
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
        self.SetDescription("A program for time-calibration of geological records.")
        self.SetCopyright("(C) Pontus Lurcock 2013")
        # Don't use SetLicence since it disables native about boxes on Windows & Mac --
        # see docs for details.
        self.SetDevelopers(("Pontus Lurcock",))

def main():
    app = ScoterApp()
    app.MainLoop()

if __name__ == "__main__":
    main()
