# -*- coding: utf-8 -*-
"""
Created on Mon Sep 23 15:52:12 2019

@author: Andrew.WF.Ng
"""

# http://www.16seats.net/chi/gmb/gh_2.html

import datetime

import pandas as pd
import requests
from bs4 import BeautifulSoup
from requests.structures import CaseInsensitiveDict

from utils import general as gn


class SearchGMB:
    """
    Search the GMB file within the local archived gmb route html pages
    """

    def __init__(self, route_num, dist):
        self.route_num = route_num
        self.dist = dist
        self.dist_dict = {'h': 'HKI', 'k': 'KLN', 'n': 'NT'}
        # self.f = self.load_gmb_data()

    def load_gmb_data(self, dist=None, data=None, trial=0):
        url = 'https://www.hkemobility.gov.hk/api/em'
        header = CaseInsensitiveDict()
        header["referer"] = "https://www.hkemobility.gov.hk/en/route-search/pt"
        header["Content-Type"] = "application/json"
        if dist is None:
            dist = self.dist
        if data is None:
            data = '{"api":"getrouteinfo7","param":{"lang":"EN","route_name":"%s","company_index":"-2",' \
                   '"region":"%s","mode":"","stop_type":""}}' % (self.route_num, self.dist_dict[dist])
        fail = 0
        f = requests.post(url, data=data, headers=header)
        if 'ROUTE_LIST' in f.json():
            for route in f.json()['ROUTE_LIST']:
                if route['ROUTE_REAL_NAME'] == str(self.route_num):
                    f = route['HYPERLINK']
        else:
            print(str(self.route_num) + ' is not a ' + self.dist_dict[dist] + ' route')
            if trial == 3:
                return None
            else:
                dist = list(self.dist_dict)[(list(self.dist_dict).index(dist) + 1) % 3]
                f = self.load_gmb_data(dist, None, trial + 1)
        return f


class gmb_get_headway:
    """
    Extract gmb headway data from the html page
    """

    def __init__(self, route, dist='n', progress=None, **kwargs):
        # all **kwargs keys will be initialized as class attributes
        allowed_keys = {'am1', 'am2', 'pm1', 'pm2', 'day_type'}
        # initialize all allowed keys to false
        self.__dict__.update( (key, False) for key in allowed_keys )
        # and update the given keys by their given values
        self.__dict__.update( (key, value) for key, value in kwargs.items() if key in allowed_keys )
        self.route = route
        self.dist = dist
        self.progress = progress
        self.main()
        self.__dict__.update(kwargs)

    def html_parse(self, bound):
        temp = self.timetable.iloc[:, 0]
        print( self.j )
        day_type = {'weekday': 'Monday',
                    'saturday': 'Saturday',
                    'holiday': 'Sunday'}
        headway_am, headway_pm, period_am, period_pm = '', '', '', ''

        for idx, val in enumerate( temp ):
            if day_type[self.day_type] in val:
                period = temp[idx + 1]
                if '-' in period:
                    # handle when a frequency in a fixed time period was given
                    headway = self.timetable.iloc[idx + 1][2]
                    p_start = datetime.datetime.strptime( period.split( ' - ' )[0], '%I:%M %p' ).time()
                    p_end = datetime.datetime.strptime( period.split( ' - ' )[1], '%I:%M %p' ).time()
                    if gn.time_in_period( p_start, p_end, self.am1, self.am2 ):
                        headway_am = headway
                        period_am = period
                    if gn.time_in_period( p_start, p_end, self.pm1, self.pm2 ):
                        headway_pm = headway
                        period_pm = period
                else:
                    # handle when a list of exact departure time was given
                    min_headway1 = ' '
                    min_headway2 = ' '
                    freq1 = 0
                    freq2 = 0
                    for t in temp[idx + 1:]:
                        time = datetime.datetime.strptime( t, '%I:%M %p' ).time()
                        if gn.time_in_period( time, time, self.am1,
                                              self.am2 ):
                            freq1 += 1
                            min_headway1 += t
                            min_headway1 += ' '
                            headway_am = min_headway1 + '(' + str( freq1 ) + [' trip only)', ' trips only)'][freq1 > 1]
                            period_am = time
                        if gn.time_in_period( time, time, self.pm1,
                                              self.pm2 ):
                            freq2 += 1
                            min_headway2 += t
                            min_headway2 += ' '
                            headway_pm = min_headway2 + '(' + str( freq2 ) + [' trip only)', ' trips only)'][freq2 > 1]
                            period_pm = time

                route = self.j
                info = self.info.replace( '<->', '-' ).replace( '>', '-' ).upper()
                if bound == 1:
                    info = info.split( ' - ' )[1] + ' - ' + info.split( ' - ' )[0]

                self.PT = pd.concat(
                    [self.PT, pd.DataFrame(
                        [[route, info, bound, headway_am, period_am, headway_pm, period_pm, self.day_type]],
                        columns=self.columns )], ignore_index=True )
    # tango='88'

    def main(self):
        tango = self.route
        self.columns = ['route', 'info', 'bound', 'headway_am', 'period_am', 'headway_pm', 'period_pm', 'day_type']

        self.PT = pd.DataFrame(
            columns=self.columns )

        for i, j in enumerate( tango ):  # j='61S'
            self.j = j
            print( j )
            f = SearchGMB( j, self.dist ).load_gmb_data()
            if f is not None:
                try:
                    html = requests.get( f ).text
                    soup = BeautifulSoup( html, 'html.parser' )
                    self.info = soup.find( "td", attrs={"class": "maincontent"} ).text
                    element = soup.find( text="Timetable" )
                    result = element.parent.parent.parent.parent.parent.parent.next_sibling
                    rows = result.find_all( 'tr' )[1:]

                    data = []

                    for row in rows:  # row = rows[2]
                        cols = row.find_all( 'td' )
                        childrens = cols[0].findChildren()
                        a = ', '.join( [x.name for x in childrens] ) if len( childrens ) > 0 else ''
                        cols = [ele.text.strip() for ele in cols]
                        cols.append( a )
                        data.append( cols )

                    columns = data[0]
                    self.timetable = pd.DataFrame( data[1:], columns=columns )
                    circular = 0
                    if '' == self.timetable.columns[1]:
                        circular = 1
                    elif 'Circular' in self.info:
                        circular = 1

                    for bound in range( 2 - circular ):
                        if bound == 0:
                            self.html_parse( bound )
                        else:
                            self.html_parse( 1 )
                except:
                    print( 'Invalid Url' )
                    pass

            if self.progress:
                self.progress.progress( i / len( tango ), text=f'Fetching route {j} data' )


if __name__ == "__main__":
    gmb_get_headway(['411'], savename='test.csv', am1=7, am2=8, pm1=17, pm2=18)
