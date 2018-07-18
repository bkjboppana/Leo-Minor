# -*- coding: utf-8 -*-
"""
Spyder Editor

This is a temporary script file.
"""

import numpy as np
import pandas as pd
from bs4 import BeautifulSoup
import urllib.request as urllib
from requests import get
import matplotlib.pyplot as plt
from dateutil import parser
from apscheduler.schedulers.blocking import BlockingScheduler
from datetime import datetime, date
import os, glob

#get the list of urls
#Given a base url, this item will keep extracting URLs from the search result page.
base_url = 'https://www.ebay.com/b/Camping-Hiking-Sleeping-Gear/181403/bn_7327730?_pgn='
## this function returns a list of links correspoding to an item on sale in ebay
def get_item_links(base_url, uppercut = 800000):
    links = []
    count = 1
    while len(links)<uppercut:
        url = base_url+str(count)
        response = get(url)
        print(url)
        html_soup = BeautifulSoup(response.text, 'html.parser')
        item_page_links = html_soup.find_all('div', class_ = "s-item__wrapper clearfix")
        for link in item_page_links:
            links.append(link.a.attrs['href'])
        count+=1
    return links[:uppercut]
    

#print(response.text[500:1000])
#here we will call the function to get the desired number of links, in order to keep things simple we will just get
#5 links
item_urls = get_item_links(base_url, uppercut=5)

def job_get_item_details(url_list):
    sellerfeedback = []
    item_available = []
    price = []
    item_currency = []
    item_description = []
    keyword = []
    seller_name = []
    currency = []
    quantity_available = []
    for url in url_list:
        print(url)
        response = get(url)
        first_soup = BeautifulSoup(response.text, 'html.parser')# get the html soup
        heading = first_soup.find_all('h1', class_ = "it-ttl")#find the item description
        seller = first_soup.find_all('span', class_ = "mbg-nw")#find the seller name
        seller_feedback = first_soup.find_all('span', class_ = "mbg-l")#get the seller feedback
        item_description.append(heading[0].text[16:])
        seller_name.append(seller[0].text)
        sellerfeedback.append(np.int(seller_feedback[0].text[15:-2]))
        item = first_soup.find_all('span', itemprop = "name")
        available_quantity = first_soup.find_all('span', id = "qtySubTxt")
        retail_price = first_soup.find_all('span', id = "prcIsum")#find the retail price
        discount_price = first_soup.find_all('span', id = "mm-saleDscPrc")
        try:#append retail price, look for error
            y=np.float(retail_price[0].attrs['content'])
            price.append(y)
            print('The price is {}'.format(y))
        except:#else look for discounted price if any
            z  = discount_price[0].text
            m = np.float(''.join(i for i in z if (i.isdigit() or i=='.')))
            price.append(m) 
            print('The discounted price is {}'.format(m))
        try:#append currency 
            price_string = retail_price[0].text.replace('.','')
            currency_1 = ''.join([i for i in price_string if not i.isdigit()])
            currency.append(currency_1)
            print('The currency is {}'.format(currency_1))
        except:#append currency for discounted price
            price_string = discount_price[0].text.replace('.','')
            currency_1 = ''.join([i for i in price_string if not i.isdigit()])
            currency.append(currency_1)
            print('The currency is {}'.format(currency_1))
        try:
            x = available_quantity[0].text
            quantity = [int(s) for s in x.split() if s.isdigit()][0]
            quantity_available.append(quantity)
            if quantity>0:
                item_available.append(1)
            else:
                item_available.append(0)
            print('Available quantity is : {}'.format(quantity))
        except:
            quantity_available.append(np.nan)
            item_available.append(0)
        try:
            keyword.append(item[4].text)#get the keyword
            print(item[4].text)
        except:
            if len(item)>0:
                keyword.append(item[-2].text)
                print(item[-2].text)
            else:
                keyword.append('Not available')
                print('Key word not available')
        
    dfitems = {'Keyword':keyword, 'seller name':seller_name,
               'Price':price, 'Currency':currency}
    return pd.DataFrame(dfitems, columns=dfitems.keys())

def job_get_item_availability(url_list):
    item_available = []
    dateandtime = date.today()
    for url in url_list:
        response = get(url)
        first_soup = BeautifulSoup(response.text, 'html.parser')# get the html soup
        available_quantity = first_soup.find_all('span', id = "qtySubTxt")
        try:
            x = available_quantity[0].text
            quantity = [int(s) for s in x.split() if s.isdigit()][0]
            if quantity>0:
                item_available.append(1)
            else:
                item_available.append(0)
            #print('Available quantity is : {}'.format(quantity))
        except:
            item_available.append(0)
    dict_availability = {str(dateandtime):item_available}
    return pd.DataFrame(dict_availability)
def job_to_schedule():
    global item_urls
    url_list = item_urls
    seed_file_link = 'items_availability.csv'
    df_init = pd.read_csv(seed_file_link)
    df_availability = job_get_item_availability(url_list)
    df_final = pd.concat([df_init, df_availability], axis=1)
    df_final.to_csv('items_availability.csv', index = False)
    print('Done at {}'.format(str(date.today())))
    #return df_final

        
item_availability = job_get_item_details(item_urls)        
item_availability.to_csv('items_availability.csv',index=False)

sched = BlockingScheduler()
sched.add_job(job_to_schedule, 'cron', day_of_week='mon-sun', hour=12, end_date = '2018-07-24' )
sched.start()
