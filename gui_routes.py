import math
import os
import tkinter
from tkinter import ttk

import pandas as pd

import general


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
        if name is not None:
            self.routes_file = name
        self.variable.set( self.routes_file )
        self.bus_treeview.delete( *self.bus_treeview.get_children() )
        try:
            self.reader = pd.read_csv( self.routes_file, delimiter=',' )
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

    def read_route(self):
        savename = general.file_prompt()
        self.read_csv( savename )
        self.window.frame_map.saves['saves'].append( savename )
        self.window.frame_map.saves['dirname'] = os.path.dirname( savename )
        self.window.tab_parent.select( self.window.route )

    def clear(self):
        self.bus_treeview.delete( *self.bus_treeview.get_children() )
        self.w['menu'].delete(0, 'end')

    def __init__(self, MainWindow, notebook):
        tkinter.Frame.__init__( self, notebook, width=MainWindow.width + 100, height=MainWindow.height + 50, bg='cyan' )

        self.window = MainWindow
        self.name = 'displayroute'

        self.routes_file = ""
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
