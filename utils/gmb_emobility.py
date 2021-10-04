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

    def __init__(self, route, dist='n', savename=None, window=None, **kwargs):
        # all **kwargs keys will be initialized as class attributes
        allowed_keys = {'am1', 'am2', 'pm1', 'pm2'}
        # initialize all allowed keys to false
        self.__dict__.update((key, False) for key in allowed_keys)
        # and update the given keys by their given values
        self.__dict__.update((key, value) for key, value in kwargs.items() if key in allowed_keys)
        self.route = route
        self.dist = dist
        self.savename = savename
        self.window = window
        self.main()
        self.__dict__.update(kwargs)

    def html_parse(self, bound):
        self.PT = self.PT.append(pd.Series(), ignore_index=True)
        temp = self.timetable.iloc[:, 0]
        print(self.j)
        if self.window:
            self.window.headway['cursor'] = 'watch'
            self.window.cprint('Connecting to CTB web service')
        for idx, val in enumerate(temp):
            if 'Mondays' in val:
                period = temp[idx + 1]
                if '-' in period:
                    # handle when a frequency in a fixed time period was given
                    headway = self.timetable.iloc[idx + 1][2]
                    p_start = datetime.datetime.strptime(period.split(' - ')[0], '%I:%M %p').time()
                    p_end = datetime.datetime.strptime(period.split(' - ')[1], '%I:%M %p').time()
                    if gn.time_in_period(p_start, p_end, self.am1, self.am2):
                        self.PT.iloc[-1]['headway_am'] = headway
                        self.PT.iloc[-1]['period_am'] = period
                    if gn.time_in_period(p_start, p_end, self.pm1, self.pm2):
                        self.PT.iloc[-1]['headway_pm'] = headway
                        self.PT.iloc[-1]['period_pm'] = period
                else:
                    # handle when a list of exact departure time was given
                    min_headway1 = ' '
                    min_headway2 = ' '
                    freq1 = 0
                    freq2 = 0
                    for t in temp[1:]:
                        time = datetime.datetime.strptime(t, '%I:%M %p').time()
                        if gn.time_in_period(time, time, self.am1,
                                             self.am2):
                            freq1 += 1
                            min_headway1 += t
                            min_headway1 += ' '
                            self.PT.iloc[-1]['period_am'] = time
                        if gn.time_in_period(time, time, self.pm1,
                                             self.pm2):
                            freq2 += 1
                            min_headway2 += t
                            min_headway2 += ' '
                            self.PT.iloc[-1]['period_pm'] = time

                    if freq1 == 1:
                        self.PT.iloc[-1]['headway_am'] = min_headway1 + '(' + str(freq1) + ' trip only)'
                    elif freq1 > 1:
                        self.PT.iloc[-1]['headway_am'] = min_headway1 + '(' + str(freq1) + ' trips only)'

                    if freq2 == 1:
                        self.PT.iloc[-1]['headway_pm'] = min_headway2 + '(' + str(freq2) + ' trip only)'
                    elif freq2 > 1:
                        self.PT.iloc[-1]['headway_pm'] = min_headway2 + '(' + str(freq2) + ' trips only)'
            self.PT.iloc[-1]['route'] = self.j
            self.PT.iloc[-1]['info'] = self.info.replace('<->', '-')
            self.PT.iloc[-1]['bound'] = bound

    # tango='88'

    def main(self):
        tango, savename = gn.read_route(self.route, self.savename)

        self.PT = pd.DataFrame(
            columns=['route', 'info', 'headway_am', 'headway_pm', 'bound', 'period_am', 'period_pm'])

        for j in tango:  # j='61S'
            self.j = j
            print(j)
            f = SearchGMB(j, self.dist).load_gmb_data()
            if f is not None:
                html = requests.get(f).text
                soup = BeautifulSoup(html, 'html.parser')
                self.info = soup.find("td", attrs={"class": "maincontent"}).text
                element = soup.find(text="Timetable")
                result = element.parent.parent.parent.parent.parent.parent.next_sibling
                rows = result.find_all('tr')[1:]

                data = []

                for row in rows:  # row = rows[2]
                    cols = row.find_all('td')
                    childrens = cols[0].findChildren()
                    a = ', '.join([x.name for x in childrens]) if len(childrens) > 0 else ''
                    cols = [ele.text.strip() for ele in cols]
                    cols.append(a)
                    data.append(cols)

                columns = data[0]
                self.timetable = pd.DataFrame(data[1:], columns=columns)
                circular = 0
                if '' == self.timetable.columns[1]:
                    circular = 1
                elif 'Circular' in self.info:
                    circular = 1

                for bound in range(2 - circular):
                    if bound == 0:
                        self.html_parse(bound)
                    else:
                        self.html_parse(1)

                if self.window is not None:
                    self.window.headway['cursor'] = 'watch'
                    self.window.progress['value'] += 1
                    self.window.cprint('retriving headway data of route ' + str(self.j))
                    self.window.update()
        if self.window:
            self.window.headway['cursor'] = 'arrow'
        self.PT.to_excel(savename)


if __name__ == "__main__":
    gmb_get_headway(['411'], savename='test.csv', am1=7, am2=8, pm1=17, pm2=18)
