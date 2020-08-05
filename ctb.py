# -*- coding: utf-8 -*-
"""
Created on Mon Sep 23 08:45:09 2019

@author: Andrew.WF.Ng
"""
import pandas as pd
import requests
import urllib
import datetime

import inflect

p = inflect.engine()
import webbrowser
from http.cookies import SimpleCookie
from tkinter import Tk
from tkinter.filedialog import askopenfilename
from tkinter.filedialog import asksaveasfilename
from http.client import IncompleteRead
import re
import general as gn


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


def main(route=None, **kwargs):
    am1 = kwargs.get( 'am1', 7 )
    pm1 = kwargs.get( 'pm1', 17 )
    period = kwargs.get( 'period', 1 )
    am2 = kwargs.get( 'am2', None )
    pm2 = kwargs.get( 'pm2', None )

    savename = kwargs.get( 'savename', None )
    window = kwargs.get( 'window', None )

    if window is not None:
        window.headway['cursor'] = 'watch'
        window.progress['value'] += 1
        window.update()

    if am2 is None or pm2 is None:
        am2 = am1 + period
        pm2 = pm1 + period

    tango, savename = gn.read_route( route, savename )

    url = 'https://mobile.nwstbus.com.hk/nwp3/printout1.php?code=X&l=1'
    try:
        raw_full_list = pd.read_html( url )
    except IncompleteRead as e:
        raw_full_list = e.partial
    full_list = pd.DataFrame( columns=raw_full_list[2].iloc[0] )

    for j in range( 3, len( raw_full_list ) ):
        full_list.loc[len( full_list )] = raw_full_list[j].iloc[0].tolist()

    PT = pd.DataFrame(
        columns=['route', 'info', 'headway_am', 'headway_pm', 'bound', 'period_am', 'period_pm', 'special'] )
    ssid = 0

    # tango=['NA20',22,'769C','702A']
    for i in tango:
        print( i )
        route_list = full_list[full_list['Route'].astype( str ) == str( i ).upper()]
        route_list = route_list.reset_index( drop=False )

        for index, row in route_list.iterrows():  # row=route_list.iloc[0]
            PT = PT.append( pd.Series(), ignore_index=True )
            PT.iloc[-1]['route', 'info'] = row['Route'], row['Route Information']
            trial = 0
            with requests.Session() as s:
                if ssid == 0:
                    url1 = 'https://mobile.nwstbus.com.hk/nwp3/index.php?golang=EN'
                    r = s.get( url1 )
                    cookie = SimpleCookie()
                    cookie.load( r.cookies )
                    # print(r.cookies)
                    ssid = next( iter( cookie ) )
                url2 = 'https://mobile.nwstbus.com.hk/nwp3/routesearch.php'
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
                url3 = 'https://mobile.nwstbus.com.hk/nwp3/getvariance.php'
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
            PT.iloc[-1]['bound'] = bound_txt
            params = {'info': info, 'bound': bound, 'l': 1}
            url = 'https://mobile.nwstbus.com.hk/nwp3/gettimetable.php'
            r = s.get( url, params=params )
            r.url
            m = pd.read_html( r.url )
            m.remove( m[0] )

            for l in range( len( m ) - 1 ):
                print( l )
                if 'Monday' in m[l][0][0] or 'Daily' in m[l][0][0]:
                    n = m[l + 1]
                    break
            add_text = m[-1][0][0]
            PT.iloc[-1]['special'] = add_text

            haveheadway = 0
            for index2, row2 in n.iterrows():  # row2=n.iloc[0]
                if '-' in row2[0]:
                    row2 = split_period( row2 )
                    if gn.time_in_period( row2['StartTime'], row2['EndTime'], am1, am2 ):
                        PT.iloc[-1]['headway_am'] = (row2[1])
                        PT.iloc[-1]['period_am'] = (row2[0])
                    if gn.time_in_period( row2['StartTime'], row2['EndTime'], pm1, pm2 ):
                        PT.iloc[-1]['headway_pm'] = (row2[1])
                        PT.iloc[-1]['period_pm'] = (row2[0])
                        haveheadway = 1
                elif haveheadway == 0:
                    peak_trip_am = []
                    peak_trip_pm = []
                    for time_str in row2[0].split( ', ' ):
                        time = datetime.datetime.strptime( time_str, '%H:%M' ).time()
                        if gn.time_in_period( time, time, am1, am2 ):
                            peak_trip_am.append( time_str )
                        if gn.time_in_period( time, time, pm1, pm2 ):
                            peak_trip_pm.append( time_str )
                    if len(peak_trip_am) > 0:
                        PT.iloc[-1]['headway_am'] = ', '.join(peak_trip_am) + ' ' + str(
                            len(peak_trip_am)) + p.plural(' trip', len(peak_trip_am))
                    if len(peak_trip_pm) > 0:
                        PT.iloc[-1]['headway_pm'] = ', '.join(peak_trip_pm) + ' ' + str(
                            len(peak_trip_pm)) + p.plural(' trip', len(peak_trip_pm))
        if window is not None:
            window.progress['value'] += 1
            window.cprint('retriving headway data of route ' + i)
            window.update()

    window.headway['cursor'] = 'arrow'
    print(PT)
    print(PT.headway_am)
    print(PT.period_am)
    # %%
    PT.to_excel(savename)

    return PT

if __name__ == '__main__':
    main( '106P', savename='test.csv' )
