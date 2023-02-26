# -*- coding: utf-8 -*-
"""
Created on Mon Sep  9 10:00:12 2019

@author: Andrew.WF.Ng
"""
import datetime
import json
import re
import urllib.request

import pandas as pd

from utils import general as gn


# %%

def check_weekday(source_type, check_type):
    day_type = {'weekday': ['MF        ', 'MS        ', 'D         '],
                'saturday': ['S         ', 'D         '],
                'holiday': ['H         ', 'D         ']}
    return source_type in day_type[check_type]


def split_period(row, bound_txt):
    try:
        row['StartTime'] = re.split( r'[-|/\s]', row[bound_txt] )[0]
        row['StartTime'] = datetime.datetime.strptime( row['StartTime'], '%H:%M' )
        row['StartTime'] = row['StartTime'].time()
    except ValueError:
        row['StartTime'] = datetime.time( 23, 59, 59 )
    try:
        if row['MinTime'] == '':
            row['EndTime'] = row[bound_txt]
        else:
            row['EndTime'] = re.split( r'[-|/\s]', row[bound_txt] )[-1]
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
    progress = kwargs.get( 'progress', None )
    day_type = kwargs.get( 'day_type', 'weekday' )

    if am2 is None or pm2 is None:
        am2 = am1 + period
        pm2 = pm1 + period

    columns = ['route', 'info', 'bound', 'headway_am', 'period_am', 'headway_pm', 'period_pm', 'day_type']
    # Declare output PT df
    # Iterate by route
    # route=['103']   #Dummy test route
    PT = pd.DataFrame( columns=columns )
    i = 0
    for route in routes:
        try:
            route = route.strip()
            print( route )
        except TypeError:
            pass
        # Fetch route type list
        url = r'http://search.kmb.hk/KMBWebSite/Function/FunctionRequest.ashx?action=getroutebound&route=%s' % route
        data1 = urllib.request.urlopen( url ).read()
        output1 = json.loads( data1 )
        output1 = output1['data']

        # detect change in bound
        legacy_bound = 0

        # iter through all special route (bidirectional) of a route
        for j in output1:  # j=0   #j=1
            min1 = 61
            min2 = 61
            min_headway1 = ' '
            min_headway2 = ' '
            freq1 = 0
            freq2 = 0
            headway_am, headway_pm, period_am, period_pm = '', '', '', ''

            try:
                bound = j['BOUND']
                # Request for route details if bound changed
                if bound != legacy_bound:
                    url = r'http://search.kmb.hk/KMBWebSite/Function/FunctionRequest.ashx?action=getschedule&route=%s' \
                          r'&bound=%s' % (route, bound)
                    data = urllib.request.urlopen( url ).read()
                    output = json.loads( data )
                    legacy_bound = bound
                    service = '0' + str( j['SERVICE_TYPE'] )

                    url2 = r'https://search.kmb.hk/kmbwebsite/Function/FunctionRequest.ashx?action=getSpecialRoute' \
                           r'&route=%s&bound=%s' % (route, bound)
                    data2 = urllib.request.urlopen( url2 ).read()
                    output2 = json.loads( data2 )
                    mother_ori = output2['data']['routes'][int( service ) - 1]['Origin_ENG']
                    mother_dest = output2['data']['routes'][int( service ) - 1]['Destination_ENG']
                # print (output)

                service = '0' + str( j['SERVICE_TYPE'] )
                schedule = pd.DataFrame( output['data'][service] )

                route = route.upper()

                if schedule.iloc[0]['Origin_Eng'] == '':
                    ori = mother_ori
                else:
                    ori = schedule.iloc[0]['Origin_Eng']
                if schedule.iloc[0]['Destination_Eng'] == '':
                    dest = mother_dest
                else:
                    dest = schedule.iloc[0]['Destination_Eng']

                if bound == 1:
                    info = ori + ' - ' + dest
                else:
                    info = dest + ' - ' + ori

                for index, row in schedule.iterrows():
                    # row=schedule.iloc[1]
                    try:
                        if 'day' in row['BoundText1']:
                            min_headway1 = 'Special route'

                        elif check_weekday( row['DayType'], day_type ):
                            bound_time = r'BoundTime%s' % bound
                            bound_txt = r'BoundText%s' % bound
                            row['MinTime'] = row[bound_time]
                            row[bound_txt] = row[bound_txt].replace( '.', ':' )
                            if row[bound_time].count( '-' ) == 1:
                                row['MinTime'] = row[bound_time].split( '-' )[0]
                            elif row[bound_time].count( '/' ) == 1:
                                row['MinTime'] = row[bound_time].split( '/' )[0]
                            row = split_period( row, bound_txt )

                            if row[bound_time] != '':
                                """
                                handle when a frequency in a fixed time period was given
                                """
                                if gn.time_in_period( row['StartTime'], row['EndTime'], am1,
                                                      am2 ):  # or time_in_pm(row['StartTime'],row['EndTime']):
                                    if int( row['MinTime'] ) < min1:
                                        min1 = int( row['MinTime'] )
                                        min_headway1 = row[bound_time]
                                        period_am = row[bound_txt].strip( '*' ).strip( '^' )
                                if gn.time_in_period( row['StartTime'], row['EndTime'], pm1,
                                                      pm2 ):  # or time_in_pm(row['StartTime'],row['EndTime']):
                                    if int( row['MinTime'] ) < min2:
                                        min2 = int( row['MinTime'] )
                                        min_headway2 = row[bound_time]
                                        period_pm = row[bound_txt].strip( '*' ).strip( '^' )

                            elif row[bound_time] == '' and row[bound_txt][:1] != '(' and row[bound_txt] != '':
                                """
                                handle when a list of exact departure time was given
                                """
                                if ',' in row[bound_txt]:
                                    for time in row[bound_txt].split( ', ' ):  # time = row[bound_txt].split(', ')[0]
                                        test_time = datetime.datetime.strptime( time, '%H:%M' ).time()
                                        if gn.time_in_period( test_time,
                                                              test_time, am1,
                                                              am2 ):  # or time_in_pm(row['StartTime'],row['EndTime']):
                                            freq1 += 1
                                            min_headway1 += time
                                            min_headway1 += ' '
                                            period_am = time
                                        if gn.time_in_period( test_time,
                                                              test_time, pm1,
                                                              pm2 ):  # or time_in_pm(row['StartTime'],row['EndTime']):
                                            freq2 += 1
                                            min_headway2 += time
                                            min_headway2 += ' '
                                            period_pm = time

                                if gn.time_in_period( datetime.datetime.strptime( row[bound_txt], '%H:%M' ).time(),
                                                      row['EndTime'], am1,
                                                      am2 ):  # or time_in_pm(row['StartTime'],row['EndTime']):
                                    freq1 += 1
                                    min_headway1 += row[bound_txt]
                                    min_headway1 += ' '
                                    period_am = row[bound_txt].strip( '*' ).strip( '^' )
                                if gn.time_in_period( row['StartTime'],
                                                      row['EndTime'], pm1,
                                                      pm2 ):  # or time_in_pm(row['StartTime'],row['EndTime']):
                                    freq2 += 1
                                    min_headway2 += row[bound_txt]
                                    min_headway2 += ' '
                                    period_pm = row[bound_txt].strip( '*' ).strip( '^' )
                    except:
                        pass
                if min1 < 61:
                    headway_am = min_headway1
                if min2 < 61:
                    headway_pm = min_headway2
                '''
                elif freq2 > freq1:
                    freq1 = freq2
                    min_headway1=min_headway2
                '''
                if freq1 == 1:
                    headway_am = min_headway1 + '(' + str( freq1 ) + ' trip only)'
                elif freq1 > 1:
                    headway_am = min_headway1 + '(' + str( freq1 ) + ' trips only)'

                if freq2 == 1:
                    headway_pm = min_headway2 + '(' + str( freq2 ) + ' trip only)'
                elif freq2 > 1:
                    headway_pm = min_headway2 + '(' + str( freq2 ) + ' trips only)'

                PT = pd.concat(
                    [PT, pd.DataFrame( [[route, info, bound, headway_am, period_am, headway_pm, period_pm, day_type]],
                                       columns=columns )], ignore_index=True )

            except:
                print( 'error' )

            # print(i)
        i = i + 1
        if progress:
            progress.progress( i / len( routes ), text=f'Fetching route {route} data' )
    print( PT )
    print( PT.period_am )
    print( PT.headway_am )
    print( PT.headway_pm )
    # %%
    return PT


if __name__ == '__main__':
    main( ['5c'], savename='debug.xlsx' )
