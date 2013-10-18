#!/usr/bin/env python
# -*- coding: utf-8 -*-

import wx
import wx.xrc
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas
from matplotlib.figure import Figure
from numpy import arange, sin, pi
from scoter import Scoter
import os.path


def find_xrc_ctrl(parent, pathspec):
    current = parent
    path = pathspec.split(" ")
    for elt in path:
        current = wx.xrc.XRCCTRL(current, elt)
    return current

class ScoterApp(wx.App):
    
    def OnInit(self):
        
        self.scoter = Scoter()
        
        res = wx.xrc.XmlResource('forms.xrc')
        self.main_frame = res.LoadFrame(None, "MainFrame")
        self.axes = []
        self.figure_canvas = []
        for panel in (0,1):
            for subpanel in (0,1):
                self.add_figure(panel, subpanel)

        self.main_frame.Bind(wx.EVT_BUTTON, self.read_record, id=wx.xrc.XRCID("button_read_d18o_record"))
        self.main_frame.Bind(wx.EVT_BUTTON, self.read_record, id=wx.xrc.XRCID("button_read_d18o_target"))
        self.main_frame.Bind(wx.EVT_BUTTON, self.read_record, id=wx.xrc.XRCID("button_read_rpi_record"))
        self.main_frame.Bind(wx.EVT_BUTTON, self.read_record, id=wx.xrc.XRCID("button_read_rpi_target"))
        notebook = find_xrc_ctrl(self.main_frame, "Notebook")
        notebook.SetSelection(0)
        self.main_frame.Center()
        self.main_frame.Show()
        
        return True
    
    def add_figure(self, panel, subpanel):
        locator = "Notebook DataPanel%d DataPanel%d%d" % (panel, panel, subpanel)
        panel = find_xrc_ctrl(self.main_frame, locator)
        figure = Figure()
        figure.set_size_inches(1, 1) # the FigureCanvas uses this as a minimum size
        self.axes.append(figure.add_subplot(111))
        figure_canvas = FigureCanvas(panel, -1, figure)
        self.figure_canvas.append(figure_canvas)
        sizer = panel.GetSizer()
        sizer.Add(figure_canvas, 1, wx.EXPAND | wx.ALL)         

    def plot_series(self):
        for dataset in (0,1):
            for rtype in (0,1):
                index = 2 * rtype + dataset
                axes = self.axes[index]
                axes.clear()
                axes.set_xlabel("time")
                axes.set_ylabel("$\delta^{18}\mathrm{O}$")
                series = self.scoter.series[dataset][rtype]
                if series is not None:
                    xs = series.data[0]
                    ys = series.data[1]
                    axes.plot(xs, ys)
                self.figure_canvas[index].draw()
        
    def read_record(self, event):
        button_name = event.GetEventObject().GetName()
        index = 0 if "record" in button_name else 1
        record_type = 0 if "d18o" in button_name else 1
        assert(0 <= index <= 1)
        assert(0 <= record_type <= 1)
        dialog = wx.FileDialog(self.main_frame, "Choose a file", "~", "", "*.*", wx.OPEN)
        if dialog.ShowModal() == wx.ID_OK:
            leafname = dialog.GetFilename()
            dirname = dialog.GetDirectory()
            filename = os.path.join(dirname, leafname)
            dialog.Destroy()
            self.scoter.read_data(index, record_type, filename)
            self.plot_series()

class MainFrame(wx.Frame):

    def __init__(self, *args, **kwargs):
        super(MainFrame, self).__init__(*args, **kwargs)
        
        self.parent_dir = os.path.dirname(os.path.realpath(__file__))
        self.scoter = Scoter()
        
        self.make_gui()

    def rel_path(self, filename):
        return os.path.join(self.parent_dir, filename)

    def make_gui(self):

        # Create icon
        favicon = wx.Icon(self.rel_path('placeholder.png'), wx.BITMAP_TYPE_PNG, 16, 16)
        self.SetIcon(favicon)
        
        # Create menus
        menu_bar = wx.MenuBar()
        file_menu = wx.Menu()
        file_quit = file_menu.Append(wx.ID_EXIT, "Quit", "Quit Scoter")
        menu_bar.Append(file_menu, "&File")
        self.SetMenuBar(menu_bar)
        self.Bind(wx.EVT_MENU, self.quit, file_quit)

        # Create vertical box
        vbox = wx.BoxSizer(wx.VERTICAL)

        # Create toolbar
        toolbar = wx.ToolBar(self, id=-1, pos=wx.DefaultPosition,
                             size=wx.DefaultSize, style = wx.TB_TEXT)
        bitmap = wx.ArtProvider.GetBitmap(wx.ART_FILE_OPEN)
        self.tool_read_record_a = toolbar.AddLabelTool(wx.ID_ANY, "Read record", bitmap)
        self.tool_read_record_b = toolbar.AddLabelTool(wx.ID_ANY, "Read target", bitmap)
        toolbar.AddLabelTool(wx.ID_ANY, "Preprocess data", bitmap)
        toolbar.AddLabelTool(wx.ID_ANY, "Tune records", bitmap)
        toolbar.Realize()
        self.Bind(wx.EVT_TOOL, self.read_record_a, self.tool_read_record_a)
        self.Bind(wx.EVT_TOOL, self.read_record_b, self.tool_read_record_b)
        vbox.Add(toolbar, 0, wx.EXPAND)

        # Create figure and canvas
        self.figure = Figure()
        self.axes = []
        self.axes.append(self.figure.add_subplot(211))
        self.axes.append(self.figure.add_subplot(212))
        
        self.figure_canvas = FigureCanvas(self, -1, self.figure)
        vbox.Add(self.figure_canvas, 1, wx.GROW)

        # Size and show frame
        self.CreateStatusBar()
        self.SetSizer(vbox)
        self.SetSize((800, 600))
        self.Fit()
        self.SetTitle("Scoter")
        self.Centre()
        self.Show(True)
    
    def plot_series(self):
        for dataset in (0,1):
            axes = self.axes[dataset]
            axes.clear()
            axes.set_xlabel("time")
            axes.set_ylabel("$\delta^{18}\mathrm{O}$")
            for rtype in (0,1):
                series = self.scoter.series[dataset][rtype]
                if series is not None:
                    xs = series.data[0]
                    ys = series.data[1]
                    axes.plot(xs, ys)
        self.figure_canvas.draw()

    def read_record(self, index):
        assert(0 <= index <= 1)
        dialog = wx.FileDialog(self, "Choose a file", "~", "", "*.*", wx.OPEN)
        if dialog.ShowModal() == wx.ID_OK:
            leafname = dialog.GetFilename()
            dirname = dialog.GetDirectory()
            filename = os.path.join(dirname, leafname)
            dialog.Destroy()
            rtype_dialog = RecordTypeDialog(None, title = "rtype_dialog")
            rtype_dialog.ShowModal()
            record_type = rtype_dialog.selected_id
            rtype_dialog.Destroy()
            self.scoter.read_data(index, record_type, filename)
            self.plot_series()

    def read_record_a(self, event):
        self.read_record(0)

    def read_record_b(self, event):
        self.read_record(1)

    def quit(self, e):
        self.Close()

class RecordTypeDialog(wx.Dialog):
    
    ID_D18O_BUTTON = wx.NewId()
    ID_RPI_BUTTON = wx.NewId()
    
    def __init__(self, *args, **kw):
        super(RecordTypeDialog, self).__init__(*args, **kw) 
        self.selected_id = 0
        self.make_gui()
        self.SetSize((200, 200))
        self.SetTitle("Select record type")
    
    def make_gui(self):
        box_sizer = wx.BoxSizer(wx.VERTICAL)
        d18o_button = wx.Button(self, id = RecordTypeDialog.ID_D18O_BUTTON, label = u"δ18O")
        rpi_button = wx.Button(self, id = RecordTypeDialog.ID_RPI_BUTTON, label = "RPI")
        box_sizer.Add(d18o_button, proportion=1, 
            flag=wx.ALL|wx.EXPAND, border=5)
        box_sizer.Add(rpi_button, proportion=1,
            flag=wx.ALL|wx.EXPAND, border=5)
        
        self.SetSizer(box_sizer)
        
        d18o_button.Bind(wx.EVT_BUTTON, self.close) #, id = RecordTypeDialog.ID_D18O_BUTTON)
        rpi_button.Bind(wx.EVT_BUTTON, self.close) #, id = RecordTypeDialog.ID_RPI_BUTTON)

    def close(self, e):
        if e.GetId() == RecordTypeDialog.ID_D18O_BUTTON:
            self.selected_id = 0
        elif e.GetId() == RecordTypeDialog.ID_RPI_BUTTON:
            self.selected_id = 1
        print self.selected_id
        self.Close()
        self.Destroy()

def main():
    app = ScoterApp()
    app.MainLoop()
    #MainFrame(None)

if __name__ == "__main__":
    main()
