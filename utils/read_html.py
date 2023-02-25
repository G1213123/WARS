# -*- coding: utf-8 -*-
"""
Reading the HKeMobility web layer of PT services (Bus and GMB) and extract the bus stop for searching of routes

Created on Tue Sep 10 15:37:31 2019

@author: Andrew.WF.Ng
"""
import json
import urllib.request

import folium
import geopandas as gpd
import html2text
import numpy as np
import pandas as pd
import requests
import streamlit as st
from geopy.distance import geodesic
from shapely.geometry import Polygon, Point, shape

COOKIES = dict( language='en' )
HEADERS = dict( referer='https://www.hkemobility.gov.hk/en/route-search/pt' )


class map_html:
    '''
    Export a Web based map using folium module for logging the assessed area
    '''

    def __init__(self, **kwargs):

        self.__dict__.update( kwargs )
        # folium.LayerControl().add_to( self.m )
        self.map_stop()
        self.map_aoi()

    def map_stop(self):
        '''
        Adding markers for bus stops in the aoi
        '''
        for key, b_stop in self.stops.iterrows():
            for type in ['GMB', 'BUS']:
                color = 'green' if type == 'GMB' else 'red'
                if b_stop[type] != '':
                    description = folium.Popup(
                        html='<b>#' + str( b_stop['STOP_ID'] ) + '</b><br><font size="4">'
                             + b_stop['NAME']
                             + '</font><br><i> lat=%s lon=%s </i>' % (b_stop.bbox[1], b_stop.bbox[0])
                             + '<br><font size="2"><b>%s (%s): </b>%s' % (
                                 type, b_stop[type].count( ',' ) + 1, b_stop[type]) + '</font>', max_width=1500 )
                    st.session_state['markers'].append(
                        folium.Marker( location=[b_stop.bbox[1], b_stop.bbox[0]], radius=5,
                                       popup=description, icon=folium.Icon( color=color ) ) )

    def map_aoi(self):
        '''
        Adding area polygon to the map
        '''
        if isinstance( self.aoi, Polygon ):
            loc_list = list( self.aoi.exterior.coords )
            st.session_state['shapes'].append(
                folium.Polygon( loc_list, color='#3186cc', fill_color='#3186cc' ) )
        elif isinstance( self.aoi, Point ):
            st.session_state['shapes'].append(
                folium.Circle( [self.aoi.x, self.aoi.y], radius=self.radius, color='#3186cc',
                               fill_color='#3186cc' ) )
        # popup=str( self.radius ) + 'm lat=%s lon=%s' % (self.aoi.x, self.aoi.y),


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


def get_stops(bbox, type):
    """
    get the bus/gmb ... stops from eTransport
    :param bbox: boundary box of the searching area
    :param type: type of stops in ['BUS', 'GMB']
    :return:
    """
    url = r'https://www.hkemobility.gov.hk/api/drss/layer/map/'
    # https://www.hkemobility.gov.hk/api/drss/layer/map/?typeName=DRSS%3AVW_HKET_PTS_BUS_EN&service=WFS&version=1.0.0&request=GetFeature&outputFormat=application%2Fjson&bbox=114.16481498686883%2C22.28951336041544%2C114.17698148696039%2C22.300591641174478
    params = dict( typeName='DRSS:VW_HKET_PTS_%s_EN' % type, service='WFS',
                   version='1.0.0',
                   request='GetFeature',
                   outputFormat='application/json',
                   bbox='%s,%s,%s,%s' % (bbox[1], bbox[0], bbox[3], bbox[2]) )
    r = requests.post( url, params=params, cookies=COOKIES, headers=HEADERS )
    xhtml = json.loads( r.text )

    if len( xhtml['features'] ) > 0:
        stops = pd.DataFrame( xhtml['features'] )
        stops['geometry'] = stops['geometry'].apply( lambda x: shape( x ) )
        stops['geometry'] = stops['geometry'].apply( lambda z: Point( z.y, z.x ) )
    else:
        return pd.DataFrame()

    return stops


def routes_from_stops(stops):
    """
    Request PT routes details from the stops provided

    Args:
        stops (pd.DataFrame): DataFrame containing the stops details
                                columns = ['type', 'id', 'geometry', 'geometry_name', 'properties']

    Returns:
        stops (pd.DataFrame): DataFrame containing the stops details
                                columns = ['type', 'id', 'geometry', 'geometry_name', 'properties', 'BUS', 'GMB']
        routes (pd.DataFrame): DataFrame containing the routes list
                                columns = ['Route', 'Service Provider', 'Origin', 'Destination']
    """

    columns = ['Route', 'Service Provider', 'Origin', 'Destination']
    routes = pd.DataFrame( columns=columns )
    stops = stops.reindex( columns=['type', 'id', 'geometry', 'geometry_name', 'properties', 'BUS', 'GMB'],
                           fill_value='' )
    for id, stop in stops.iterrows():
        stop_id = stop['properties']['STOP_ID']
        stop_type = stop['id'].split( '_' )[3]
        url = 'https://www.hkemobility.gov.hk/api/drss/getTextInfo/%s/en/%s' % (stop_type, stop_id)

        r = requests.get( url, cookies=COOKIES, headers=HEADERS )
        xhtml = r.text
        try:
            route = pd.DataFrame( json.loads( xhtml ) ).iloc[:, 2:6]
            route = route.set_axis( columns, axis=1 )
        except (json.decoder.JSONDecodeError, ValueError):
            print( "invalid string ", xhtml )
            route = None
        routes = pd.concat( [routes, route] )

        # Assign Routes to corresponding stops
        bus = ['KMB', 'CTB', 'NWFB', 'NLB', 'LWB']
        if route is not None:
            if stop_type == 'GMB':
                stops['GMB'][id] = route[route["Service Provider"] == "GMB"]["Route"].drop_duplicates().to_string(
                    header=False, index=False ).replace( '\n', ',' ).replace( 'Series([], )', '' ).replace( ' ', '' )
            else:
                stops['BUS'][id] = \
                    route[route["Service Provider"].str.contains( r'\b(?:{})\b'.format( '|'.join( bus ) ) )][
                        "Route"].drop_duplicates().to_string(
                        header=False, index=False ).replace( '\n', ',' ).replace( 'Series([], )', '' ).replace( ' ',
                                                                                                                '' )
                # print(routes)
    routes = routes.drop_duplicates()
    return routes, stops


def catch_stops_in_polygon(stop, polygon, radius=500, point2=None):
    try:
        if point2:
            point2 = (point2.x, point2.y)
            return geodesic( stop, point2 ).m < radius
        else:
            return stop.within( polygon )
    except (ValueError, IndexError) as e:
        return False


def routes_export_polygon_mode(polygon):
    services_type = ['BUS', 'GMB']

    polygongdf = gpd.GeoDataFrame( index=[0], geometry=[polygon], crs={'init': 'epsg:4326'} )
    bbox = polygongdf.total_bounds  # lat-long of 2 corners

    stops = pd.DataFrame()
    for service in services_type:
        stops = pd.concat( [stops, get_stops( bbox, service )], ignore_index=True )

    stops = stops[stops.apply( lambda x: catch_stops_in_polygon( x['geometry'], polygon ), axis=1 )]
    routes, stops = routes_from_stops( stops )

    # Formatting
    stops = pd.concat( [stops['properties'].apply( pd.Series ), stops['BUS'], stops['GMB']], axis=1 )
    stops[' '] = ""  # padding for display
    if 'STOP_ID' in stops.columns:
        stops['STOP_ID'] = stops['STOP_ID'].apply( str )
        stops['NAME'] = stops['NAME'].apply( html2text.html2text )

        map_html( stops=stops, aoi=polygon, )
    else:
        stops = pd.DataFrame()

    return routes, stops


def get_nearby_stops_html(y, x):
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
    :param xhtml: html text retrieved
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


def routes_export_circle_mode(x, y, radius, m):
    """
    legacy route searching function by mannual input target location in lat lon format with search radius
    :param x: latitude of target
    :param y: longitude of target
    :param savename: savename input, if none is provided, open a file choosing prompt
    :param show: show the map of the target location
    :return: exported file path
    """
    routes = html_to_table()
    stops = []
    for services_type in range( 1, 3 ):
        stops = stops + get_stops( x, y, services_type )
    stops = list( dict.fromkeys( stops ) )  # remove duplicated stops
    stops = list( filter( lambda z: catch_stops_in_polygon( z, None, radius, Point( x, y ) ), stops ) )
    xx, stops = routes_from_stops( stops )

    # m = folium.Map( location=[x, y], zoom_start=20, tiles='https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
    #                attr="<a href=https://github.com/G1213123/WARS>WARS</a>" )
    # folium.Circle( [x, y], radius=radius, popup=str( radius ) + 'm lat=%s lon=%s' % (x, y), color='#3186cc',
    #               fill_color='#3186cc' ).add_to( m )
    # m.save( savename.replace( '.csv', '.html' ), 'a' )

    map_html( m=m, stops=stops, aoi=Point( x, y ), radius=radius )

    return routes, stops
