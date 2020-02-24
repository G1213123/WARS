# -*- coding: utf-8 -*-
"""
Created on Mon Sep 23 15:19:41 2019

@author: Andrew.WF.Ng
"""
import pandas as pd
import requests
import datetime
from bs4 import BeautifulSoup
def fetch_archive(path):
    for id in range (0,4000):
        print (id)
        with requests.Session() as s:
            url='https://www.hkemobility.gov.hk/ris_page/get_gmb_detail.php?route_id=%s&lang=EN' % id
            r=s.get(url)
            soup = BeautifulSoup(r.text,'html.parser')
            header=soup.find("td",attrs={"class":"HLevel1"})
            head=pd.DataFrame(header)
            if len(head)>0:
                save_path=path + r'\%s.html' % head[0][0][:len(head[0][0])-1].replace(' ','_')
                with open(save_path, "w", encoding="utf-8") as file:
                    file.write(str(soup))
