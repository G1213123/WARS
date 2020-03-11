import base64
import math
import os
import tkinter
import urllib.parse
from tkinter import messagebox

import requests
from shapely.geometry import Point, Polygon

import combine_routes
import data_gov
import gui_popups
import read_html


class AoiInstance:
    def __init__(self, point, type, radius=0):
        self.point = []
        self.type = type
        self.radius = radius

        if isinstance( point, tuple ):
            self.point += [point]
        elif isinstance( point, list ):
            self.point += point
        else:
            raise TypeError( 'Point must be a tuple of a coordinate' )

    def close_polygon(self):
        self.type = 'Polygon'

    def add_vertex(self, point):
        if isinstance( point, tuple ):
            if self.type == 'Unclose':
                self.point.append( point )
        else:
            raise TypeError( 'Point must be a tuple of a coordinate' )


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

    '''    def rev_FX(self, circlelat, circlelng):
        # reverse coordinate translate from lat, lng to canvas xy
        dx = (circlelng - self.lng) * 40000000 * math.cos( (circlelat + self.lat) * math.pi / 360 ) / 360
        dy = (circlelat - self.lat) * 40000000 / 360
        scale = 156543.03392 * math.cos( self.lat * math.pi / 180 ) / math.pow( 2, self.zoom )
        target = {'x': self.centerX + dx / scale, 'y': self.centerY + dy / scale}
        return target'''

    def rev_FX(self, circlelat, circlelng):
        dlat = (circlelat - self.maxlat) / (self.minlat - self.maxlat)
        dlng = (circlelng - self.minlng) / (self.maxlng - self.minlng)
        x = self.canvas.canvasx( 0 ) + self.width * dlng
        y = self.canvas.canvasy( 0 ) + self.height * dlat
        return (x, y)

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

        self.aoi_append( aoi_point, x, y, scale, widget )

    def aoi_append(self, point, canvasx, canvasy, scale, widget):
        pt = (point['lat'], point['lng'])

        if self.aoimode == 'Polygon':
            widget.create_oval( canvasx - 2, canvasy - 2, canvasx + 2, canvasy + 2, width=2, fill='red', outline='red' )
            if self.aoi[-1].type == 'Unclose':
                widget.create_line( *self.rev_FX( *self.aoi[-1].point[-1] ), canvasx, canvasy )
                self.aoi[-1].add_vertex( pt )
            else:
                self.aoi.append( AoiInstance( pt, 'Unclose' ) )

        elif self.aoimode == 'Circle':
            if self.websource.get() == 'eTransport':
                html, radius = read_html.get_html( point['lat'], point['lng'] )
            else:
                radius = 500
            size = radius / scale

            widget.create_oval( canvasx - size, canvasy - size, canvasx + size, canvasy + size, width=2 )
            widget.create_text( canvasx, canvasy,
                                text='lat=%s\nlon=%s\nradius=%s' % (point['lat'], point['lng'], radius),
                                tags='CircleLabel' )
            if not self.showlbl:
                self.canvas.delete( 'CircleLabel' )
            self.aoi.append( AoiInstance( pt, 'Circle', radius ) )

    def close_polygon(self):
        self.canvas.create_line( *self.rev_FX( *self.aoi[-1].point[0] ),
                                 *self.rev_FX( *self.aoi[-1].point[-1] ) )
        self.aoi[-1].close_polygon()

    def label_circle(self):
        self.showlbl = not self.showlbl
        if self.showlbl:
            self.btnD4.config( relief=tkinter.SUNKEN )
        else:
            self.btnD4.config( relief=tkinter.RAISED )

        self.reload()

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
        # if no x,y is passed, the map will be reloaded in place
        if mousex is None:
            mousex = self.canvas.canvasx( 320 )
        if mousey is None:
            mousey = self.canvas.canvasy( 320 )
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

        self.mapimage = self.getmap()  # set image to widget reference, see:
        # http://effbot.org/pyfaq/why-do-my-tkinter-images-not-appear.htm
        self.canvas.delete( 'all' )
        self.canvas.create_image( self.canvas.canvasx( 0 ), self.canvas.canvasy( 0 ), image=self.mapimage,
                                  anchor=tkinter.NW,
                                  tags="map" )
        scale = 156543.03392 * math.cos( self.lat * math.pi / 180 ) / math.pow( 2, self.zoom )
        for marker in self.aoi:
            if marker.type == 'Circle':
                size = marker.radius / scale

                x, y = self.rev_FX( *marker.point[0] )
                self.canvas.create_oval( x - size, y - size, x + size, y + size, width=2 )
                if self.showlbl:
                    self.canvas.create_text( x, y,
                                             text='lat=%s\nlon=%s\nradius=%s' % (*marker.point[0], marker.radius),
                                             tags='CircleLabel' )
                else:
                    self.canvas.delete( 'CircleLabel' )

            elif marker.type == 'Polygon' or marker.type == 'Unclose':
                vetices = marker.point
                for id, val in enumerate( vetices ):
                    x, y = self.rev_FX( *marker.point[id] )
                    self.canvas.create_oval( x - 2, y - 2, x + 2, y + 2, width=2, fill='red', outline='red' )
                    if id == 0 and marker.type == 'Unclose':
                        pass
                    else:
                        self.canvas.create_line( *self.rev_FX( vetices[id - 1][0], vetices[id - 1][1] ),
                                                 *self.rev_FX( vetices[id][0], vetices[id][1] ) )

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
        popup = gui_popups.SaveSetting( self.save_cfg['dirname'] )
        if len( popup.out ) > 0:
            self.save_cfg = popup.out
            print( self.save_cfg )

            self.saves['saves'].clear()
            self.window.progress.config( maximum=len( self.aoi ) + 1, value=1 )
            marker_id = 1
            for marker in self.aoi:
                savename = os.path.join( self.save_cfg['dirname'], 'Marker%s.csv' % marker_id ) if self.save_cfg[
                    'batch'] else ''
                if self.webMode == 'eTransport':
                    if marker.type == 'Circle':
                        self.saves['saves'].append(
                            read_html.main( *marker.point[0], savename, self.save_cfg['showmap'] ) )

                elif self.webMode == 'data.gov.hk':
                    if marker.type == 'Polygon':
                        d = 0
                        shape = Polygon( marker.point )
                    elif marker.type == 'Circle':
                        d = 500
                        shape = Point( marker.point[0] )
                    else:
                        shape = None
                        marker_id -= 1
                    if shape is not None:
                        self.saves['saves'].append(
                            data_gov.data_gov().gui_handler( shape, d, savename, self.save_cfg['showmap'] ) )
                marker_id += 1
                self.window.progress['value'] += 1
                self.window.update()

            self.saves['dirname'] = os.path.dirname( self.saves['saves'][-1] )
            if self.save_cfg['consld']:
                self.saves['saves'].append( combine_routes.main( self.saves ) )
            self.window.route.update_list( self.saves )
            self.window.tab_parent.select( self.window.route )

    def back(self, event=None):
        if len( self.aoi ) > 1:
            del self.aoi[-1]
        self.reload()

    def clear(self, event=None):
        self.aoi = [AoiInstance( (0, 0), 'Initiate' )]
        self.reload()

    def web_list_handler(self, event=None, load=False):
        if self.webMode != self.websource.get():
            if load:
                self.websource.set( self.webMode )
            else:
                self.webMode = self.websource.get()
            if self.webMode == 'eTransport':
                if not load:
                    if not self.aoi[-1].type == 'Initiate':
                        msg_box = tkinter.messagebox.askquestion( 'Reset AOIs',
                                                                  'Choosing eTransport will clear your AOIs, are you sure?',
                                                                  icon='warning' )
                        if msg_box == 'yes':
                            self.clear()
                            self.reload()
                self.drawtoolhandler( None, 'Circle', 'eTrans' )
            else:

                tkinter.messagebox.showwarning( 'Warning',
                                                'data.gov.hk dataset supports bus stop only, gmb data is omitted :(' )
                self.drawtoolhandler( None, self.aoimode, 'data.gov.hk' )

    def drawtoolhandler(self, event=None, btn=None, web=None):
        self.btnD2.config( state="normal" )
        if web == 'eTransport':
            self.btnD2.config( state="disabled" )

        else:
            self.btnD2.config( state='normal' )
        if btn == 'Circle':
            self.btnD2.config( relief=tkinter.RAISED )
            self.btnD.config( relief=tkinter.SUNKEN )
            self.aoimode = 'Circle'
            self.btnD3.config( state="disabled" )
        elif btn == 'Polygon':
            self.btnD.config( relief=tkinter.RAISED )
            self.btnD2.config( relief=tkinter.SUNKEN )
            self.aoimode = 'Polygon'
            self.btnD3.config( state="normal" )

    def __init__(self, window, notebook):
        tkinter.Frame.__init__( self, notebook, width=window.width + 100, height=window.height + 50,
                                bg='salmon3' )
        self.name = 'frame_canvas'
        self.window = window
        self.zoom = 12
        self.location = "Hong Kong"
        self.api = 'AIzaSyB1ahSJjh6TtRwXmLOCTJ6eDY_dchw5v4s'
        self.lat = None
        self.lng = None
        self.minlat, self.maxlat, self.minlng, self.maxlng = None, None, None, None
        self.width = window.width
        self.height = window.height
        self.centerX = window.width / 2
        self.centerY = window.height / 2

        self.aoi = [AoiInstance( (0, 0), 'Initiate' )]
        web_name = ['data.gov.hk', 'eTransport']
        self.aoimode = 'Circle'
        self.webMode = web_name[1]
        self.showlbl = False
        self.s = requests.Session()
        self.save_cfg = {'batch': True, 'consld': True, 'dirname': '',
                         'map': False}
        self.saves = {'saves': [''], 'dirname': None}

        self.frmCanvas = tkinter.Frame( self, width=window.width, height=window.height, bg='green' )
        self.frmCanvas.place( relx=.5, anchor="n", y=0, x=-40 )
        #############################################################
        self.frmD = tkinter.Frame( self, width=80, height=50, bg='azure' )
        self.frmD.place( relx=.5, rely=.0, x=self.centerX - 35, anchor="nw" )

        self.websource = tkinter.StringVar( self )
        self.websource.set( self.webMode )
        w = tkinter.OptionMenu( self.frmD, self.websource, *web_name, command=self.web_list_handler )
        w.pack( side='top' )

        self.btnD = tkinter.Button( self.frmD, text='Circle', command=lambda: self.drawtoolhandler( btn='Circle' ) )

        self.btnD.pack()
        self.btnD2 = tkinter.Button( self.frmD, text='Polygon', command=lambda: self.drawtoolhandler( btn='Polygon' ) )

        self.btnD2.pack()

        sep = tkinter.Frame( self.frmD, width=80, height=80, bg='azure' )
        sep.pack()
        self.btnD3 = tkinter.Button( self.frmD, text='Close\nPolygon', command=self.close_polygon )
        self.btnD3.config( state="disabled" )
        self.btnD3.pack()

        self.btnD4 = tkinter.Button( self.frmD, text='Show\nCircle\nDetails', command=self.label_circle )
        self.btnD4.pack()

        self.drawtoolhandler( btn=self.aoimode, web=self.webMode )

        #############################################################
        self.frmA = tkinter.Frame( self, width=250, height=window.height, bg='yellow' )
        self.frmA.place( relx=.5, rely=.5, x=self.centerX - 35, anchor="w" )

        self.btnA = tkinter.Button( self.frmA, text='Back', command=self.back )
        self.btnA.pack( side='bottom' )
        self.btnA2 = tkinter.Button( self.frmA, text='Clear', command=self.clear )
        self.btnA2.pack( side='bottom' )
        self.btnA3 = tkinter.Button( self.frmA, text='Enter', command=self.to_read_html )
        self.btnA3.configure( width=10, activebackground="#33B5E5", relief=tkinter.FLAT )
        self.btnA3.pack( side='top' )
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
        self.canvas = tkinter.Canvas( self.frmCanvas, width=window.width, height=window.height )
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

        window.bind( '<Return>', self.search )
