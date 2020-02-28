'''
Created on Jan 1, 2020

@author: Andrew.WF.Ng
'''

import base64
import tkinter
from tkinter import ttk
from tkinter import filedialog
from tkinter.filedialog import askopenfilename, askdirectory
import urllib.parse
import os
import requests
import math
import shelve
import pandas as pd
import pickle
import general as gn

import gui_frame_canvas
import gui_logging
import gui_popups

def treeview_sort_column(tv, col, reverse):
    l = [(tv.set( k, col ), k) for k in tv.get_children()]
    l.sort( reverse=reverse )

    # rearrange items in sorted positions
    for index, (val, k) in enumerate( l ):
        tv.move( k, '', index )

    # reverse sort next time
    tv.heading( col, command=lambda: treeview_sort_column( tv, col, not reverse ) )


class displayroutes( tkinter.Frame ):

    def update_list(self, saves):
        for string in saves['saves']:
            self.w['menu'].add_command( label=string,
                                        command=lambda value=string: self.read_csv( value ) )

    def read_csv(self, name):
        self.variable.set( name )
        try:
            self.reader = pd.read_csv( name, delimiter=',' )
            self.reader = self.reader.fillna( '' )
            for SP in self.reader['Service Provider'].unique():
                self.bus_treeview.insert( "", 'end', SP, values=(SP, '', '', '') )
            for index, row in self.reader.iterrows():
                ServiceProvider = row['Service Provider']
                Route = row['Route']
                Origin = row['Origin']
                Destination = row['Destination']
                self.bus_treeview.insert( ServiceProvider, 'end',
                                          values=(ServiceProvider, Route, Origin, Destination) )
        except TypeError:
            pass

    def __init__(self, MainWindow, notebook):
        tkinter.Frame.__init__( self, notebook, width=MainWindow.width + 100, height=MainWindow.height + 50, bg='cyan' )

        self.name = 'displayroute'

        self.variable = tkinter.StringVar( self )
        self.variable.set( "Choose File" )

        self.w = tkinter.OptionMenu( self, self.variable, 'Choose File' )
        self.w.pack()

        columns = ['Service Provider', 'Route', 'Origin', 'Destination']
        self.bus_treeview = ttk.Treeview( self, height=MainWindow.height - 608,
                                          columns=columns )  # , show = 'headings')

        vsb = ttk.Scrollbar( self, orient="vertical", command=self.bus_treeview.yview )
        vsb.pack( side=tkinter.RIGHT, fill='y' )
        self.bus_treeview.column( '#0', width=10 )
        for i, col in enumerate( columns ):
            self.bus_treeview.column( col, width=math.floor( i / 2 ) * 100 + 100 )
            self.bus_treeview.heading( col, text=col,
                                       command=lambda _col=col: treeview_sort_column( self.bus_treeview, _col,
                                                                                      False ) )

        self.bus_treeview.configure( yscrollcommand=vsb.set )
        self.bus_treeview.pack( expand=True, fill=tkinter.BOTH, padx=10, pady=10 )


class get_headway( tkinter.Frame ):
    def __init__(self, MainWindow, notebook):
        self.window = MainWindow
        tkinter.Frame.__init__( self, notebook, width=MainWindow.width + 100, height=MainWindow.height + 50,
                                bg='light green' )

        self.name = 'get_headway'
        self.archive = r'C:\Users\Andrew.WF.Ng\Documents\Python_Scripts\PT\gmb_achive'

        Mode = ['KMB', 'CTB/NWFB', 'GMB']

        self.input_panelA = tkinter.Frame( self, height=100 )
        self.input_panelA.pack( fill='x' )
        self.input_panelB = tkinter.Frame( self, height=100 )
        self.input_panelB.pack( fill='x' )
        self.variable1 = tkinter.StringVar( self )
        self.variable1.set( "Choose Service Provider" )
        self.am1 = tkinter.StringVar( self, value=7 )
        self.am2 = tkinter.StringVar( self, value=8 )
        self.pm1 = tkinter.StringVar( self, value=17 )
        self.pm2 = tkinter.StringVar( self, value=18 )

        w = tkinter.OptionMenu( self.input_panelA, self.variable1, *Mode, command=self.toggle_dist )
        w.grid( column=3, row=0 )

        x = tkinter.Button( self.input_panelA, text='Enter', command=self.go_bus_web )
        x.grid( column=5, row=0 )

        e = tkinter.Label( self.input_panelB, text='AM start' )
        e.pack( side='left' )
        f = tkinter.Entry( self.input_panelB, width=20, textvariable=self.am1 )
        f.pack( side='left' )
        g = tkinter.Label( self.input_panelB, text='AM end' )
        g.pack( side='left' )
        h = tkinter.Entry( self.input_panelB, width=20, textvariable=self.am2 )
        h.pack( side='left' )
        i = tkinter.Label( self.input_panelB, text='PM start' )
        i.pack( side='left' )
        j = tkinter.Entry( self.input_panelB, width=20, textvariable=self.pm1 )
        j.pack( side='left' )
        k = tkinter.Label( self.input_panelB, text='PM end' )
        k.pack( side='left' )
        l = tkinter.Entry( self.input_panelB, width=20, textvariable=self.pm2 )
        l.pack( side='left' )

        self.variable2 = tkinter.StringVar( self )

        columns = ['id', 'route', 'info', 'headway_am', 'headway_pm', 'bound', 'period_am', 'period_pm']
        self.bus_treeview = ttk.Treeview( self, height=MainWindow.height - 608, columns=columns, show='headings' )

        vsb = ttk.Scrollbar( self, orient="vertical", command=self.bus_treeview.yview )
        vsb.pack( side=tkinter.RIGHT, fill='y' )
        self.bus_treeview.column( '#0', width=10 )
        for i, col in enumerate( columns ):
            self.bus_treeview.column( col, width=150 if i == 2 else 70 )
            self.bus_treeview.heading( col, text=col,
                                       command=lambda _col=col: treeview_sort_column( self.bus_treeview, _col,
                                                                                      False ) )

        self.bus_treeview.configure( yscrollcommand=vsb.set )
        self.bus_treeview.pack( expand=True, fill=tkinter.BOTH, padx=10, pady=10 )

    def toggle_dist(self, value):
        hidden = value == 'GMB'
        dist = ['Hong Kong Island', 'Kowloon', 'New Territories']
        m1 = tkinter.Frame( self.input_panelA, width=400 )
        m = tkinter.OptionMenu( self.input_panelA, self.variable2, *dist )
        if hidden:
            m1.grid( column=6, row=0 )
            m.grid( column=7, row=0 )
        else:
            m.grid_remove()

    def go_bus_web(self):
        SP = self.variable1.get().lower().split( '/' )[0]
        route = self.window.route.reader
        extra_loading = 0
        if SP == 'ctb':
            routeSP = route[
                (route['Service Provider'].str.contains( 'CTB' )) | (route['Service Provider'].str.contains( 'NWFB' ))][
                'Route']
            extra_loading = 3
        else:
            routeSP = route[route['Service Provider'].str.contains( SP.upper() )]['Route']
        print( routeSP )
        routeSP = list( dict.fromkeys( routeSP ) )
        savename = os.path.join( self.window.frame_map.saves['dirname'],
                                 SP + '-' + self.am1.get() + '-' + self.pm1.get() + '.xlsx' )
        self.window.progress.config( maximum=len( routeSP ) + extra_loading, value=0 )
        getattr( self, SP )( routeSP, savename, self.window )

    def kmb(self, routeSP, savename, progress):
        import kmb
        kmb_headway = kmb.main( routeSP, am1=self.am1.get(), am2=self.am2.get(), pm1=self.pm1.get(), pm2=self.pm2.get(),
                                savename=savename, window=progress )
        self.write_headway( kmb_headway )

    def gmb(self, routeSP, savename, progress):
        import gmb_achive
        gmb_headway = gmb_achive.gmb_get_headway( routeSP, am1=self.am1.get(), am2=self.am2.get(), pm1=self.pm1.get(),
                                                  pm2=self.pm2.get(), savename=savename, window=progress,
                                                  archive=self.archive )
        self.write_headway( gmb_headway.PT )

    def ctb(self, routeSP, savename, progress):
        import ctb
        ctb_headway = ctb.main( routeSP, am1=self.am1.get(), am2=self.am2.get(), pm1=self.pm1.get(), pm2=self.pm2.get(),
                                savename=savename, window=progress )
        self.write_headway( ctb_headway )

    def write_headway(self, headway):
        self.bus_treeview.delete( *self.bus_treeview.get_children() )
        for index, row in headway.iterrows():
            id = index
            route = row['route']
            info = row['info']
            headway_am = row['headway_am']
            headway_pm = row['headway_pm']
            bound = row['bound']
            period_am = row['period_am']
            period_pm = row['period_pm']
            self.bus_treeview.insert( '', 'end',
                                      values=(id, route, info, headway_am, headway_pm, bound, period_am, period_pm) )
            self.window.progress.config( value=0 )


class MainWindow( tkinter.Toplevel ):

    def savework(self):
        path = os.path.expanduser( '~/Documents/Python_Scripts/PT/saves' )
        if not os.path.exists( path ):
            os.makedirs( path )
        savename = os.path.join( path, 'workspace.pickle' )
        PTApp = gui_popups.var_logging( self.__modules )

        with open( savename, 'wb' ) as handle:
            pickle.dump( PTApp, handle, protocol=pickle.HIGHEST_PROTOCOL )

    def loadwork(self):
        MsgBox = 'yes'
        if len( self.frame_map.aoi ) > 0 and self.frame_map.aoi[0].type != 'Initiate':
            MsgBox = tkinter.messagebox.askquestion( 'Load Save FIle',
                                                     'Loading saves will clear your AOIs, are you sure?',
                                                     icon='warning' )
        if MsgBox == 'yes':
            tkinter.Tk().withdraw()  # we don't want a full GUI, so keep the root window from appearing
            save = askopenfilename( title="Load save", filetypes=(("pickle", "*.pickle"), (
                "all files", "*.*")) )  # show an "Open" dialog box and return the path to the selected file
            with open( save, 'rb' ) as handle:
                PTApp = pickle.load( handle )
            for module in self.__modules:
                for key, value in PTApp[module.name].items():
                    setattr( module, key, value )
            # self.frame_map.canvas.scan_dragto(self.frame_map.centerX, self.frame_map.centerY)
            self.frame_map.reload( mousex=self.frame_map.centerX, mousey=self.frame_map.centerY )
            self.frame_map.webListHandler( load=True )

    def gmb_achive(self):
        import td_fetch_gmb
        tkinter.Tk().withdraw()  # we don't want a full GUI, so keep the root window from appearing
        save = askdirectory(
            title="Select save directory" )  # show an "Open" dialog box and return the path to the selected file
        if save != '':
            td_fetch_gmb.fetch_archive( save )
        self.headway.archive = save

    def __init__(self, parent):
        tkinter.Toplevel.__init__( self, parent )
        self.name = 'Mainwindow'
        self.width = 640
        self.height = 640

        self.title( "PT" )
        self.minsize( self.width + 170, self.height + 100 )
        # self.window.maxsize(self.width + 200, self.height + 100)

        self.filemenu = tkinter.Menu()
        self.config( menu=self.filemenu )
        self.menu1 = tkinter.Menu( self.filemenu, tearoff=0 )
        self.menu1.add_command( label='save', command=self.savework )
        self.menu1.add_command( label='load', command=self.loadwork )
        self.filemenu.add_cascade( label='File', menu=self.menu1 )

        self.menu2 = tkinter.Menu( self.filemenu, tearoff=0 )
        self.menu2.add_command( label='create gmb archive', command=self.gmb_achive )
        self.filemenu.add_cascade( label='Import', menu=self.menu2 )

        self.tab_parent = ttk.Notebook( self, width=self.width, height=self.height )

        self.frame_map = gui_frame_canvas.frame_canvas( self, self.tab_parent )
        self.route = displayroutes( self, self.tab_parent )
        self.headway = get_headway( self, self.tab_parent )

        self.__modules = [self, self.frame_map, self.route, self.headway]
        self.log = gui_logging.ShowLog( self, self.tab_parent )
        # self.frame_map.pack()

        self.tab_parent.add( self.frame_map, text="Map" )
        self.tab_parent.add( self.route, text="Route" )
        self.tab_parent.add( self.headway, text="headway" )
        self.tab_parent.add( self.log, text="log" )
        self.tab_parent.pack( expand=True, fill=tkinter.BOTH )

        bottombar = tkinter.Frame( self, height=5 )
        bottombar.pack( expand=False, fill=tkinter.X )
        self.progress = ttk.Progressbar( bottombar, orient=tkinter.HORIZONTAL, length=300, mode='determinate' )
        self.progress.pack( side='right' )

        self.frame_map.reload()


if __name__ == "__main__":
    root = tkinter.Tk()
    root.withdraw()
    MainWindow( root )
    root.mainloop()

# for pyinstaller: https://github.com/pyinstaller/pyinstaller/issues/2137  ## install develop
