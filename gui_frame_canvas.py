import base64
import math
import os
import tkinter
import urllib.parse
from tkinter import messagebox

import numpy as np
import requests
from shapely.geometry import Point, Polygon

import combine_routes
import data_gov
import gui_popups
import read_html


class AoiInstance:
    """
    object of the area enclosed by users (Area of Interest)
    """

    def __init__(self, point, type, id, radius=0) -> None:
        """
        initial set-up of the area

        Args:
            point (list of (float,float)|(float,float)): a single or a list of vertices (tuple) for a polygon object
            type (str): ype of the area, can be initiate(at the initiation of the program), 'circle',
                        'unclosed'(for open edged polygon) or 'polygon'
            radius (float): non-zero if self.type != 'circle'
        """
        self.point = []
        self.type = type
        self.radius = radius
        self.id = id

        # check the point parameter input is a single point (tuple) or a list of points (list of tuple)
        if isinstance( point, tuple ):
            self.point += [point]
        elif isinstance( point, list ):
            self.point += point
        else:
            raise TypeError( 'Point must be a tuple of a coordinate' )

    def close_polygon(self):
        """
        change type from 'Unclosed' to 'Polygon'

        Returns: none

        """
        self.type = 'Polygon'

    def add_vertex(self, point):
        """
        Add vertices to the 'Unclosed' Polygon

        Args:
            point ((float,float)): the xy coordinate of the vertex to be added

        Returns: None

        """
        if isinstance( point, tuple ):
            if self.type == 'Unclose':
                self.point.append( point )
        else:
            raise TypeError( 'Point must be a tuple of a coordinate' )


class frame_canvas( tkinter.Frame ):
    """
    Frame containing map display, location searching box and enter/clear box for specifying location of interest.
    Used in the main window under the tab 'map'
    """

    def FX(self, lat, lng, zoom, centerX, centerY, mouseX, mouseY):
        """
        interpolating a point coordinate on a canvas (default 640x640) to latitude and longitude
        coordinate of center frame is used as a referencing point
        x, y as delta distance of input point to reference center point

        Args:
            lat (float): lat of the point
            lng (float): lng of the point
            zoom (int): the zoom level of the google map, details check Google Map API:
                        https://developers.google.com/maps/documentation/javascript/tutorial#zoom-levels
            centerX (float): x of the center point of the map in canvas coordinate
            centerY (float): y of the center point of the map in canvas coordinate
            mouseX (float): x of the mouse click point of the map in canvas coordinate
            mouseY (float): y of the mouse click point of the map in canvas coordinate

        Returns: mouseLatLng = {'lat':mouseLat,'lng':mouseLng}

        """
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
        """
        reverse interpolate a point coordinate of latitude and longitude to canvas xy coordinate
        coordinate of center frame is used as a referencing point
        x, y as delta distance of input point to reference center point

        Args:
            circlelat (float):
            circlelng (float):

        Returns: canvas xy coordinate

        """
        dlat = (circlelat - self.maxlat) / (self.minlat - self.maxlat)
        dlng = (circlelng - self.minlng) / (self.maxlng - self.minlng)
        x = self.canvas.canvasx( 0 ) + self.width * dlng
        y = self.canvas.canvasy( 0 ) + self.height * dlat
        return x, y

    def getaddress(self, lat, lng, location=None):
        """
        return url address for static map image by either provide lat lng or geocode a location name (self.location)

        Args:
            lat (float|None): center point lat for requesting static map
            lng (float|None): center point lng for requesting static map
            location (str|None): center location name

        Returns: url address of the static map

        """
        if (lat is None) and (lng is None) and (location is not None):
            locationnospaces = urllib.parse.quote( location )
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
        """
        return image from an url request

        Returns: image of tkinter.PhotoImage

        """
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
        """
        handle right click on the canvas map
        Args:
            event (tkinter.event): event on the tkinter.canvas

        Returns: None

        """
        x, y = self.canvas.canvasx( event.x ), self.canvas.canvasy( event.y )
        widget = event.widget
        scale = 156543.03392 * math.cos( self.lat * math.pi / 180 ) / math.pow( 2, self.zoom )

        aoi_point = self.FX( self.lat, self.lng, self.zoom, self.centerX, self.centerY, x,
                             y )

        self.aoi_append( aoi_point, x, y, scale, widget )

    def aoi_append(self, point, canvasx, canvasy, scale, widget):
        """
        proceed to append AOI after right clicking on the canvas
        for circle mode, the click point is regard as the
        circle center and radius is determined either by the web service (for eTransport) or default 500m (data.gov.hk)
        for polygon mode, the click point is treated as an vertex and the polygon is free-form by the vertice

        Args:
            point (dict[str, int]): dictionary of the latlng pair {'lat':lat,'lng':lng}
            canvasx (float): x of the canvas coordinate
            canvasy (float): y of the canvas coordinate
            scale (float): scale of the canvas map
            widget (tkinter.widget): canvas object to be add point

        Returns: None

        """
        pt = (point['lat'], point['lng'])

        if self.aoimode == 'Polygon':
            # end point of the line
            widget.create_oval( canvasx - 2, canvasy - 2, canvasx + 2, canvasy + 2, width=2, fill='red', outline='red' )
            if self.aoi[-1].type == 'Unclose':
                widget.create_line( *self.rev_FX( *self.aoi[-1].point[-1] ), canvasx, canvasy )
                self.aoi[-1].add_vertex( pt )
            else:
                self.aoi.append( AoiInstance( pt, 'Unclose', len( self.aoi ) ) )

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
            self.aoi.append( AoiInstance( pt, 'Circle', len( self.aoi ), radius ) )

    def close_polygon(self):
        """
        draw connecting line from end point to starting point and call aoi function close_polygon

        Returns: None

        """
        self.canvas.create_line( *self.rev_FX( *self.aoi[-1].point[0] ),
                                 *self.rev_FX( *self.aoi[-1].point[-1] ) )
        self.aoi[-1].close_polygon()

    def label_circle(self):
        """
        Set label button RAISED/SUNKEN
        """
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
        """
        Reload the canvas map with all self parameter

        Args:
            event ():
            mousex ():
            mousey ():

        Returns:

        """
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
                                             text='#%s\nlat=%s\nlon=%s\nradius=%s' % (
                                             marker.id, *marker.point[0], marker.radius),
                                             tags='CircleLabel' )
                else:
                    self.canvas.delete( 'CircleLabel' )

            elif marker.type == 'Polygon' or marker.type == 'Unclose':
                vertices = marker.point
                for id, val in enumerate( vertices ):
                    x, y = self.rev_FX( *marker.point[id] )
                    self.canvas.create_oval( x - 2, y - 2, x + 2, y + 2, width=2, fill='red', outline='red' )
                    if id == 0 and marker.type == 'Unclose':
                        pass
                    else:
                        self.canvas.create_line( *self.rev_FX( vertices[id - 1][0], vertices[id - 1][1] ),
                                                 *self.rev_FX( vertices[id][0], vertices[id][1] ) )
                if self.showlbl:
                    centroid = self.rev_FX( *np.mean( vertices, axis=0 ) )
                    self.canvas.create_text( centroid[0], centroid[1],
                                             text='#%s' % marker.id,
                                             tags='CircleLabel' )
                else:
                    self.canvas.delete( 'CircleLabel' )

        self.canvas.focus_set()
        self.window.update()

    def wheel(self, event):
        """
        zoom the map with the mouse wheel input
        """
        if event.num == 4 or event.delta == 120:
            self.zoom = self.zoom + 1
        elif event.num == 5 or event.delta == -120:
            self.zoom = self.zoom - 1
        self.reload()
        # mapimage = self.getmap()
        # self.canvas.itemconfig("map", image=mapimage)
        # self.window.mainloop()

    def search(self, event=None):
        """
        center the map the to location searched
        """
        self.location = self.varB.get()
        self.getaddress( None, None, self.location )
        self.reload()

    def to_read_html(self, event=None):
        """
        fetch the routes in the AOI from the website selected
        require function from read_html.py

        Args:
            event ():

        Returns:

        """

        # reset the previously loaded data
        self.window.route.clear()
        self.window.headway.clear()
        self.saves['saves'].clear()

        # prompt save setting for the processed routes
        if len( self.aoi ) > 1:
            popup = gui_popups.SaveSetting( aoi_nos=len( self.aoi ) )

        # check the return from save setting popup
        if popup.out['done'] > 0:
            self.save_cfg = popup.out
            # print( self.save_cfg )

            # progress bar setting
            self.window.progress.config( maximum=(len( self.aoi ) - 1) * 10 + 1, value=1 )
            self.window.headway['cursor'] = 'watch'
            marker_id = 1
            for marker in self.aoi:
                self.window.cprint('retriving routes in ' + marker.type + ' #' + str(marker_id - 1))

                savename = os.path.join(self.save_cfg['dirname'], 'Marker%s.csv' % (marker_id - 1)) if self.save_cfg[
                    'batch'] else ''
                if self.webMode == 'eTransport':
                    if marker.type == 'Circle':
                        self.saves['saves'].append(
                            read_html.routes_export_circle_mode( *marker.point[0], savename,
                                                                 self.save_cfg['showmap'] ) )
                        self.window.progress['value'] += 10
                    elif marker.type != 'Initiate':
                        if marker.type == 'Unclose':
                            self.close_polygon()
                        self.saves['saves'].append(
                            read_html.routes_export_polygon_mode( Polygon( marker.point ), savename,
                                                                  self.save_cfg['showmap'], self.window ) )
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
                    self.window.progress['value'] += 10
                marker_id += 1

                self.window.update()

            self.saves['dirname'] = os.path.dirname( self.saves['saves'][-1] )
            if self.save_cfg['consld']:
                self.saves['saves'].append( combine_routes.main( self.saves ) )
            self.window.route.update_list( self.saves )
            self.window.route.read_csv( self.saves['saves'][-1] )
            self.window.headway['cursor'] = 'arrow'
            self.window.tab_parent.select( self.window.route )

    def back(self, event=None):
        """
        Remove last AOI
        """
        if len( self.aoi ) > 1:
            del self.aoi[-1]
        self.reload()

    def clear(self, event=None):
        """
        Clear all AOI
        """
        self.aoi = [AoiInstance( (0, 0), 'Initiate', 0 )]
        self.reload()

    def web_list_handler(self, event=None, load=False):
        """
        handle changes in the datasource website dropdown list

        Args:
            load (bool): set the variable to be change, if true display text changes to internal self value, vice versa

        Returns:

        """
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
                # self.drawtoolhandler( None, 'Circle', 'eTrans' )
            else:

                tkinter.messagebox.showwarning( 'Warning',
                                                'data.gov.hk dataset supports bus stop only, gmb data is incomplete :(' )
                self.drawtoolhandler( None, self.aoimode )

    def drawtoolhandler(self, event=None, btn=None):
        """
        AOI mode handler, can specify AOI in circles or free-draw polygon
        Args:
            btn (str): the aoi button activated

        Returns:

        """
        self.btnD2.config( state="normal" )
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
        """
        Layout of the frame canvas map tab
        """
        tkinter.Frame.__init__( self, notebook, width=window.width + 100, height=window.height + 50,
                                bg='#2ea8ce' )
        self.name = 'frame_canvas'
        self.window = window
        self.zoom = 12
        self.location = "Hong Kong"
        self.api = 'AIzaSyCpZMD9JKcb3bfDRC7xE2H6oBp-DhDv4s8'
        self.lat = 22.305349
        self.lng = 114.171598
        self.minlat, self.maxlat, self.minlng, self.maxlng = None, None, None, None
        self.width = window.width
        self.height = window.height
        self.centerX = window.width / 2
        self.centerY = window.height / 2

        self.aoi = [AoiInstance( (0, 0), 'Initiate', 0 )]
        web_name = ['data.gov.hk', 'eTransport']
        self.aoimode = 'Polygon'
        self.webMode = web_name[1]
        self.showlbl = False
        self.s = requests.Session()
        self.save_cfg = {'batch': True, 'consld': True, 'dirname': '',
                         'map': False, 'done': 0}
        self.saves = {'saves': [''], 'dirname': None}

        self.frmCanvas = tkinter.Frame( self, width=window.width, height=window.height, bg='green', cursor='tcross' )
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

        guide = tkinter.Message( self.frmD, text='Right click on the map to add interested area', bg='white' )
        guide.pack()

        sep = tkinter.Frame( self.frmD, width=80, height=60, bg='azure' )
        sep.pack()
        self.btnD3 = tkinter.Button( self.frmD, text='Close\nPolygon', command=self.close_polygon )
        self.btnD3.config( state="disabled" )
        self.btnD3.pack( fill='x' )

        self.btnD4 = tkinter.Button( self.frmD, text='Show AOI\nDetails', command=self.label_circle )
        self.btnD4.pack( fill='x' )

        self.drawtoolhandler( btn=self.aoimode )

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
