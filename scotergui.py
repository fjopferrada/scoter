#!/usr/bin/env python
# -*- coding: utf-8 -*-

import wx.xrc
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas
from matplotlib.figure import Figure
from scoter import Scoter
import os.path
import forms

class ScoterApp(wx.App):
    
    def OnInit(self):
        
        self.scoter = Scoter()
        
        #res = wx.xrc.XmlResource('forms.xrc')
        #self.main_frame = res.LoadFrame(None, "MainFrame")
        self.main_frame = forms.MainFrame(None)
        self.axes = []
        self.figure_canvas = []
        for panel in (0,1):
            for subpanel in (0,1):
                self.add_figure(panel, subpanel)

        self.main_frame.Bind(wx.EVT_BUTTON, self.read_record, self.main_frame.button_read_d18o_record)
        self.main_frame.Bind(wx.EVT_BUTTON, self.read_record, self.main_frame.button_read_d18o_target)
        self.main_frame.Bind(wx.EVT_BUTTON, self.read_record, self.main_frame.button_read_rpi_record)
        self.main_frame.Bind(wx.EVT_BUTTON, self.read_record, self.main_frame.button_read_rpi_target)
        
        notebook = self.main_frame.Notebook
        notebook.SetSelection(0)
        self.main_frame.Center()
        self.main_frame.Show()
        
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

def main():
    app = ScoterApp()
    app.MainLoop()

if __name__ == "__main__":
    main()
