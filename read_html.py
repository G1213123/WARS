# -*- coding: utf-8 -*-
"""
Created on Tue Sep 10 15:37:31 2019

@author: Andrew.WF.Ng
"""
import tkinter as tk
import urllib.request
import webbrowser
from tkinter import *
from tkinter.filedialog import asksaveasfilename

import folium
import geopandas as gpd
import numpy as np
import pandas as pd
import requests
from bs4 import BeautifulSoup
from matplotlib.patches import RegularPolygon
from shapely.geometry import Polygon, Point


class App():
    def __init__(self, master):
        self.display_button_entry( master )
        self.x = 960
        # self.y=0

    def setup_window(self, master):
        self.f = tk.Frame( master, height=480, width=640, padx=10, pady=12 )
        self.f.pack_propagate( 0 )

    def display_button_entry(self, master):
        self.setup_window( master )
        v = tk.StringVar()
        self.e = tk.Entry( self.f, textvariable=v )
        u = tk.StringVar()
        self.d = tk.Entry( self.f, textvariable=u )
        buttonA = tk.Button( self.f, text="Cancel", command=self.cancelbutton )
        buttonB = tk.Button( self.f, text="OK", command=self.okbutton )
        labelx = tk.Label( self.f, text='lat' )
        labely = tk.Label( self.f, text='lon' )
        # self.var1 = IntVar()
        # self.var1.set(0)
        # self.cbus = tk.Checkbutton(self.f, text="bus", variable=self.var1, onvalue=1, offvalue=0)

        labelx.pack()
        self.e.pack()
        labely.pack()
        self.d.pack()
        buttonA.pack()
        buttonB.pack()
        # self.cbus.pack()
        self.f.pack()

    def cancelbutton(self):
        print( self.e.get() )
        master.destroy()

    def okbutton(self):
        print( self.e.get() )
        print( self.d.get() )
        x = self.e.get()
        y = self.d.get()
        # bus=self.var1
        routes_export_circle_mode( x, y )
        master.destroy()
        return 0

    def _close(self):
        master.destroy()


class map_html:
    '''
    Creating a Web based map using folium module for logging the assessed area
    '''

    def __init__(self, **kwargs):
        '''
        Define base map with aoi centroid focused
        '''
        self.__slots__ = ['stops', 'aoi', 'radius', 'savename']
        self.__dict__.update( kwargs )

        centroid = self.aoi.centroid
        self.m = folium.Map( location=[centroid.x, centroid.y], zoom_start=20, tiles='OpenStreetMap' )
        self.map_stop()
        self.map_aoi()

        self.m.save( self.savename )

        if True:
            webbrowser.open( self.savename )

    def map_stop(self):
        '''
        Adding markers for bus stops in the aoi
        '''
        for key, b_stop in self.stops.iterrows():
            description = folium.Popup( html='<b>#' + str( key ) + '</b><br><font size="4">' + str(
                b_stop['stop_name'] ) + '</font><br><i> lat=%s lon=%s </i>'
                                             % (b_stop.stop_lat, b_stop.stop_lon), max_width=300 )
            folium.Marker( location=[b_stop.stop_lat, b_stop.stop_lon], radius=10,
                           popup=description, color='#3186cc', fill_color='#3186cc' ).add_to( self.m )

    def map_aoi(self):
        '''
        Adding area polygon to the map
        '''
        if isinstance( self.aoi, Polygon ):
            loc_list = list( self.aoi.exterior.coords )
            folium.Polygon( loc_list, popup=str( loc_list ), color='#3186cc', fill_color='#3186cc' ).add_to( self.m )
        elif isinstance( self.aoi, Point ):
            folium.Circle( [self.aoi.x, self.aoi.y], radius=self.radius,
                           popup=str( self.radius ) + 'm lat=%s lon=%s' % (self.aoi.x, self.aoi.y), color='#3186cc',
                           fill_color='#3186cc' ).add_to( self.m )


def haversine(coord1, coord2):
    # Coordinates in decimal degrees (e.g. 43.60, -79.49)
    lon1, lat1 = coord1
    lon2, lat2 = coord2
    R = 6371000  # radius of Earth in meters
    phi_1 = np.radians( lat1 )
    phi_2 = np.radians( lat2 )
    delta_phi = np.radians( lat2 - lat1 )
    delta_lambda = np.radians( lon2 - lon1 )
    a = np.sin( delta_phi / 2.0 ) ** 2 + np.cos( phi_1 ) * np.cos( phi_2 ) * np.sin( delta_lambda / 2.0 ) ** 2
    c = 2 * np.arctan2( np.sqrt( a ), np.sqrt( 1 - a ) )
    meters = R * c  # output distance in meters
    km = meters / 1000.0  # output distance in kilometers
    meters = round( meters )
    km = round( km, 3 )
    return meters


def get_stops(y, x, type):
    """
    get the bus/gmb stop from eTransport
    default radius of stop fetching is 1000m from the target
    :param y: lat of the target
    :param x: lon of the target
    :param type: type of stops, 1 for bus, 2 for gmb
    :return:
    """
    url = r'https://www.hkemobility.gov.hk/loadptstop.php?type=%s&lat=%s&lon=%s' % (type, y, x)
    # https://www.hkemobility.gov.hk/loadptstop.php?type=2&lat=22.300230999999982&lon=114.172954&sysid=2 TST

    cookies = dict( LANG='EN' )
    r = requests.post( url, cookies=cookies )
    xhtml = r.text

    soup = BeautifulSoup( xhtml, 'html.parser' )
    json_string = soup.find( "iframe" )['onload'].replace( '\n', '' ).replace( '\t', '' )
    try:
        value = json_string.split( ';' )[0].strip( 'mapLayerPtStr = ' ).strip( '\'' )
    except ValueError:
        print( "invalid string", json_string )
        return ''
    else:
        stops = value.split( '|*|' )
        print( stops )
        return stops


def routes_from_stops(stops, window):
    routes = []
    for stop in stops:
        if stop is not '':
            stop_info = stop.split( '||' )
            type = stop_info[3]
            stopid = stop_info[4]
            url = 'https://www.hkemobility.gov.hk/getstopinfo.php?type=%s&stopid=%s' % (type, stopid)

            cookies = dict( LANG='EN' )
            r = requests.post( url, cookies=cookies )
            xhtml = r.text
            routes.append( html_to_table( xhtml, 1 ) )
            # print(routes)
        if window is not None:
            window.progress['value'] += (10 / len( stops ))
            window.update()
    routes = pd.concat( routes, ignore_index=True )
    routes = routes.drop_duplicates()
    return routes


def catch_stops_in_polygon(stop_str, polygon):
    try:
        point = Point( float( stop_str.split( '||' )[1] ), float( stop_str.split( '||' )[0] ) )
    except (ValueError, IndexError) as e:
        return False
    else:
        return point.within( polygon )


def routes_export_polygon_mode(polygon, savename='', show=False, window=None):
    polygongdf = gpd.GeoDataFrame( index=[0], geometry=[polygon], crs={'init': 'epsg:4326'} )
    xmin, ymin, xmax, ymax = polygongdf.total_bounds  # lat-long of 2 corners
    EW = haversine( (xmin, ymin), (xmax, ymin) )  # East-West extent of Toronto = 42193 metres
    NS = haversine( (xmin, ymin), (xmin, ymax) )  # North-South extent of Toronto = 30519 metres
    d = 2000  # diamter of each hexagon in the grid = 900 metres
    w = d * np.sin( np.pi / 3 )  # horizontal width of hexagon = w = d* sin(60)
    n_cols = int( EW / w ) + 1  # Approximate number of hexagons per row = EW/w
    n_rows = int( NS / d ) + 1  # Approximate number of hexagons per column = NS/d

    w = (xmax - xmin) / n_cols  # width of hexagon
    d = w / np.sin( np.pi / 3 )  # diameter of hexagon
    array_of_hexes = []
    for rows in range( 0, n_rows ):
        hcoord = np.arange( xmin, xmax, w ) + (rows % 2) * w / 2
        vcoord = [ymax - rows * d * 0.75] * n_cols
        for x, y in zip( hcoord, vcoord ):  # , colors):
            hexes = RegularPolygon( (x, y), numVertices=6, radius=d / 2 )
            verts = hexes.get_path().vertices
            trans = hexes.get_patch_transform()
            points = trans.transform( verts )
            if Polygon( points ).intersects( polygon ):
                array_of_hexes.append( Polygon( points ) )

    stops = []
    for pts in array_of_hexes:
        for services_type in range( 1, 3 ):
            stops = stops + get_stops( pts.centroid.x, pts.centroid.y, services_type )

    stops = list( dict.fromkeys( stops ) )  # remove duplicated stops
    stops = list( filter( lambda x: catch_stops_in_polygon( x, polygon ), stops ) )
    routes = routes_from_stops( stops, window )

    if savename == '':
        # File path prompt
        Tk().withdraw()  # we don't want a full GUI, so keep the root window from appearing
        savename = asksaveasfilename( defaultextension=".csv", title="save file",
                                      filetypes=(("comma seperated values", "*.csv"), ("all files", "*.*")) )
    routes.to_csv( savename )

    m = folium.Map( location=[x, y], zoom_start=20, tiles='https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
                    attr="<a href=https://github.com/G1213123/WARS>WARS</a>" )
    folium.Polygon( polygon.exterior.coords ).add_to( m )
    m.save( savename.replace( '.csv', '.html' ), 'a' )

    if show:
        webbrowser.open( savename.replace( '.csv', '.html' ) )

    return savename


def get_html(y, x):
    url = r'https://www.hkemobility.gov.hk/getnearby.php?dist=500&lat=%s&lon=%s&golang=EN' % (y, x)
    # url = http://www.hkemobility.gov.hk/getnearby.php?dist=1000&lat=22.33236511796521&lon=114.18292213964844&sysid=6

    req = urllib.request.Request( url )
    f = urllib.request.urlopen( req )
    xhtml = f.read().decode( 'utf-8' )

    radius = int( xhtml.split( 'sys_nearby_radius=', 1 )[1][:4].replace( ';', '' ) )

    return xhtml, radius


def html_to_table(xhtml, header=2):
    """
    organize the html page to a dataframe
    :param xhtml: html text retrived
    :param header: header row to be skipped
    :return: routes dataframe with columns ['Service Provider', 'Route', 'Origin', 'Destination']
    """
    tables = pd.read_html( xhtml )

    del tables[0:header]
    routes = pd.concat( tables )
    routes = routes.fillna( method='bfill' )
    routes.reset_index( inplace=True, drop=True )
    routes = routes[routes.index % 2 == 0]
    routes.columns = ['Origin', 'route_no', 'Destination']
    routes.reset_index( inplace=True, drop=True )

    routes[['Service Provider', 'Route']] = routes.route_no.str.split( n=1, expand=True )
    routes = routes[['Service Provider', 'Route', 'Origin', 'Destination']]
    # routes=routes.drop_duplicates()

    '''
    gmb=routes[routes['Service Provider']=='GMB']
    gmb=gmb.drop_duplicates(['Route'])
    '''
    return routes


def routes_export_circle_mode(x, y, savename='', show=False):
    """
    legacy route searching function by mannual input target location in lat lon format
    :param x: latitude of target
    :param y: longitude of target
    :param savename: savename input, if none is provided, open a file choosing prompt
    :param show: show the map of the target location
    :return: exported file path
    """
    xhtml, radius = get_html( x, y )
    routes = html_to_table( xhtml )

    if savename == '':
        # File path prompt
        Tk().withdraw()  # we don't want a full GUI, so keep the root window from appearing
        savename = asksaveasfilename( defaultextension=".csv", title="save file",
                                      filetypes=(("comma seperated values", "*.csv"), ("all files", "*.*")) )
    routes.to_csv( savename )

    m = folium.Map( location=[x, y], zoom_start=20, tiles='https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
                    attr="<a href=https://github.com/G1213123/WARS>WARS</a>" )
    folium.Circle( [x, y], radius=radius, popup=str( radius ) + 'm lat=%s lon=%s' % (x, y), color='#3186cc',
                   fill_color='#3186cc' ).add_to( m )
    m.save( savename.replace( '.csv', '.html' ), 'a' )

    if show:
        webbrowser.open( savename.replace( '.csv', '.html' ) )

    return savename


if __name__ == "__main__":
    master = tk.Tk()
    master.title('Location')
    master.resizable(width=tk.NO, height=tk.NO)
    app = App(master)
    master.mainloop()
