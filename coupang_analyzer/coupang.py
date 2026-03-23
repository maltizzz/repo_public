from selenium import webdriver
from selenium.webdriver.common.by import By
import time, requests, certifi
import pandas as pd
from bs4 import BeautifulSoup
from urllib.parse import quote
from utill import *
import streamlit as st
import re, ssl, os
from dotenv import load_dotenv
import socket

# Environment settings
base_dir = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(os.path.dirname(base_dir), '_secrets', '.env'))
secret_path = os.path.join(os.path.dirname(base_dir), '_secrets', 'pj_han_official.json')

# ca_bundle_path = os.path.join(base_dir, 'cacert.pem')
hostname = socket.gethostname()
local_ip = socket.gethostbyname(hostname)

def coupang_scrape(item_name):

    _item = item_name
    encoded_text = quote(_item, encoding='utf-8')
    header =  {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36", 
            "Accept-Language": "ko-KR,ko;q=0.8,en-US;q=0.5,en;q=0.3"}   
    url = f'https://www.coupang.com/np/search?component=&q={encoded_text}&channel=user&rating=4'

    res = requests.get(url, headers=header)

    if res.status_code == 200:

        final_dict = dict()
        soup = BeautifulSoup(res.text, "lxml")
        soup = soup.find("ul", attrs={"class":re.compile("^search-product-list")})
        items = soup.find_all("li", attrs={"class":re.compile("^search-product")})

        # Process the data
        top10_price = 0
        number = 0 
        for item in items:
            ad_badge = item.find("span", attrs={"class":"ad-badge-text"}) # 광고 제품은 제외
            if ad_badge:
                continue

            # Item name
            name = item.find("div", attrs={"class":"name"}).get_text().strip().replace('\n', '') # 제품명
            final_dict[name] = dict()
            # Pricing
            try:
                price = int(item.find("strong", attrs={"class":"price-value"}).get_text().replace(',', '').strip()) # sale price
            except:
                price = int(item.find("del", attrs={"class":"base-price"}).get_text().replace(',', '').strip()) # base price
            final_dict[name]['price'] = price

            # Unit pricing
            unit_price_soup = item.find("span", attrs={"class":"unit-price"})
            if unit_price_soup:
                unit_price = int(unit_price_soup.find_all('em')[1].get_text().replace(',', '').strip()) # sale price
                final_dict[name]['unit_price'] = unit_price
            else:
                final_dict[name]['unit_price'] = None
                pass
            
            # Link
            sub_link = item.find("a", attrs={"class":re.compile("^search-product-link")})['href']
            link = f"https://www.coupang.com{sub_link}"
            final_dict[name]['link'] = link

            # Get the top5 price
            if number < 10:
                top10_price += price

            # To get the top 5
            number += 1
        # Filter the items with similar price range (ex. 30%)
        top10_price_avg = (top10_price / 10)
        final_dict_2 = {key: value for key, value in final_dict.items() if (value['price'] > (top10_price_avg * 0.7)) and (value['price'] < (top10_price_avg * 1.3))}

        # FINAL OUTPUS
        processed_data = [{'item_name': key, **value} for key, value in final_dict_2.items()]
        final_df = pd.DataFrame(processed_data)
        return final_df
    else:
        return None
