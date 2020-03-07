import pandas as pd
import requests
from io import StringIO
import os
from shapely.geometry import Point
from shapely.geometry.polygon import Polygon
import folium
import geopandas as gpd
import webbrowser
import pyproj

# pointer for temp. loading of database
global cache


class map_gov:
    '''
    Creating a Web based map using folium module for logging the assessed area
    '''
    def __init__(self, **kwargs):
        '''
        Define base map with area centroid focused
        '''
        self.__slots__ = ['stops', 'aoi']
        self.__dict__.update( kwargs )

        centroid = self.aoi.centroid
        self.m = folium.Map( location=[centroid.x, centroid.y], zoom_start=20, tiles='OpenStreetMap' )
        self.map_stop()
        self.map_aoi()

        self.m.save( 'test.html' ) # save path to be finalized

        if True:
            webbrowser.open( 'test.html' )

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
        polygon_geom = gpd.GeoDataFrame( index=[0], geometry=[self.aoi] )
        polygon_geom.crs = {'init': 'epsg:4326'}
        folium.GeoJson( polygon_geom ).add_to( self.m )


def pt_in_polygon(x, y, polygon):
    '''
    Check a point in a polygon
    '''
    return polygon.contains( Point( x, y ) )

class data_gov:
    '''
    A frame work for searching of bus stop data using data.gov.hk as data source
    For documentation of source data format, see https://static.data.gov.hk/td/pt-headway-en/dataspec/ptheadway_dataspec.pdf
    Data is pre-cached in a cache folder if it is first time setup for subsequential query
    Bus Stop Data querying can be in form of field value or location filtering. See read_by_field and 
        read_by_loc respectively
    Route list querying is presumed to be according to given area. See ruote_query
    '''
    def __init__(self):
        '''
        Check first time setup
        if file not exist, download the file as cache for later operations
        '''
        self.cache_path = os.path.expanduser('~/Documents/Python_Scripts/WARS/cache')
        self.fields=['stops', 'stop_times', 'trips', 'routes']
        url='https://static.data.gov.hk/td/pt-headway-en/'
        cache={}

        if not os.path.exists(self.cache_path):
            os.makedirs(self.cache_path)

        for f in self.fields:
            if not os.path.exists(self.d_path(f)):
                g = requests.get(url+f+'.txt').content
                cache[f] = pd.read_csv( StringIO( g.decode( 'utf-8' ) ) )
                cache[f].to_csv(self.d_path(f))

    def d_path(self, f):
        return os.path.join(self.cache_path, f+'.csv')

                
    def read(self, f):
        cache = pd.read_csv( self.d_path( f ), index_col=0 )
        return cache

    def read_by_field(self, f, field, value):
        cache = pd.read_csv( self.d_path( f ), index_col=0 )
        cache = cache[cache[field].isin( value )]
        return cache

    def read_by_loc(self, polygon):
        cache = self.read( 'stops' )
        cache = cache[cache.apply( lambda x: pt_in_polygon( x['stop_lat'], x['stop_lon'], polygon ), axis=1 )]
        return cache

    def route_query_id(self, stop):
        cache = self.read_by_field( 'stops', 'stop_id', stop )
        cache=cache.merge(self.read('stop_times'), on='stop_id', how='left')
        cache=cache.merge(self.read('trips'), on='trip_id', how='left')
        cache = cache.merge( self.read( 'routes' ), on='route_id', how='left' )
        return cache

if __name__ == '__main__':
    polygon = Polygon( [(22.322304, 114.188933), (22.322709, 114.190472), (22.320541, 114.189943)] )
    g=data_gov()
    d = g.read_by_loc( polygon )
    e = g.route_query_id( d['stop_id'] )
    f = map_gov( stops=d, aoi=polygon )
    q=1
