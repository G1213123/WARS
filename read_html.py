# -*- coding: utf-8 -*-
"""
Created on Tue Sep 10 15:37:31 2019

@author: Andrew.WF.Ng
"""
import urllib.request
import pandas as pd
import webbrowser
import folium
from tkinter import *
from tkinter.filedialog import askopenfilename
from tkinter.filedialog import asksaveasfilename

import tkinter as tk


class App():
    def __init__(self, master):
        self.display_button_entry(master)
        self.x = 960
        # self.y=0

    def setup_window(self, master):
        self.f = tk.Frame(master, height=480, width=640, padx=10, pady=12)
        self.f.pack_propagate(0)

    def display_button_entry(self, master):
        self.setup_window(master)
        v = tk.StringVar()
        self.e = tk.Entry(self.f, textvariable=v)
        u = tk.StringVar()
        self.d = tk.Entry(self.f, textvariable=u)
        buttonA = tk.Button(self.f, text="Cancel", command=self.cancelbutton)
        buttonB = tk.Button(self.f, text="OK", command=self.okbutton)
        labelx = tk.Label(self.f, text='lat')
        labely = tk.Label(self.f, text='lon')
        # self.var1 = IntVar()
        # self.var1.set(0)
        # self.cbus = tk.Checkbutton(self.f, text="bus", variable=self.var1, onvalue=1, offvalue=0)

        labelx.pack()
        self.e.pack()
        labely.pack()
        self.d.pack()
        buttonA.pack()
        buttonB.pack()
        # self.cbus.pack()
        self.f.pack()

    def cancelbutton(self):
        print(self.e.get())
        master.destroy()

    def okbutton(self):
        print(self.e.get())
        print(self.d.get())
        x = self.e.get()
        y = self.d.get()
        # bus=self.var1
        main(x, y)
        master.destroy()
        return 0

    def _close(self):
        master.destroy()


def get_html(x,y):
    url = r'https://www.hkemobility.gov.hk/getnearby.php?dist=500&lat=%s&lon=%s&golang=EN' % (x, y)
    # url = http://www.hkemobility.gov.hk/getnearby.php?dist=1000&lat=22.33236511796521&lon=114.18292213964844&sysid=6

    req = urllib.request.Request(url)
    f = urllib.request.urlopen(req)
    xhtml = f.read().decode('utf-8')

    radius=int(xhtml.split('sys_nearby_radius=',1)[1][:4].replace(';',''))

    return xhtml,radius

def html_to_table(xhtml):
    tables = pd.read_html(xhtml)

    del tables[0:2]
    routes = pd.concat(tables)
    routes = routes.fillna(method='bfill')
    routes.reset_index(inplace=True, drop=True)
    routes = routes[routes.index % 2 == 0]
    routes.columns = ['Origin', 'route_no', 'Destination']
    routes.reset_index(inplace=True, drop=True)

    routes[['Service Provider', 'Route']] = routes.route_no.str.split(n=1, expand=True)
    routes = routes[['Service Provider', 'Route', 'Origin', 'Destination']]
    # routes=routes.drop_duplicates()

    '''
    gmb=routes[routes['Service Provider']=='GMB']
    gmb=gmb.drop_duplicates(['Route'])
    '''
    return routes


def main(x, y, savename='', show = False):
    xhtml, radius = get_html(x,y)
    routes=html_to_table(xhtml)

    if savename == '':
        # File path prompt
        Tk().withdraw()  # we don't want a full GUI, so keep the root window from appearing
        savename = asksaveasfilename(defaultextension=".csv", title="save file",
                                     filetypes=(("comma seperated values", "*.csv"), ("all files", "*.*")))
    routes.to_csv(savename)

    m = folium.Map(location=[x, y], zoom_start=20, tiles='OpenStreetMap')
    folium.Circle([x, y], radius=radius, popup=str(radius) + 'm lat=%s lon=%s' % (x, y), color='#3186cc',
                  fill_color='#3186cc').add_to(m)
    m.save(savename.replace('.csv', '.html'), 'a')

    if show:
        webbrowser.open(savename.replace('.csv', '.html'))

    return savename


if __name__ == "__main__":
    master = tk.Tk()
    master.title('Location')
    master.resizable(width=tk.NO, height=tk.NO)
    app = App(master)
    master.mainloop()
