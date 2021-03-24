# -*- coding: utf-8 -*-
"""
Created on Mon Sep 23 15:19:41 2019

@author: Andrew.WF.Ng
"""
import pandas as pd
import requests
from bs4 import BeautifulSoup
from tkinter.filedialog import askdirectory


def fetch_archive(path, window=None):
    for id in range( 0, 4000 ):
        print( id )
        with requests.Session() as s:
            url = 'https://h2-app-rr.hkemobility.gov.hk/ris_page/get_gmb_detail.php?route_id=%s&lang=EN' % id
            r = s.get( url )
            soup = BeautifulSoup( r.text, 'html.parser' )
            header = soup.find( "td", attrs={"class": "HLevel1"} )
            head = pd.DataFrame( header )
            if len( head ) > 0:
                save_path = path + r'\%s.html' % head[0][0][:len( head[0][0] ) - 1].replace( ' ', '_' )
                with open( save_path, "w", encoding="utf-8" ) as file:
                    file.write( str( soup ) )
        if window is not None:
            window.progress['value'] += 1
            window.update()

if __name__ == "__main__":
    fetch_archive(askdirectory())