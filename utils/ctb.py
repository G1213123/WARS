# -*- coding: utf-8 -*-
"""
Created on Mon Sep 23 08:45:09 2019

@author: Andrew.WF.Ng
"""
import datetime

import inflect
import pandas as pd
import requests

p = inflect.engine()
from http.cookies import SimpleCookie
from http.client import IncompleteRead
import re
from utils import general as gn


def check_weekday(source_type, check_type):
    day_type = {'weekday': ['Monday', 'Daily'],
                'saturday': ['Saturday'],
                'holiday': ['Sunday']}
    return any( day_type[check_type] in source_type )


def split_period(row):
    try:
        row['StartTime'] = re.split( ' - |/', row[0] )[0]
        row['StartTime'] = datetime.datetime.strptime( row['StartTime'], '%H:%M' )
        row['StartTime'] = row['StartTime'].time()
    except ValueError:
        row['StartTime'] = datetime.time( 23, 59, 59 )
    try:
        row['EndTime'] = re.split( ' - |/', row[0] )[1][:5]
        row['EndTime'] = datetime.datetime.strptime( row['EndTime'], '%H:%M' )
        row['EndTime'] = row['EndTime'].time()
    except ValueError:
        row['EndTime'] = datetime.time( 0, 0, 0 )
    return row


def main(routes=None, **kwargs):
    am1 = kwargs.get( 'am1', 7 )
    pm1 = kwargs.get( 'pm1', 17 )
    period = kwargs.get( 'period', 1 )
    am2 = kwargs.get( 'am2', None )
    pm2 = kwargs.get( 'pm2', None )
    day_type = kwargs.get( 'day_type', 'weekday' )
    progress = kwargs.get( 'progress', None )
    columns = ['route', 'info', 'bound', 'headway_am', 'period_am', 'headway_pm', 'period_pm', 'day_type', 'special']

    if am2 is None or pm2 is None:
        am2 = am1 + period
        pm2 = pm1 + period

    url = 'https://mobile.bravobus.com.hk/nwp3/printout1.php?code=X&l=1'
    try:
        raw_full_list = pd.read_html( url )
    except IncompleteRead as e:
        raw_full_list = e.partial
    full_list = pd.DataFrame( columns=raw_full_list[2].iloc[0] )

    for j in range( 3, len( raw_full_list ) ):
        full_list.loc[len( full_list )] = raw_full_list[j].iloc[0].tolist()

    PT = pd.DataFrame(
        columns=columns )
    ssid = 0

    # tango=['NA20',22,'769C','702A']
    for i, route in enumerate( routes ):
        print( route )
        route_list = full_list[full_list['Route'].astype( str ) == str( route ).upper()]
        route_list = route_list.reset_index( drop=False )

        for index, row in route_list.iterrows():  # row=route_list.iloc[0]
            route_info = row['Route Information'].upper()
            trial = 0
            with requests.Session() as s:
                if ssid == 0:
                    url1 = 'https://mobile.bravobus.com.hk/nwp3/index.php?golang=EN'
                    r = s.get( url1 )
                    cookie = SimpleCookie()
                    cookie.load( r.cookies )
                    # print(r.cookies)
                    ssid = next( iter( cookie ) )
                url2 = 'https://mobile.bravobus.com.hk/nwp3/routesearch.php'
                params = {'rtype': 'X', 'skey': 'Input%20Route%20No.', 'l': 1, 'savecookie': 0, 'ssid': ssid,
                          'sysid': 3}
                while trial == 0:
                    try:
                        t = s.get( url2, params=params )
                        t.url
                    except:
                        trial = 0
                        print( 'Retry connection' )
                        continue
                    trial += 1
                    # t = IncompleteRead.partial
                url3 = 'https://mobile.bravobus.com.hk/nwp3/getvariance.php'
                params = {'lid': row['index'], 'cur': 0, 'l': 1, 'ssid': ssid}
                try:
                    l = s.get( url3, params=params )
                    l.url
                except IncompleteRead as e:
                    l = e.partial

                # l.text
            temp_var = l.text[l.text.rfind( 'showroute1' ) + 18:]
            info = temp_var[:temp_var.find( '|' )]
            info = row.Company + '||' + info
            if temp_var.find( '*I|' ) > 0:
                bound = 'I'
                bound_txt = 1
            else:
                bound = 'O'
                bound_txt = 0

            params = {'info': info, 'bound': bound, 'l': 1}
            url = 'https://mobile.bravobus.com.hk/nwp3/gettimetable.php'
            r = s.get( url, params=params )
            # r.url
            m = pd.read_html( r.url )
            m.remove( m[0] )

            for l in range( len( m ) - 1 ):
                print( l )
                if 'Monday' in m[l][0][0] or 'Daily' in m[l][0][0]:
                    n = m[l + 1]
                    break
            add_text = m[-1][0][0]

            headway_am, headway_pm, period_am, period_pm = '', '', '', ''
            haveheadway = 0
            for index2, row2 in n.iterrows():  # row2=n.iloc[0]
                if '-' in row2[0]:
                    row2 = split_period( row2 )
                    if gn.time_in_period( row2['StartTime'], row2['EndTime'], am1, am2 ):
                        headway_am = (row2[1])
                        period_am = (row2[0])
                    if gn.time_in_period( row2['StartTime'], row2['EndTime'], pm1, pm2 ):
                        headway_pm = (row2[1])
                        period_pm = (row2[0])
                        haveheadway = 1
                elif haveheadway == 0:
                    peak_trip_am = []
                    peak_trip_pm = []
                    for time_str in row2[0].split( ', ' ):
                        if ':' in time_str:
                            time = datetime.datetime.strptime( time_str, '%H:%M' ).time()
                        else:
                            time = datetime.datetime.strptime( time_str, '%H%M' ).time()
                        if gn.time_in_period( time, time, am1, am2 ):
                            peak_trip_am.append( time_str )
                        if gn.time_in_period( time, time, pm1, pm2 ):
                            peak_trip_pm.append( time_str )
                    if len( peak_trip_am ) > 0:
                        headway_am = ', '.join( peak_trip_am ) + ' (' + str(
                            len( peak_trip_am ) ) + [' trips only)', ' trip only)'][len( peak_trip_am ) == 1]
                    if len( peak_trip_pm ) > 0:
                        headway_pm = ', '.join( peak_trip_pm ) + ' (' + str(
                            len( peak_trip_pm ) ) + [' trips only)', ' trip only)'][len( peak_trip_pm ) == 1]

            PT = pd.concat(
                [PT, pd.DataFrame(
                    [[route, route_info, bound_txt, headway_am, period_am, headway_pm, period_pm, day_type, add_text]],
                    columns=columns )], ignore_index=True )

        if progress is not None:
            progress.progress( i / len( routes ), text=f'Fetching route {route} data' )

    print( PT )
    print( PT.headway_am )
    print( PT.period_am )
    # %%

    return PT


if __name__ == '__main__':
    main( '106P', savename='test.csv' )
