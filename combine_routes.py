# -*- coding: utf-8 -*-
"""
Created on Thu Sep 19 11:12:59 2019

@author: Andrew.WF.Ng
"""

import pandas as pd

import os
import glob

from tkinter import Tk

from tkinter.filedialog import askdirectory

#%%#set peak hour
#peak = 'pm'
#open file

def file_diag():
    Tk().withdraw() # we don't want a full GUI, so keep the root window from appearing
    dirname = askdirectory(initialdir=os.getcwd(),title='Please select a directory')#savename = asksaveasfilename(defaultextension=".666", title = "save file",filetypes = (("666card","*.666"),("all files","*.*")))

    os.chdir(dirname)
    saves=[os.path.join(dirname, os.path.basename(x)) for x in glob.glob("*.csv")]
    return {'saves':saves, 'dirname':dirname}

def main(saves=None):
    if saves == None:
        saves=file_diag()
    routes=pd.DataFrame()
    for file in saves['saves']:
        if 'routes_consolidate' not in file:
            routes=routes.append(pd.read_csv(file))
    dirname=saves['dirname']


    del routes['Unnamed: 0']
    routes=routes.dropna(subset=['Route'])
    routes=routes.drop_duplicates()
    #routes=routes.sort_values(by=['Service Provider', 'Route'])
    routes['Service Provider_cat'] = pd.Categorical(
        routes['Service Provider'],
        categories=['KMB','KMB/CTB','KMB/NWFB','CTB','CTB/NWFB','NWFB','LWB','NLB','GMB','RMB'],
        ordered=True
    )
    routes=routes.sort_values('Service Provider_cat')
    routes.reset_index(inplace=True, drop=True)
    del routes['Service Provider_cat']

    routes.to_csv(dirname+'/routes_consolidate.csv')

    return dirname+'/routes_consolidate.csv'

if __name__ == '__main__':
    main()