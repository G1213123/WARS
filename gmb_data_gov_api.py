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
        for idx, direction in enumerate( seq['direction'] ):
            for period in direction['headways']:
                weekday_check = any( period['weekdays'][0:4] )
                am_check = gn.time_in_period( p_start, p_end, self.am1, self.am2 )
                fit_criteria =
                if 'Mondays' in val:
                    period = seq[idx + 1]
                    if '-' in period:
                        # handle when a frequency in a fixed time period was given
                        headway = self.timetable.iloc[idx + 1][2]
                        p_start = datetime.datetime.strptime( period.split( ' - ' )[0], '%I:%M %p' ).time()
                        p_end = datetime.datetime.strptime( period.split( ' - ' )[1], '%I:%M %p' ).time()
                        if gn.time_in_period( p_start, p_end, self.am1, self.am2 ):
                            self.PT.iloc[-1]['headway_am'] = headway
                            self.PT.iloc[-1]['period_am'] = period
                        if gn.time_in_period( p_start, p_end, self.pm1, self.pm2 ):
                            self.PT.iloc[-1]['headway_pm'] = headway
                            self.PT.iloc[-1]['period_pm'] = period
                    else:
                        # handle when a list of exact departure time was given
                        min_headway1 = ' '
                        min_headway2 = ' '
                        freq1 = 0
                        freq2 = 0
                        for t in temp[1:]:
                            time = datetime.datetime.strptime( t, '%I:%M %p' ).time()
                            if gn.time_in_period( time, time, self.am1,
                                                  self.am2 ):
                                freq1 += 1
                                min_headway1 += t
                                min_headway1 += ' '
                                self.PT.iloc[-1]['period_am'] = time
                            if gn.time_in_period( time, time, self.pm1,
                                                  self.pm2 ):
                                freq2 += 1
                                min_headway2 += t
                                min_headway2 += ' '
                                self.PT.iloc[-1]['period_pm'] = time

                        if freq1 == 1:
                            self.PT.iloc[-1]['headway_am'] = min_headway1 + '(' + str( freq1 ) + ' trip only)'
                        elif freq1 > 1:
                            self.PT.iloc[-1]['headway_am'] = min_headway1 + '(' + str( freq1 ) + ' trips only)'

                        if freq2 == 1:
                            self.PT.iloc[-1]['headway_pm'] = min_headway2 + '(' + str( freq2 ) + ' trip only)'
                        elif freq2 > 1:
                            self.PT.iloc[-1]['headway_pm'] = min_headway2 + '(' + str( freq2 ) + ' trips only)'
            self.PT.iloc[-1]['route'] = self.j
            self.PT.iloc[-1]['info'] = self.info.replace( '<->', '-' )
            self.PT.iloc[-1]['bound'] = seq

    # tango='88'

    def main(self):
        tango, savename = gn.read_route( self.route, self.savename )

        self.PT = pd.DataFrame(
            columns=['route', 'info', 'headway_am', 'headway_pm', 'bound', 'period_am', 'period_pm'] )

        for j in tango:  # j='61S'
            self.j = j
            print( j )
            param = dict( region=DIST_DICT[self.dist], route_code=j )
            request_url = 'https://data.etagmb.gov.hk/route/{region}/{route_code}'.format( **param )
            get_json = requests.get( request_url )
            data = get_json.json()['data']

            for seq in data:
                self.read_data( seq )

            if self.window is not None:
                self.window.headway['cursor'] = 'watch'
                self.window.progress['value'] += 1
                self.window.cprint( 'retriving headway data of route ' + self.j )
                self.window.update()
        self.window.headway['cursor'] = 'arrow'
        self.PT.to_excel( savename )


if __name__ == "__main__":
    gmb_get_headway( ['69'], dist='h', savename='test\\test.csv', am1=7, am2=8, pm1=17, pm2=18 )
