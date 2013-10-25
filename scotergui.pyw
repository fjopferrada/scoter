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
        self.SetVendorName("talvi.net") # may as well adopt the Java convention
        self.SetAppName("Scoter")
        
        self.main_frame = forms.MainFrame(None)
        icon = wx.Icon("placeholder.png", wx.BITMAP_TYPE_PNG, 16, 16)
        self.main_frame.SetIcon(icon)
        
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

        self.main_frame.Bind(wx.EVT_BUTTON, self.read_record, self.main_frame.button_read_d18o_record)
        self.main_frame.Bind(wx.EVT_BUTTON, self.read_record, self.main_frame.button_read_d18o_target)
        self.main_frame.Bind(wx.EVT_BUTTON, self.read_record, self.main_frame.button_read_rpi_record)
        self.main_frame.Bind(wx.EVT_BUTTON, self.read_record, self.main_frame.button_read_rpi_target)
        self.main_frame.Bind(wx.EVT_BUTTON, self.clear_record, self.main_frame.button_clear_d18o_record)
        self.main_frame.Bind(wx.EVT_BUTTON, self.clear_record, self.main_frame.button_clear_d18o_target)
        self.main_frame.Bind(wx.EVT_BUTTON, self.clear_record, self.main_frame.button_clear_rpi_record)
        self.main_frame.Bind(wx.EVT_BUTTON, self.clear_record, self.main_frame.button_clear_rpi_target)        
        self.main_frame.Bind(wx.EVT_BUTTON, self.tune, self.main_frame.button_tune)
        
        notebook = self.main_frame.Notebook
        notebook.SetSelection(0)
        self.main_frame.Center()
        self.main_frame.Show()
        
        # Ugly hack to force Windows to draw graphs at correct size.
        width, height = self.main_frame.GetSize()
        self.main_frame.SetSize((width+1,height))
        self.main_frame.SetSize((width-1,height))
        
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
        class params(object):
            live_display = False
            precalc = False
            make_pdf = False
            nblocks = 64
            max_rate = 4
        self.scoter.solve_sa(None, params)
        xs = self.scoter.dewarped.data[0]
        ys = self.scoter.dewarped.data[1]
        self.result_axes.clear()
        self.result_axes.plot(xs, ys)

def main():
    app = ScoterApp()
    app.MainLoop()

if __name__ == "__main__":
    main()
