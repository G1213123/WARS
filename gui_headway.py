import os
import pickle
import tkinter
from tkinter import ttk, messagebox

from gui_routes import treeview_sort_column


class get_headway( tkinter.Frame ):
    def __init__(self, MainWindow, notebook):
        self.window = MainWindow
        tkinter.Frame.__init__( self, notebook, width=MainWindow.width + 100, height=MainWindow.height + 50,
                                bg='light green' )

        self.name = 'get_headway'

        directory = os.path.expanduser( '~/Documents/Python_Scripts/WARS/cfg' )
        self.savename = os.path.join( directory, 'archive.cfg' )
        try:
            with open( self.savename, 'rb' ) as handle:
                self.archive = pickle.load( handle )
        except:
            self.archive = ''

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

        self.variable2 = tkinter.StringVar( self, value='Select District' )

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
        print(routeSP)
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
        if self.archive == '':
            messagebox.showwarning( 'Warning', 'Please create gmb archive through \n "Import > create gmb archive"' )
        else:
            import gmb_achive
            gmb_headway = gmb_achive.gmb_get_headway( routeSP, am1=self.am1.get(), am2=self.am2.get(),
                                                      pm1=self.pm1.get(),
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
