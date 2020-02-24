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

import read_html
import combine_routes

class savesetting( tkinter.Toplevel ):
    # Prompt for configuring save settings
    # Activate by 'Enter' button in Map Frame
    # Batch save:   Save all map markers to multiple csv files in the same folder
    #               Default save names 'Marker1.csv', 'Marker2.csv' ...
    #               Unlock folder name entry/browse option
    # Consolidate:  Combine all markers csv files into single csv file
    #               Default save name 'routes_consolidate.csv'
    #               Save path refers to the last marker csv file

    def __init__(self):
        # Configure save popup dialogue
        self.popup = tkinter.Toplevel()
        self.popup.geometry( "%dx%d%+d%+d" % (300, 200, 250, 125) )
        self.popup.title( "Save" )

        # Return save setting as dict
        self.out = {'batch': False, 'consld': False, 'dirname': ''}

        # batch save checkbox
        frmA = tkinter.Frame( self.popup, width=self.popup.winfo_reqwidth(), height=50 )
        frmA.pack()
        self.batch = tkinter.IntVar( value=1 )
        self.batch_box = tkinter.Checkbutton( frmA, text='batch save', variable=self.batch, command=self.com )
        self.batch_box.pack()

        # consolidate markers checkbox
        frmB = tkinter.Frame( self.popup, width=self.popup.winfo_reqwidth(), height=50 )
        frmB.pack()
        self.consld = tkinter.IntVar( value=1 )
        consld_box = tkinter.Checkbutton( frmB, text='consolidate markers', variable=self.consld )
        consld_box.pack()

        # show html map check box
        frmC = tkinter.Frame( self.popup, width=self.popup.winfo_reqwidth(), height=50, bg='green')
        frmC.pack()
        self.showmap = tkinter.IntVar( value=0 )
        map_box = tkinter.Checkbutton( frmC, text='show map file', variable=self.showmap )
        map_box.pack()

        # Browse folder dialogue button
        frmD = tkinter.Frame( self.popup, width=self.popup.winfo_reqwidth(), height=50 )
        frmD.pack()
        label = tkinter.Label( frmD, text="Folder" )
        label.pack()
        self.dirname = tkinter.StringVar()
        self.textbox = tkinter.Entry( frmD, textvariable=self.dirname, width=200, state='normal' )
        self.textbox.pack()
        browse = tkinter.Button( frmD, text='Browse', command=self.browse_button )
        browse.pack()

        # Done button
        button = tkinter.Button( self.popup, text="Done", command=self.done )
        button.pack()

        # Set popup focus and wait
        self.popup.grab_set()
        self.popup.wait_window()

    def browse_button(self):
        # file dialog prompt for file picking
        self.popup.grab_release()
        dirname = filedialog.askdirectory()
        self.dirname = dirname
        self.textbox.insert( 0, dirname )
        self.popup.grab_set()
        self.popup.focus_force()

    def com(self):
        # activiate and deactivate file path entry box
        if self.batch.get():
            self.textbox.config( state='normal' )
        else:
            self.textbox.config( state='disabled' )

    def done(self):
        self.out = {'batch': self.batch.get(), 'consld': self.consld.get(), 'dirname': self.dirname, 'map':self.showmap.get()}
        self.popup.destroy()


class frame_canvas( tkinter.Frame ):
    # Frame containing map display, location searching function and enter/clear box for specifying location
    #   of interest
    # used in the main window tab of 'map'

    def FX(self, lat, lng, zoom, centerX, centerY, mouseX, mouseY):
        # translating a point coordinate on a canvas to latitude and longitude
        # coordinate of center frame is used as a referencing point

        # x, y as delta distance of input point to reference center point
        x = mouseX - centerX,
        y = mouseY - centerY,

        s = min( max( math.sin( lat * (math.pi / 180) ), -.9999 ), .9999 )
        tiles = 1 << zoom
        centerPoint = {
            'x': 128 + lng * (256 / 360),
            'y': 128 + 0.5 * math.log( (1 + s) / (1 - s) )
                 * -(256 / (2 * math.pi))
        }
        mousePoint = {
            'x': (centerPoint['x'] * tiles) + x[0],
            'y': (centerPoint['y'] * tiles) + y[0]
        }
        mouseLatLng = {
            'lat': (2 * math.atan( math.exp( ((mousePoint['y'] / tiles) - 128)
                                             / -(256 / (2 * math.pi)) ) ) -
                    math.pi / 2) / (math.pi / 180),
            'lng': (((mousePoint['x'] / tiles) - 128) / (256 / 360))
        }
        return mouseLatLng

    def rev_FX(self, circlelat, circlelng):
        # reverse coordinate translate from lat, lng to canvas xy
        dx = (circlelng - self.lng) * 40000000 * math.cos( (circlelat + self.lat) * math.pi / 360 ) / 360
        dy = (circlelat - self.lat) * 40000000 / 360
        scale = 156543.03392 * math.cos( self.lat * math.pi / 180 ) / math.pow( 2, self.zoom )
        target = {'x': self.centerX + dx / scale, 'y': self.centerY + dy / scale}
        return target

    def getaddress(self, lat, lng):
        # return url address for static map image by either provide lat lng or geocode a location name
        if (lat is None) and (lng is None):
            locationnospaces = urllib.parse.quote( self.location )
            geocode = "https://maps.googleapis.com/maps/api/geocode/json?address={0}&key={1}" \
                .format( locationnospaces, self.api )
            r = self.s.get( geocode )
            results = r.json()['results'][0]
            self.lat = results['geometry']['location']['lat']
            self.lng = results['geometry']['location']['lng']
        address = "http://maps.googleapis.com/maps/api/staticmap?center={0},{1}&zoom={2}&size={3}x{4}&format=gif&sensor=false&key={5}" \
            .format( lat, lng, self.zoom, 640, 640, self.api )
        return address

    def getmap(self):
        # return image from an url request
        address = self.getaddress( self.lat, self.lng )
        r = self.s.get( address )
        base64data = base64.encodebytes( r.content )
        image = tkinter.PhotoImage( data=base64data )
        return image

    def create_grid(self, event=None):
        # depreciated. For record only
        w = self.width  # Get current width of canvas
        h = self.height  # Get current height of canvas
        self.canvas.delete( 'grid_line' )  # Will only remove the grid_line

        # Creates all vertical lines at intevals of 100
        for i in range( 0, w, 160 ):
            self.canvas.create_line( [(i, 0), (i, h)], tag='grid_line' )

        # Creates all horizontal lines at intevals of 100
        for i in range( 0, h, 160 ):
            self.canvas.create_line( [(0, i), (w, i)], tag='grid_line' )

    def canvasclick(self, event):
        x, y = self.canvas.canvasx( event.x ), self.canvas.canvasy( event.y )
        widget = event.widget
        scale = 156543.03392 * math.cos( self.lat * math.pi / 180 ) / math.pow( 2, self.zoom )

        aoi_point = self.FX( self.lat, self.lng, self.zoom, self.centerX, self.centerY, x,
                             y )

        html, radius =read_html.get_html(aoi_point['lat'], aoi_point['lng'])

        size = radius / scale
        widget.create_oval( x - size, y - size, x + size, y + size, width=2 )

        aoi_point.update( {'radius' : radius} )
        self.aoi.append( aoi_point )
        self.canvas_marker.append( {'x': x, 'y': y} )
        print( 0 )
        # label = self.getlabelname()
        # widget.create_text(x, y+2*size, text=label)

    def move_from(self, event):
        ''' Remember previous coordinates for scrolling with the mouse '''
        self.delatmouse = [event.x, event.y]
        self.canvas.scan_mark( event.x, event.y )

    def move_to(self, event):
        ''' Drag (move) canvas to the new position '''
        self.delatmouse = [event.x - self.delatmouse[0], event.y - self.delatmouse[1]]
        self.canvas.scan_dragto( event.x, event.y, gain=1 )
        # show_image()  # redraw the image

    def reload(self, event=None, mousex=None, mousey=None, ):
        if mousex is None:
            mousex=self.canvas.canvasx(320)
        if mousey is None:
            mousey=self.canvas.canvasy(320)
        new_location = self.FX( self.lat, self.lng, self.zoom, self.centerX, self.centerY, mousex,
                                mousey )
        self.lat = new_location['lat']
        self.lng = new_location['lng']
        self.centerX = self.canvas.canvasx( 320 )
        self.centerY = self.canvas.canvasy( 320 )
        bottom_left = self.FX( self.lat, self.lng, self.zoom, self.centerX, self.centerY, self.canvas.canvasx( 0 ),
                               self.canvas.canvasy( 0 ) )
        top_right = self.FX( self.lat, self.lng, self.zoom, self.centerX, self.centerY, self.canvas.canvasx( 640 ),
                             self.canvas.canvasy( 640 ) )
        self.maxlat = bottom_left['lat']
        self.minlng = bottom_left['lng']
        self.minlat = top_right['lat']
        self.maxlng = top_right['lng']

        self.mapimage = self.getmap()   # set image to widget reference, see:
                                        # http://effbot.org/pyfaq/why-do-my-tkinter-images-not-appear.htm
        self.canvas.delete( 'all' )
        self.canvas.create_image( self.canvas.canvasx( 0 ), self.canvas.canvasy( 0 ), image=self.mapimage, anchor=tkinter.NW,
                                  tags="map" )
        scale = 156543.03392 * math.cos( self.lat * math.pi / 180 ) / math.pow( 2, self.zoom )
        for marker in self.aoi:
            if self.minlat <= marker['lat'] <= self.maxlat:
                if self.minlng < marker['lng'] <= self.maxlng:
                    size = marker['radius'] / scale
                    dlat = (marker['lat'] - self.maxlat) / (self.minlat - self.maxlat)
                    dlng = (marker['lng'] - self.minlng) / (self.maxlng - self.minlng)
                    x = self.canvas.canvasx( 0 ) + self.width * dlng
                    y = self.canvas.canvasy( 0 ) + self.height * dlat
                    self.canvas.create_oval( x - size, y - size, x + size, y + size, width=2 )
        self.canvas.focus_set()
        self.window.update()

    def wheel(self, event):
        if event.num == 4 or event.delta == 120:
            self.zoom = self.zoom + 1
        elif event.num == 5 or event.delta == -120:
            self.zoom = self.zoom - 1
        self.reload()
        # mapimage = self.getmap()
        # self.canvas.itemconfig("map", image=mapimage)
        # self.window.mainloop()

    def search(self, event=None):
        self.location = self.varB.get()
        self.getaddress( None, None )
        self.reload()

    def to_read_html(self, event=None):
        popup = savesetting()
        self.save_cfg = popup.out
        print( self.save_cfg )

        self.saves['saves'].clear()
        if self.save_cfg['batch']:
            marker_id = 1
            for marker in self.aoi:
                self.saves['saves'].append( read_html.main( marker['lat'], marker['lng'],
                                                            os.path.join( self.save_cfg['dirname'],
                                                                          'Marker%s.csv' % marker_id ), self.save_cfg['map'] ) )
                marker_id += 1
        else:
            for marker in self.aoi:
                self.saves['saves'].append( read_html.main( marker['lat'], marker['lng'], show= self.save_cfg['map']) )

        self.saves['dirname'] = os.path.dirname( self.saves['saves'][-1] )
        if self.save_cfg['consld']:
            self.saves['saves'].append( combine_routes.main( self.saves ) )
        self.window.route.update_list( self.saves )

    def back(self, event=None):
        del self.aoi[-1]
        del self.canvas_marker[-1]
        self.reload()

    def clear(self, event=None):
        self.aoi = []
        self.canvas_marker = []
        self.reload()

    def __init__(self, MainWindow, notebook):
        tkinter.Frame.__init__( self, notebook, width=MainWindow.width + 100, height=MainWindow.height + 50,
                                bg='salmon3' )
        self.name='frame_canvas'
        self.window = MainWindow
        self.zoom = 12
        self.location = "Hong Kong"
        self.api = 'AIzaSyB1ahSJjh6TtRwXmLOCTJ6eDY_dchw5v4s'
        self.lat = None
        self.lng = None
        self.minlat, self.maxlat, self.minlng, self.maxlng = None, None, None, None
        self.width = MainWindow.width
        self.height = MainWindow.height
        self.centerX = MainWindow.width / 2
        self.centerY = MainWindow.height / 2
        self.canvas_marker = []
        self.aoi = []
        self.s = requests.Session()
        self.saves = {'saves': [''], 'dirname': None}

        self.frmCanvas = tkinter.Frame( self, width=MainWindow.width, height=MainWindow.height, bg='green' )
        self.frmCanvas.place( relx=.5, anchor="n", y=0, x=-40 )
        #############################################################
        self.frmA = tkinter.Frame( self, width=80, height=MainWindow.height, bg='yellow' )
        self.frmA.place( relx=.5, rely=.5, x=self.centerX - 35, anchor="w" )

        self.btnA = tkinter.Button( self.frmA, text='Back', command=self.back )
        self.btnA.pack( side='bottom' )
        self.btnA2 = tkinter.Button( self.frmA, text='Clear', command=self.clear )
        self.btnA2.pack( side='bottom' )
        self.btnA3 = tkinter.Button( self.frmA, text='Enter', command=self.to_read_html )
        self.btnA3.configure( width=10, activebackground="#33B5E5", relief=tkinter.FLAT )
        self.btnA3.pack( side='right' )
        #############################################################

        self.frmB = tkinter.Frame( self, width=50, height=20 )
        self.frmB.place( relx=.5, rely=.48, y=self.centerY, anchor="n" )

        self.varB = tkinter.StringVar( value=self.location )
        self.inputB = tkinter.Entry( self.frmB, width=50, textvariable=self.varB )
        self.inputB.pack( side='left' )
        self.btnB = tkinter.Button( self.frmB, text='Search', command=self.search )
        self.btnB.configure( width=10, activebackground="#33B5E5", relief=tkinter.FLAT )
        self.btnB.pack( side='right' )

        ###############################################################
        self.mapimage = self.getmap()
        self.canvas = tkinter.Canvas( self.frmCanvas, width=MainWindow.width, height=MainWindow.height )
        self.canvas.create_image( 0, 0, image=self.mapimage, anchor=tkinter.NW, tags="map" )
        self.delta_org = [0, 0]
        self.canvas.bind( "<Button-3>", self.canvasclick )
        self.canvas.bind( '<ButtonPress-1>', self.move_from )
        self.canvas.bind( '<B1-Motion>', self.move_to )
        self.canvas.bind( '<ButtonRelease-1>', self.reload )
        self.canvas.bind( '<MouseWheel>', self.wheel )  # with Windows and MacOS, but not Linux
        self.canvas.pack( fill='none', expand=True )
        # self.create_grid()
        self.canvas.focus_set()

        MainWindow.bind( '<Return>', self.search )


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
        except:
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

        self.name='get_headway'
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
        SP = self.variable1.get().lower().split('/')[0]
        route = self.window.route.reader
        extra_loading = 0
        if SP == 'ctb':
            routeSP = route[(route['Service Provider'].str.contains('CTB')) | (route['Service Provider'].str.contains('NWFB'))]['Route']
            extra_loading = 3
        else:
            routeSP = route[route['Service Provider'].str.contains( SP.upper() )]['Route']
        print( routeSP )
        routeSP = list(dict.fromkeys(routeSP))
        savename = os.path.join( self.window.frame_map.saves['dirname'],
                                 SP + '-' + self.am1.get() + '-' + self.pm1.get() + '.xlsx' )
        self.window.progress.config(maximum=len(routeSP)+ extra_loading, value = 0 )
        getattr( self, SP )( routeSP, savename, self.window)

    def kmb(self, routeSP, savename, progress):
        import kmb
        kmb_headway = kmb.main( routeSP, am1=self.am1.get(), am2=self.am2.get(), pm1=self.pm1.get(), pm2=self.pm2.get(),
                                savename=savename, window=progress )
        self.write_headway( kmb_headway )

    def gmb(self, routeSP, savename, progress):
        import gmb_achive
        gmb_headway = gmb_achive.gmb_get_headway( routeSP, am1=self.am1.get(), am2=self.am2.get(), pm1=self.pm1.get(),
                                                  pm2=self.pm2.get(), savename=savename , window=progress, archive=self.archive)
        self.write_headway( gmb_headway.PT )

    def ctb(self, routeSP, savename, progress):
        import ctb
        ctb_headway = ctb.main( routeSP, am1=self.am1.get(), am2=self.am2.get(), pm1=self.pm1.get(), pm2=self.pm2.get(),
                                savename=savename, window=progress)
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
            self.window.progress.config(value = 0)

class MainWindow( tkinter.Toplevel ):

    def savework(self):
        path = os.path.expanduser('~/Documents/Python_Scripts/PT/saves')
        if not os.path.exists( path ):
            os.makedirs( path )
        savename = os.path.join(path, 'workspace.pickle')

        PTApp = {}
        for module in self.modules['widget']:
            data = {key:value for key, value in module.__dict__.items() if
                    not (key.startswith( '_' ) or callable( key ) or not isinstance( value, (str, list, int, float) ))}
            PTApp[module.name] = data
        with open( savename, 'wb' ) as handle:
            pickle.dump( PTApp, handle, protocol=pickle.HIGHEST_PROTOCOL )

    def loadwork(self):
        tkinter.Tk().withdraw()  # we don't want a full GUI, so keep the root window from appearing
        save = askopenfilename( title="Load save", filetypes=(("pickle", "*.pickle"), (
            "all files", "*.*")) )  # show an "Open" dialog box and return the path to the selected file
        with open( save, 'rb' ) as handle:
            PTApp = pickle.load( handle )
        for module in self.modules['widget']:
            for key, value in PTApp[module.name].items():
                setattr(module, key, value)
        #self.frame_map.canvas.scan_dragto(self.frame_map.centerX, self.frame_map.centerY)
        self.frame_map.reload(mousex=self.frame_map.centerX, mousey=self.frame_map.centerY)

    def gmb_achive(self):
        import td_fetch_gmb
        tkinter.Tk().withdraw()  # we don't want a full GUI, so keep the root window from appearing
        save = askdirectory(title="Select save directory")  # show an "Open" dialog box and return the path to the selected file
        if save != '':
            td_fetch_gmb.fetch_archive(save)
        self.headway.archive = save

    def __init__(self, parent):
        tkinter.Toplevel.__init__( self, parent )
        self.name='Mainwindow'
        self.width = 640
        self.height = 640

        self.title( "PT" )
        self.minsize( self.width + 100, self.height + 100 )
        # self.window.maxsize(self.width + 200, self.height + 100)

        self.filemenu=tkinter.Menu()
        self.config(menu=self.filemenu)
        self.menu1=tkinter.Menu(self.filemenu, tearoff=0)
        self.menu1.add_command(label='save', command=self.savework)
        self.menu1.add_command( label='load', command=self.loadwork)
        self.filemenu.add_cascade(label='File', menu=self.menu1)

        self.menu2=tkinter.Menu(self.filemenu, tearoff=0)
        self.menu2.add_command(label='create gmb archive', command=self.gmb_achive)
        self.filemenu.add_cascade(label='Import', menu=self.menu2)

        self.tab_parent = ttk.Notebook( self, width=self.width, height=self.height )

        self.frame_map = frame_canvas( self, self.tab_parent )
        self.route = displayroutes( self, self.tab_parent )
        self.headway = get_headway( self, self.tab_parent )
        # self.frame_map.pack()

        self.tab_parent.add( self.frame_map, text="Map" )
        self.tab_parent.add( self.route, text="Route" )
        self.tab_parent.add( self.headway, text="headway" )
        self.tab_parent.pack( expand=True, fill=tkinter.BOTH )

        self.modules = {'widget':[self, self.frame_map, self.route, self.headway]}

        bottombar=tkinter.Frame(self, height=5)
        bottombar.pack(expand=False, fill=tkinter.X)
        self.progress=ttk.Progressbar(bottombar,orient=tkinter.HORIZONTAL,length=300,mode='determinate')
        self.progress.pack(side='right')

        self.frame_map.reload()


if __name__ == "__main__":
    root = tkinter.Tk()
    root.withdraw()
    MainWindow( root )
    root.mainloop()


# for pyinstaller: https://github.com/pyinstaller/pyinstaller/issues/2137  ## install develop
