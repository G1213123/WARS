import pandas as pd
import requests
from io import StringIO
import os

global cache

class data_gov:
    def __init__(self):
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
            cache = pd.read_csv( self.d_path(f), index_col=0)
            return cache

    def read_filter(self, f, field, value):
            cache = pd.read_csv( self.d_path(f), index_col=0)
            cache=cache[cache[field]==value]
            return cache

    def route_query(self, stop):
        cache=self.read_filter('stops', 'stop_id', stop)
        cache=cache.merge(self.read('stop_times'), on='stop_id', how='left')
        cache=cache.merge(self.read('trips'), on='trip_id', how='left')
        cache = cache.merge( self.read( 'routes' ), on='route_id', how='left' )
        return cache

if __name__ == '__main__':
    g=data_gov()
    d = g.route_query(453)

    q=1