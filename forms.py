# -*- coding: utf-8 -*- 

###########################################################################
## Python code generated with wxFormBuilder (version Apr 30 2013)
## http://www.wxformbuilder.org/
##
## PLEASE DO "NOT" EDIT THIS FILE!
###########################################################################

import wx
import wx.xrc

###########################################################################
## Class MainFrame
###########################################################################

class MainFrame ( wx.Frame ):
	
	def __init__( self, parent ):
		wx.Frame.__init__ ( self, parent, id = wx.ID_ANY, title = u"Scoter", pos = wx.DefaultPosition, size = wx.Size( 981,643 ), style = wx.DEFAULT_FRAME_STYLE|wx.TAB_TRAVERSAL )
		
		self.SetSizeHintsSz( wx.DefaultSize, wx.DefaultSize )
		
		bSizer1 = wx.BoxSizer( wx.VERTICAL )
		
		self.Notebook = wx.Notebook( self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, 0 )
		self.DataPanel0 = wx.Panel( self.Notebook, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL )
		bSizer2 = wx.BoxSizer( wx.VERTICAL )
		
		self.ControlPanel00 = wx.Panel( self.DataPanel0, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL )
		bSizer7 = wx.BoxSizer( wx.HORIZONTAL )
		
		self.button_read_d18o_record = wx.Button( self.ControlPanel00, wx.ID_ANY, u"Read δ18O record", wx.DefaultPosition, wx.DefaultSize, 0 )
		bSizer7.Add( self.button_read_d18o_record, 0, wx.ALL, 5 )
		
		self.button_clear_d18o_record = wx.Button( self.ControlPanel00, wx.ID_ANY, u"Clear δ18O record", wx.DefaultPosition, wx.DefaultSize, 0 )
		bSizer7.Add( self.button_clear_d18o_record, 0, wx.ALL, 5 )
		
		
		self.ControlPanel00.SetSizer( bSizer7 )
		self.ControlPanel00.Layout()
		bSizer7.Fit( self.ControlPanel00 )
		bSizer2.Add( self.ControlPanel00, 0, wx.ALL, 5 )
		
		self.DataPanel00 = wx.Panel( self.DataPanel0, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL )
		self.DataPanel00.SetBackgroundColour( wx.SystemSettings.GetColour( wx.SYS_COLOUR_WINDOW ) )
		
		bSizer5 = wx.BoxSizer( wx.VERTICAL )
		
		
		self.DataPanel00.SetSizer( bSizer5 )
		self.DataPanel00.Layout()
		bSizer5.Fit( self.DataPanel00 )
		bSizer2.Add( self.DataPanel00, 1, wx.EXPAND |wx.ALL, 5 )
		
		self.m_panel27 = wx.Panel( self.DataPanel0, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL )
		bSizer20 = wx.BoxSizer( wx.HORIZONTAL )
		
		self.button_read_d18o_target = wx.Button( self.m_panel27, wx.ID_ANY, u"Read δ18O target", wx.DefaultPosition, wx.DefaultSize, 0 )
		bSizer20.Add( self.button_read_d18o_target, 0, wx.ALL, 5 )
		
		self.button_clear_d18o_target = wx.Button( self.m_panel27, wx.ID_ANY, u"Clear δ18O target", wx.DefaultPosition, wx.DefaultSize, 0 )
		bSizer20.Add( self.button_clear_d18o_target, 0, wx.ALL, 5 )
		
		
		self.m_panel27.SetSizer( bSizer20 )
		self.m_panel27.Layout()
		bSizer20.Fit( self.m_panel27 )
		bSizer2.Add( self.m_panel27, 0, wx.EXPAND |wx.ALL, 5 )
		
		self.DataPanel01 = wx.Panel( self.DataPanel0, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL )
		self.DataPanel01.SetBackgroundColour( wx.SystemSettings.GetColour( wx.SYS_COLOUR_WINDOW ) )
		
		bSizer6 = wx.BoxSizer( wx.VERTICAL )
		
		
		self.DataPanel01.SetSizer( bSizer6 )
		self.DataPanel01.Layout()
		bSizer6.Fit( self.DataPanel01 )
		bSizer2.Add( self.DataPanel01, 1, wx.EXPAND |wx.ALL, 5 )
		
		
		self.DataPanel0.SetSizer( bSizer2 )
		self.DataPanel0.Layout()
		bSizer2.Fit( self.DataPanel0 )
		self.Notebook.AddPage( self.DataPanel0, u"δ18O data", False )
		self.DataPanel1 = wx.Panel( self.Notebook, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL )
		bSizer21 = wx.BoxSizer( wx.VERTICAL )
		
		self.ControlPanel001 = wx.Panel( self.DataPanel1, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL )
		bSizer71 = wx.BoxSizer( wx.HORIZONTAL )
		
		self.button_read_rpi_record = wx.Button( self.ControlPanel001, wx.ID_ANY, u"Read RPI record", wx.DefaultPosition, wx.DefaultSize, 0 )
		bSizer71.Add( self.button_read_rpi_record, 0, wx.ALL, 5 )
		
		self.button_clear_rpi_record = wx.Button( self.ControlPanel001, wx.ID_ANY, u"Clear RPI record", wx.DefaultPosition, wx.DefaultSize, 0 )
		bSizer71.Add( self.button_clear_rpi_record, 0, wx.ALL, 5 )
		
		
		self.ControlPanel001.SetSizer( bSizer71 )
		self.ControlPanel001.Layout()
		bSizer71.Fit( self.ControlPanel001 )
		bSizer21.Add( self.ControlPanel001, 0, wx.ALL, 5 )
		
		self.DataPanel10 = wx.Panel( self.DataPanel1, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL )
		self.DataPanel10.SetBackgroundColour( wx.SystemSettings.GetColour( wx.SYS_COLOUR_WINDOW ) )
		
		bSizer51 = wx.BoxSizer( wx.VERTICAL )
		
		
		self.DataPanel10.SetSizer( bSizer51 )
		self.DataPanel10.Layout()
		bSizer51.Fit( self.DataPanel10 )
		bSizer21.Add( self.DataPanel10, 1, wx.EXPAND |wx.ALL, 5 )
		
		self.m_panel271 = wx.Panel( self.DataPanel1, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL )
		bSizer201 = wx.BoxSizer( wx.HORIZONTAL )
		
		self.button_read_rpi_target = wx.Button( self.m_panel271, wx.ID_ANY, u"Read RPI target", wx.DefaultPosition, wx.DefaultSize, 0 )
		bSizer201.Add( self.button_read_rpi_target, 0, wx.ALL, 5 )
		
		self.button_clear_rpi_target = wx.Button( self.m_panel271, wx.ID_ANY, u"Clear RPI target", wx.DefaultPosition, wx.DefaultSize, 0 )
		bSizer201.Add( self.button_clear_rpi_target, 0, wx.ALL, 5 )
		
		
		self.m_panel271.SetSizer( bSizer201 )
		self.m_panel271.Layout()
		bSizer201.Fit( self.m_panel271 )
		bSizer21.Add( self.m_panel271, 0, wx.EXPAND |wx.ALL, 5 )
		
		self.DataPanel11 = wx.Panel( self.DataPanel1, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL )
		self.DataPanel11.SetBackgroundColour( wx.SystemSettings.GetColour( wx.SYS_COLOUR_WINDOW ) )
		
		bSizer61 = wx.BoxSizer( wx.VERTICAL )
		
		
		self.DataPanel11.SetSizer( bSizer61 )
		self.DataPanel11.Layout()
		bSizer61.Fit( self.DataPanel11 )
		bSizer21.Add( self.DataPanel11, 1, wx.EXPAND |wx.ALL, 5 )
		
		
		self.DataPanel1.SetSizer( bSizer21 )
		self.DataPanel1.Layout()
		bSizer21.Fit( self.DataPanel1 )
		self.Notebook.AddPage( self.DataPanel1, u"RPI data", False )
		self.PreprocessingPanel = wx.Panel( self.Notebook, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL )
		fgSizer1 = wx.FlexGridSizer( 2, 2, 0, 0 )
		fgSizer1.AddGrowableCol( 1 )
		fgSizer1.SetFlexibleDirection( wx.BOTH )
		fgSizer1.SetNonFlexibleGrowMode( wx.FLEX_GROWMODE_SPECIFIED )
		
		self.m_staticText3 = wx.StaticText( self.PreprocessingPanel, wx.ID_ANY, u"Detrending", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText3.Wrap( -1 )
		fgSizer1.Add( self.m_staticText3, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT|wx.ALL, 5 )
		
		preproc_detrendChoices = [ u"None", u"Subtract mean", u"Linear detrend" ]
		self.preproc_detrend = wx.Choice( self.PreprocessingPanel, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, preproc_detrendChoices, 0 )
		self.preproc_detrend.SetSelection( 0 )
		fgSizer1.Add( self.preproc_detrend, 0, wx.ALL, 5 )
		
		self.m_staticText6 = wx.StaticText( self.PreprocessingPanel, wx.ID_ANY, u"Normalization", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText6.Wrap( -1 )
		fgSizer1.Add( self.m_staticText6, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT|wx.ALL, 5 )
		
		self.preproc_normalize = wx.CheckBox( self.PreprocessingPanel, wx.ID_ANY, u"Normalize", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.preproc_normalize.SetValue(True) 
		fgSizer1.Add( self.preproc_normalize, 0, wx.ALL, 5 )
		
		self.m_staticText7 = wx.StaticText( self.PreprocessingPanel, wx.ID_ANY, u"Deepest depth", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText7.Wrap( -1 )
		fgSizer1.Add( self.m_staticText7, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT|wx.ALL, 5 )
		
		self.preproc_deepest = wx.SpinCtrl( self.PreprocessingPanel, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, wx.SP_ARROW_KEYS, 0, 10, 0 )
		fgSizer1.Add( self.preproc_deepest, 0, wx.ALL, 5 )
		
		self.m_staticText71 = wx.StaticText( self.PreprocessingPanel, wx.ID_ANY, u"Shallowest depth", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText71.Wrap( -1 )
		fgSizer1.Add( self.m_staticText71, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT|wx.ALL, 5 )
		
		self.preproc_shallowest = wx.SpinCtrl( self.PreprocessingPanel, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, wx.SP_ARROW_KEYS, 0, 10, 0 )
		fgSizer1.Add( self.preproc_shallowest, 0, wx.ALL, 5 )
		
		self.m_staticText711 = wx.StaticText( self.PreprocessingPanel, wx.ID_ANY, u"Oldest time", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText711.Wrap( -1 )
		fgSizer1.Add( self.m_staticText711, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT|wx.ALL, 5 )
		
		self.preproc_oldest = wx.SpinCtrl( self.PreprocessingPanel, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, wx.SP_ARROW_KEYS, 0, 10, 0 )
		fgSizer1.Add( self.preproc_oldest, 0, wx.ALL, 5 )
		
		self.m_staticText712 = wx.StaticText( self.PreprocessingPanel, wx.ID_ANY, u"Youngest time", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText712.Wrap( -1 )
		fgSizer1.Add( self.m_staticText712, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT|wx.ALL, 5 )
		
		self.preproc_youngest = wx.SpinCtrl( self.PreprocessingPanel, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, wx.SP_ARROW_KEYS, 0, 10, 0 )
		fgSizer1.Add( self.preproc_youngest, 0, wx.ALL, 5 )
		
		self.m_staticText7121 = wx.StaticText( self.PreprocessingPanel, wx.ID_ANY, u"Interpolation", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText7121.Wrap( -1 )
		fgSizer1.Add( self.m_staticText7121, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT|wx.ALL, 5 )
		
		self.m_panel13 = wx.Panel( self.PreprocessingPanel, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL )
		bSizer12 = wx.BoxSizer( wx.HORIZONTAL )
		
		self.preproc_interp_none = wx.RadioButton( self.m_panel13, wx.ID_ANY, u"None", wx.DefaultPosition, wx.DefaultSize, wx.RB_GROUP )
		bSizer12.Add( self.preproc_interp_none, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5 )
		
		self.preproc_interp_min = wx.RadioButton( self.m_panel13, wx.ID_ANY, u"Minimum", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.preproc_interp_min.SetToolTipString( u"Interpolate to the minimum number of points in any of the data-sets" )
		
		bSizer12.Add( self.preproc_interp_min, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5 )
		
		self.preproc_interp_max = wx.RadioButton( self.m_panel13, wx.ID_ANY, u"Maximum", wx.DefaultPosition, wx.DefaultSize, 0 )
		bSizer12.Add( self.preproc_interp_max, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5 )
		
		self.preproc_interp_min1 = wx.RadioButton( self.m_panel13, wx.ID_ANY, u"Minimum", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.preproc_interp_min1.SetToolTipString( u"Interpolate to the minimum number of points in any of the data-sets" )
		
		bSizer12.Add( self.preproc_interp_min1, 0, wx.ALL, 5 )
		
		
		bSizer12.AddSpacer( ( 16, 0), 0, 0, 5 )
		
		self.preproc_interp_explicit = wx.RadioButton( self.m_panel13, wx.ID_ANY, u"Custom:", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.preproc_interp_explicit.SetToolTipString( u"Interpolate to the specified number of points" )
		
		bSizer12.Add( self.preproc_interp_explicit, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5 )
		
		self.preproc_interp_npoints = wx.SpinCtrl( self.m_panel13, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, 0, 0, 1000000, 0 )
		bSizer12.Add( self.preproc_interp_npoints, 0, wx.ALL, 5 )
		
		self.m_staticText19 = wx.StaticText( self.m_panel13, wx.ID_ANY, u"points", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText19.Wrap( -1 )
		bSizer12.Add( self.m_staticText19, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5 )
		
		
		self.m_panel13.SetSizer( bSizer12 )
		self.m_panel13.Layout()
		bSizer12.Fit( self.m_panel13 )
		fgSizer1.Add( self.m_panel13, 1, wx.EXPAND |wx.ALL, 5 )
		
		
		self.PreprocessingPanel.SetSizer( fgSizer1 )
		self.PreprocessingPanel.Layout()
		fgSizer1.Fit( self.PreprocessingPanel )
		self.Notebook.AddPage( self.PreprocessingPanel, u"Preprocessing", False )
		self.TuningPanel = wx.Panel( self.Notebook, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL )
		bSizer14 = wx.BoxSizer( wx.VERTICAL )
		
		sbSizer1 = wx.StaticBoxSizer( wx.StaticBox( self.TuningPanel, wx.ID_ANY, u"Simulated annealing" ), wx.VERTICAL )
		
		
		bSizer14.Add( sbSizer1, 1, wx.EXPAND, 5 )
		
		self.button_tune = wx.Button( self.TuningPanel, wx.ID_ANY, u"Tune", wx.DefaultPosition, wx.DefaultSize, 0 )
		bSizer14.Add( self.button_tune, 0, wx.ALL, 5 )
		
		
		self.TuningPanel.SetSizer( bSizer14 )
		self.TuningPanel.Layout()
		bSizer14.Fit( self.TuningPanel )
		self.Notebook.AddPage( self.TuningPanel, u"Tuning", True )
		self.ResultsPanel = wx.Panel( self.Notebook, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL )
		bSizer13 = wx.BoxSizer( wx.VERTICAL )
		
		self.DataPanel_Results = wx.Panel( self.ResultsPanel, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL )
		bSizer15 = wx.BoxSizer( wx.VERTICAL )
		
		
		self.DataPanel_Results.SetSizer( bSizer15 )
		self.DataPanel_Results.Layout()
		bSizer15.Fit( self.DataPanel_Results )
		bSizer13.Add( self.DataPanel_Results, 1, wx.EXPAND |wx.ALL, 5 )
		
		self.m_button9 = wx.Button( self.ResultsPanel, wx.ID_ANY, u"Save results", wx.DefaultPosition, wx.DefaultSize, 0 )
		bSizer13.Add( self.m_button9, 0, wx.ALIGN_RIGHT|wx.ALL, 5 )
		
		
		self.ResultsPanel.SetSizer( bSizer13 )
		self.ResultsPanel.Layout()
		bSizer13.Fit( self.ResultsPanel )
		self.Notebook.AddPage( self.ResultsPanel, u"Results", False )
		
		bSizer1.Add( self.Notebook, 1, wx.EXPAND |wx.ALL, 5 )
		
		
		self.SetSizer( bSizer1 )
		self.Layout()
		self.m_statusBar1 = self.CreateStatusBar( 1, wx.ST_SIZEGRIP, wx.ID_ANY )
		self.menubar = wx.MenuBar( 0 )
		self.menu_file = wx.Menu()
		self.menuitem_quit = wx.MenuItem( self.menu_file, wx.ID_EXIT, wx.EmptyString, wx.EmptyString, wx.ITEM_NORMAL )
		self.menu_file.AppendItem( self.menuitem_quit )
		
		self.menubar.Append( self.menu_file, u"File" ) 
		
		self.menu_help = wx.Menu()
		self.menuitem_about = wx.MenuItem( self.menu_help, wx.ID_ABOUT, wx.EmptyString, wx.EmptyString, wx.ITEM_NORMAL )
		self.menu_help.AppendItem( self.menuitem_about )
		
		self.menubar.Append( self.menu_help, u"Help" ) 
		
		self.SetMenuBar( self.menubar )
		
	
	def __del__( self ):
		pass
	

