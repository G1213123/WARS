"""
GMB headway data from data.gov.hk
https://data.etagmb.gov.hk/static/GMB_ETA_API_Specification.pdf
"""
import datetime

import pandas as pd
import requests

import general as gn

DIST_DICT = {'h': 'HKI', 'k': 'KLN', 'n': 'NT'}


class gmb_get_headway:
    """
    Extract gmb headway data from the html page
    """

    def __init__(self, route, dist='n', savename=None, window=None, archive=None, **kwargs):
        # all **kwargs keys will be initialized as class attributes
        allowed_keys = {'am1', 'am2', 'pm1', 'pm2'}
        # initialize all allowed keys to false
        self.__dict__.update( (key, False) for key in allowed_keys )
        # and update the given keys by their given values
        self.__dict__.update( (key, value) for key, value in kwargs.items() if key in allowed_keys )
        self.route = route
        self.dist = dist
        self.savename = savename
        self.archive = archive
        self.window = window
        self.main()
        self.__dict__.update( kwargs )

    def read_data(self, seq):
        self.PT = self.PT.append( pd.Series(), ignore_index=True )
        print( self.j )
        if self.window:
            self.window.headway['cursor'] = 'watch'
            self.window.cprint( 'Connecting to Gov Data web service' )
        for idx, direction in enumerate( seq['directions'] ):
            for period in direction['headways']:
                weekday_check = any( period['weekdays'][0:5] )
                if weekday_check:
                    # handle when a frequency in a fixed time period was given
                    headway = period['frequency']
                    if headway is None: headway = '1 trip only'
                    p_start = datetime.datetime.strptime( period['start_time'], '%H:%M:%S' ).time()
                    p_end = datetime.datetime.strptime( period['end_time'], '%H:%M:%S' ).time()
                    if gn.time_in_period( p_start, p_end, self.am1, self.am2 ):
                        self.PT.iloc[-1]['headway_am'] = headway
                        self.PT.iloc[-1]['period_am'] = period['start_time'] + ' - ' + period['end_time']
                    if gn.time_in_period( p_start, p_end, self.pm1, self.pm2 ):
                        self.PT.iloc[-1]['headway_pm'] = headway
                        self.PT.iloc[-1]['period_pm'] = period['start_time'] + ' - ' + period['end_time']
            self.PT.iloc[-1]['route'] = self.j
            self.PT.iloc[-1]['info'] = direction['orig_en'] + ' - ' + direction['dest_en']
            self.PT.iloc[-1]['bound'] = direction['route_seq']

    # tango='88'

    def main(self):
        tango, savename = gn.read_route( self.route, self.savename )

        self.PT = pd.DataFrame(
            columns=['route', 'info', 'headway_am', 'headway_pm', 'bound', 'period_am', 'period_pm', 'Remarks'] )

        for j in tango:  # j='61S'
            self.j = j
            print( j )
            param = dict( region=DIST_DICT[self.dist], route_code=j )
            request_url = 'https://data.etagmb.gov.hk/route/{region}/{route_code}'.format( **param )
            get_json = requests.get( request_url )
            data = get_json.json()['data']

            for seq in data:
                self.read_data( seq )
                self.PT.iloc[-1]['Remarks'] = seq['description_en']

            if self.window is not None:
                self.window.headway['cursor'] = 'watch'
                self.window.progress['value'] += 1
                self.window.cprint( 'retriving headway data of route ' + self.j )
                self.window.update()
        if self.window: self.window.headway['cursor'] = 'arrow'
        self.PT.to_csv( savename )


if __name__ == "__main__":
    gmb_get_headway( ['69'], dist='h', savename='test.csv', am1=7, am2=8, pm1=17, pm2=18 )
