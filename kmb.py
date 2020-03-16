# -*- coding: utf-8 -*-
"""
Created on Mon Sep  9 10:00:12 2019

@author: Andrew.WF.Ng
"""
import pandas as pd
import json, urllib.request
import datetime
import re
import geopandas
import numpy as np
from shapely.geometry import Point
import general as gn
from pyproj import _datadir, datadir

# %%


def split_period(row, bound_txt):
    try:
        row['StartTime'] = re.split(' - |/', row[bound_txt])[0]
        row['StartTime'] = datetime.datetime.strptime(row['StartTime'], '%H:%M')
        row['StartTime'] = row['StartTime'].time()
    except ValueError:
        row['StartTime'] = datetime.time(23, 59, 59)
    try:
        if row['MinTime'] == '':
            row['EndTime'] = row[bound_txt]
        else:
            row['EndTime'] = re.split(' - |/', row[bound_txt])[1][:5]
        row['EndTime'] = datetime.datetime.strptime(row['EndTime'], '%H:%M')
        row['EndTime'] = row['EndTime'].time()
    except ValueError:
        row['EndTime'] = datetime.time(0, 0, 0)
    return row


# %%
class Kmb_Route():
    def __init__(self, route, bound):
        self.route = route
        self.bound = bound

    def fetch_kmb_route(self):
        url = r'http://search.kmb.hk/KMBWebSite/Function/FunctionRequest.ashx?action=getstops&route=%s&bound=%s&serviceType=1' % (
            self.route, self.bound)
        test_gps = pd.read_json(url)
        test_gps = test_gps['data']['route']
        test_gps['lineGeometry'] = test_gps['lineGeometry'].replace("{paths:", "")
        test_gps['lineGeometry'] = test_gps['lineGeometry'][:-1]
        paths = pd.read_json(test_gps['lineGeometry'])
        test2 = paths.to_numpy().flatten()
        test2 = test2[test2 != np.array(None)]
        paths = pd.DataFrame(test2, columns=['point'])
        paths['geometry'] = paths.apply(lambda row: Point(row.point), axis=1)
        paths = geopandas.GeoDataFrame(paths['geometry'], geometry='geometry')
        paths.crs = {'init': 'epsg:2326'}
        gps = paths.to_crs({'init': 'epsg:4326'})
        return gps


# Kmb_Route('277x',1).fetch_kmb_route()
# %%

# if __name__ == '__main__':


def main(route=None, **kwargs):
    am1 = kwargs.get('am1', 7)
    pm1 = kwargs.get('pm1', 17)
    period = kwargs.get('period', 1)
    am2 = kwargs.get('am2', None)
    pm2 = kwargs.get('pm2', None)

    savename = kwargs.get('savename', None)
    window = kwargs.get( 'window', None )

    if am2 is None or pm2 is None:
        am2 = am1 + period
        pm2 = pm1 + period

    route, savename = gn.read_route(route, savename)

    # Declare output PT df
    # Iterate by route
    # route=['103']   #Dummy test route
    PT = pd.DataFrame(columns=['route', 'info', 'headway_am', 'headway_pm', 'bound', 'period_am', 'period_pm'])
    i = 0
    while i < len(route):
        try:
            route[i] = route[i].strip()
            print(route[i])
        except TypeError:
            pass
        # Fetch route type list
        url = r'http://search.kmb.hk/KMBWebSite/Function/FunctionRequest.ashx?action=getroutebound&route=%s' % route[i]
        data1 = urllib.request.urlopen(url).read()
        output1 = json.loads(data1)
        output1 = output1['data']
        ori = ''
        dest = ''
        # detect change in bound
        legacy_bound = 0

        # iter through all routes
        for j in range(len(output1)):  # j=0   #j=1
            min1 = 61
            min2 = 61
            min_headway1 = ' '
            min_headway2 = ' '
            freq1 = 0
            freq2 = 0

            try:
                bound = output1[j]['BOUND']
                if bound != legacy_bound:
                    url = r'http://search.kmb.hk/KMBWebSite/Function/FunctionRequest.ashx?action=getschedule&route=%s&bound=%s' % (
                        route[i], bound)
                    data = urllib.request.urlopen(url).read()
                    output = json.loads(data)
                    legacy_bound = bound
                    service = '0' + str(output1[j]['SERVICE_TYPE'])
                    schedule = pd.DataFrame(output['data'][service])

                    mother_ori = schedule.iloc[0]['Origin_Eng']

                    mother_dest = schedule.iloc[0]['Destination_Eng']
                # print (output)

                service = '0' + str(output1[j]['SERVICE_TYPE'])
                schedule = pd.DataFrame(output['data'][service])

                PT = PT.append(pd.Series(), ignore_index=True)
                PT.iloc[-1]['route'] = route[i].upper()
                PT.iloc[-1]['bound'] = bound
                ori = schedule.iloc[0]['Origin_Eng']
                dest = schedule.iloc[0]['Destination_Eng']
                if bound == 1:
                    if schedule.iloc[0]['Origin_Eng'] == '':
                        ori = mother_ori
                    if schedule.iloc[0]['Destination_Eng'] == '':
                        dest = mother_dest
                    PT.iloc[-1]['info'] = ori + ' - ' + dest
                else:
                    if schedule.iloc[0]['Origin_Eng'] == '':
                        ori = mother_ori
                    if schedule.iloc[0]['Destination_Eng'] == '':
                        dest = mother_dest
                    PT.iloc[-1]['info'] = dest + ' - ' + ori

                for index, row in schedule.iterrows():  # row=schedule.iloc[1]
                    try:
                        if 'day' in row['BoundText1']:
                            min_headway1 = 'Special route'

                        elif row['DayType'] == 'MF        ' or row['DayType'] == 'MS        ' or row[
                            'DayType'] == 'D         ':

                            bound_time = r'BoundTime%s' % bound
                            bound_txt = r'BoundText%s' % bound
                            row['MinTime'] = row[bound_time]
                            row[bound_txt] = row[bound_txt].replace('.', ':')
                            if row[bound_time].count('-') == 1:
                                row['MinTime'] = row[bound_time].split('-')[0]
                            elif row[bound_time].count('/') == 1:
                                row['MinTime'] = row[bound_time].split('/')[0]
                            row = split_period(row, bound_txt)

                            if row[bound_time] != '':
                                if gn.time_in_period(row['StartTime'], row['EndTime'], am1,
                                                     am2):  # or time_in_pm(row['StartTime'],row['EndTime']):
                                    if int(row['MinTime']) < min1:
                                        min1 = int(row['MinTime'])
                                        min_headway1 = row[bound_time]
                                        PT.iloc[-1]['period_am'] = row[bound_txt].strip('*').strip('^')
                                if gn.time_in_period(row['StartTime'], row['EndTime'], pm1,
                                                     pm2):  # or time_in_pm(row['StartTime'],row['EndTime']):
                                    if int(row['MinTime']) < min2:
                                        min2 = int(row['MinTime'])
                                        min_headway2 = row[bound_time]
                                        PT.iloc[-1]['period_pm'] = row[bound_txt].strip('*').strip('^')

                            elif row[bound_time] == '' and row[bound_txt][:1] != '(' and row[bound_txt] != '':
                                if ',' in row[bound_txt]:
                                    for time in row[bound_txt].split(', '):  # time = row[bound_txt].split(', ')[0]
                                        test_time = datetime.datetime.strptime(time, '%H:%M').time()
                                        if gn.time_in_period(test_time,
                                                             test_time, am1, am2):  # or time_in_pm(row['StartTime'],row['EndTime']):
                                            freq1 += 1
                                            min_headway1 += time
                                            min_headway1 += ' '
                                            PT.iloc[-1]['period_am'] = time
                                        if gn.time_in_period(test_time,
                                                             test_time, pm1, pm2):  # or time_in_pm(row['StartTime'],row['EndTime']):
                                            freq2 += 1
                                            min_headway2 += time
                                            min_headway2 += ' '
                                            PT.iloc[-1]['period_pm'] = time

                                if gn.time_in_period(datetime.datetime.strptime(row[bound_txt], '%H:%M').time(),
                                                     row['EndTime'], am1, am2):  # or time_in_pm(row['StartTime'],row['EndTime']):
                                    freq1 += 1
                                    min_headway1 += row[bound_txt]
                                    min_headway1 += ' '
                                    PT.iloc[-1]['period_am'] = row[bound_txt].strip('*').strip('^')
                                if gn.time_in_period(row['StartTime'],
                                                     row['EndTime'], pm1, pm2):  # or time_in_pm(row['StartTime'],row['EndTime']):
                                    freq2 += 1
                                    min_headway2 += row[bound_txt]
                                    min_headway2 += ' '
                                    PT.iloc[-1]['period_pm'] = row[bound_txt].strip('*').strip('^')
                    except:
                        pass
                if min1 < 61:
                    PT.iloc[-1]['headway_am'] = min_headway1
                if min2 < 61:
                    PT.iloc[-1]['headway_pm'] = min_headway2
                '''
                elif freq2 > freq1:
                    freq1 = freq2
                    min_headway1=min_headway2
                '''
                if freq1 == 1:
                    PT.iloc[-1]['headway_am'] = min_headway1 + '(' + str(freq1) + ' trip only)'
                elif freq1 > 1:
                    PT.iloc[-1]['headway_am'] = min_headway1 + '(' + str(freq1) + ' trips only)'

                if freq2 == 1:
                    PT.iloc[-1]['headway_pm'] = min_headway2 + '(' + str(freq2) + ' trip only)'
                elif freq2 > 1:
                    PT.iloc[-1]['headway_pm'] = min_headway2 + '(' + str(freq2) + ' trips only)'


            except:
                print('error')
        i = i + 1
        # print(i)
        if window is not None:
            window.progress['value']+=1
            window.update()

    print(PT)
    print(PT.period_am)
    print(PT.headway_am)
    print(PT.headway_pm)
    # %%
    PT.to_excel(savename)
    return PT


if __name__ == '__main__':
    main(['5c'], savename='debug.xlsx')
