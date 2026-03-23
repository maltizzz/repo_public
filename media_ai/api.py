import requests
from bs4 import BeautifulSoup
import google.generativeai as genai
import re, pygsheets, json, ssl, os
from google.oauth2 import service_account
from googleapiclient.discovery import build
import pandas as pd
from pprint import pprint
from tqdm import tqdm
from datetime import date, timedelta
from datetime import datetime
from requests import Session
from selenium import webdriver
from selenium.webdriver.common.by import By
import time

ssl._create_default_https_context = ssl._create_stdlib_context

genai.configure(api_key='SECRET')

model = genai.GenerativeModel('gemini-1.5-flash')
# response = model.generate_content("Summarize me about the Texas Property Code 92")

class Media():
    def __init__(self):
        self.gemini = model
        self.base_path = os.path.abspath(__file__)
        self.service_file = 'SECRET'
        self.gsheet_id = 'SECRET'
        self.gc = pygsheets.authorize(service_file= self.service_file)

    # Format the korean name cleanly
    def korean_name_clean(self, text):
        return text.strip().replace(' ', '')
    
    # Get every dates within designed date
    def get_dates(self, 
                  days_back:int, 
                 formatting: str = '%Y%m%d'):
        # Get today's date
        today = date.today()
        past_date = today - timedelta(days=days_back)

        # Create a list to store the desired dates
        dates = []

        # Loop through each day from past_date to today (inclusive)
        for day in range((today - past_date).days + 1):
            # Calculate the date for each iteration
            current_date = past_date + timedelta(days=day)
            formatted_date = current_date.strftime(formatting) # Format the date as 'YYYYMMDD'
            dates.append(formatted_date)
        return dates
    
    # Get all time combinations
    def get_times(self):
        # Create an empty list to store time combinations
        time_combinations = []

        # Loop through all hours (0 to 23)
        for hour in range(24):
            # Loop through all minutes (0 to 59)
            for minute in range(60):
                # Loop through all seconds (0 to 59)
                for second in range(60):
                    # Format the time as 'HHMMSS'
                    formatted_time = f"{hour:02d}{minute:02d}{second:02d}"
                    # Append the formatted time to the list
                    time_combinations.append(formatted_time)
        return time_combinations
    
    # Extract words in parenthesis
    def find_word_in_parenthesis(self, 
                                 total_text, 
                                 search_word):
        # Define the regular expression pattern
        pattern = re.compile(r'\b{}\s*\((.*?)\)'.format(re.escape(search_word)))
        
        # Find all matches
        matches = pattern.findall(total_text)
        
        return matches

    # Random digits numbers
    def random_digits(self, start_number, end_number, digits):

        # Create an empty list to store the combinations
        combinations = []

        # Loop through all numbers from start_number to end_number
        for number in range(start_number, end_number + 1):
            formatted_number = str(number).zfill(digits) # Convert the number to a string and format to have 4 digits
            # Append the formatted number to the list
            combinations.append(formatted_number)
        return combinations
    
    # Loading gsheet data as Pandas
    def load_gsheet(self, sheet_name):
        sh = self.gc.open_by_key(self.gsheet_id)
        wks = sh.worksheet_by_title(sheet_name)
        data = wks.get_as_df()
        return data

    # Sending Pandas to Gsheet
    def pd_to_gsheet(self, df, sheet_name):
        
        # Open the Google Sheet (by title)
        sh = self.gc.open_by_key(self.gsheet_id)

        # Select the first sheet
        wks = sh.worksheet_by_title(sheet_name)
        
        # Post the DataFrame to the Google Sheet
        wks.clear()
        wks.set_dataframe(df, (1, 1))  # (1, 1) specifies the starting cell (A1)

    # Scrape the jtbc journliasts
    def jtbc_journalists(self):
        jtbc_journalists_df = pd.DataFrame(columns = ['journalist', 'company', 'en_journalist', 'e-mail', 'department', 'id'])

        for i in tqdm(range(30), desc = 'jtbc_journalists'):
            url = f"https://news.jtbc.co.kr/Reporter/data_Reporter.aspx?rdept={i}&vname=rep_list&dtype=rep_list&page=1&pagesize=40"
            response = requests.request("GET", url)    
            if response.status_code == 200:

                # Convert Javascript response to Json
                _data = response.content.decode('utf-8')
                _data_json = re.sub(r'^var\s+\w+\s*=\s*', '', _data
                                ).replace("count :", '"count":'
                                            ).replace("data :", '"data":')
                data_dict = json.loads(_data_json)

                # Get the needed data
                for _sub_data in data_dict['data']:
                    if _sub_data['grade'] == '기자':
                        new_row = {
                            'journalist': self.korean_name_clean(_sub_data['name']),
                            'company': 'jtbc',
                            'en_journalist': '',
                            'e-mail': _sub_data['email'],
                            'department': self.korean_name_clean(_sub_data['part']),
                            'id': _sub_data['rep_seq']}
                        jtbc_journalists_df.loc[len(jtbc_journalists_df)] = new_row
                
            else:
                pass
        jtbc_journalists_df = jtbc_journalists_df.drop_duplicates(subset = ['journalist'], keep = 'last')
        original_df = self.load_gsheet('journalists')
        final_df = pd.concat([original_df, jtbc_journalists_df]).drop_duplicates(subset = ['journalist', 'company'], 
                                                                                keep = 'first')
        self.pd_to_gsheet(df = final_df, sheet_name = 'journalists')

    # Scrape the jtbc contents by journalist
    def jtbc_contents(self):

        # Get the journalist lists
        jtbc_journalist_df = self.load_gsheet('journalists')
        jtbc_journalist_df = jtbc_journalist_df[jtbc_journalist_df['company'] == 'jtbc']
        jtbc_journalist_df = jtbc_journalist_df[['journalist', 'id', 'department']].reset_index(drop = True)
        jtbc_journalist_df['department'] = jtbc_journalist_df['department'].str.replace(r'팀|\d+', '', regex=True).str.strip()

        # Scrape the news
        final_df = pd.DataFrame(columns = ['journalist', 'company', 'headline', 'display_date', 'description', 'topic'])
        for index, row in tqdm(jtbc_journalist_df.iterrows(), 
                               total = jtbc_journalist_df.shape[0], 
                               desc = 'jtbc_contents'):
            _id = int(row['id'])
            _topic = row['department']
            url = f"https://news.jtbc.co.kr/Reporter/data_Reporter.aspx?rep_seq={_id}&vname=news_list&page=1&pagesize=50"
            response = requests.request("GET", url)    
            if response.status_code == 200:
                # Convert Javascript response to Json
                _data = response.content.decode('utf-8')
                _data_json = re.sub(r'^var\s+\w+\s*=\s*', '', _data).replace("count :", '"count":').replace("data :", '"data":')
                try:
                    data_dict = json.loads(_data_json)
                    for _news in data_dict['data']:
                        new_row = {
                                'journalist': row['journalist'],
                                'company': 'jtbc',
                                'headline': _news['title'],
                                'display_date': _news['service_dt'],
                                'description': _news['art_desc'],
                                'topic': _topic}
                        final_df.loc[len(final_df)] = new_row 
                except:
                    pass
            else:
                pass
        original_df = self.load_gsheet('journalist_contents')
        final_df_2 = pd.concat([original_df, final_df]).drop_duplicates(subset = ['journalist', 'company', 'headline'], keep = 'last')
        self.pd_to_gsheet(df = final_df_2, sheet_name = 'journalist_contents')
    
    # Scrape chosun_ilbo journalists
    def chosun_ilbo_journalists(self):
            url = "https://about.chosun.com/pages/hr/recruit_story.php"
            response = requests.request("GET", url)
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')

                _dict_list = list()
                for span in tqdm(soup.find_all('span', class_='tit'), desc = 'chosun_ilbo_journalists'):
                    _dict = dict()

                    # Format the ouput
                    span = span.text.strip()
                    span = span.replace(' ', '')
                    phrase_index = span.find("입니다")
                    extracted_letters = span[phrase_index - 3:phrase_index]

                    # Adding new rows
                    _dict['journalist'] = extracted_letters
                    _dict['company'] = 'chosun_ilbo'
                    _dict['en_journalist'] = None
                    _dict_list.append(_dict)
                
                # Adding as Pandas
                column_name = list(_dict.keys())
                chosun_ilbo_df = pd.DataFrame(_dict_list, columns = column_name)
                original_df = self.load_gsheet('journalists')
                final_df = pd.concat([original_df, chosun_ilbo_df]).drop_duplicates(subset = ['journalist', 'company'], 
                                                                                    keep = 'first')
            self.pd_to_gsheet(df = final_df, sheet_name = 'journalists')
    
    # Get the headline and description of contents by journalist
    def chosun_ibo_contents(self):

        # Get journalist lists
        journalist_list_df = self.load_gsheet('journalists')
        journalist_list_df = journalist_list_df[journalist_list_df['company'] == 'chosun_ilbo']
        journalist_list_df = journalist_list_df[['journalist', 'en_journalist']].reset_index(drop = True)

        # Get the content by author
        final_df = pd.DataFrame(columns = ['journalist', 'company', 'headline', 'display_date', 'description', 'topic'])
        for index, row in tqdm(journalist_list_df.iterrows(), total=journalist_list_df.shape[0], desc="chosun_ibo_contents"):
            # Base URL
            author = row['en_journalist']
            url = "https://www.chosun.com/pf/api/v3/content/fetch/story-feed"
            params = {
                "query": f'{{"excludeContentTypes":"video, gallery","excludeSections":"/english","includeAuthors":"{author}","includeContentTypes":"story","size":100}}',
                "filter": '{"content_elements":{"_id","canonical_url","credits":{"by":{"_id","additional_properties":{"original":{"affiliations","byline"}},"name","org","url"}},"description":{"basic"},"display_date","headlines":{"basic","mobile"},"label":{"shoulder_title":{"text","url"},"video_icon":{"text"}},"last_updated_date","liveblogging_content":{"basic":{"date","headline","id","url","website"}},"promo_items":{"basic":{"_id","additional_properties":{"focal_point":{"max","min"}},"alt_text","caption","content","content_elements":{"_id","alignment","alt_text","caption","content","credits":{"affiliation":{"name"},"by":{"_id","byline","name","org"}},"height","resizedUrls":{"16x9_lg","16x9_md","16x9_sm","16x9_xs","16x9_xxl","4x3_lg","4x3_md","4x3_sm","4x3_xs","4x3_xxl"},"subtype","type","url","width"},"credits":{"affiliation":{"byline","name"},"by":{"byline","name"}},"description":{"basic"},"embed_html","focal_point":{"x","y"},"headlines":{"basic"},"height","promo_items":{"basic":{"_id","height","resizedUrls":{"16x9_lg","16x9_md","16x9_sm","16x9_xs","16x9_xxl","4x3_lg","4x3_md","4x3_sm","4x3_xs","4x3_xxl"},"subtype","type","url","width"}},"resizedUrls":{"16x9_lg","16x9_md","16x9_sm","16x9_xs","16x9_xxl","4x3_lg","4x3_md","4x3_sm","4x3_xs","4x3_xxl"},"streams":{"height","width"},"subtype","type","url","websites","width"},"lead_art":{"duration","type"}},"related_content":{"basic":{"_id","absolute_canonical_url","headlines":{"basic","mobile"},"referent":{"id","type"},"type"}},"subheadlines":{"basic"},"subtype","taxonomy":{"primary_section":{"_id","name"},"tags":{"slug","text"}},"type","website_url"},"count","next"}',
                "d": 1382,
                "_website": "chosun"
            }

            # Get the API response
            response = requests.request("GET", url, params=params)
            if response.status_code == 200:
                _data = response.json()
                if len(_data) >0:
                    for _content in _data['content_elements']:
                        if _content['credits']['by'][0]['_id'] == author:
                            new_row = {'journalist': row['journalist'], 
                                        'company': 'chosun_ilbo',
                                        'headline': _content['headlines']['basic'],
                                        'display_date': _content['display_date'],
                                        'description': _content['description']['basic'],
                                        'topic': _content['taxonomy']['primary_section']['name']}
                            final_df.loc[len(final_df)] = new_row
                else:
                    pass
            else:
                print(f'chosun_ibo_contents [{author}] failed due to {response.headers}')
        original_df = self.load_gsheet('journalist_contents')
        final_df_2 = pd.concat([original_df, final_df ]).drop_duplicates(subset = ['journalist', 'company', 'headline'], keep = 'last')
        self.pd_to_gsheet(df = final_df_2, sheet_name = 'journalist_contents')
    
    # Get the article id
    def ytn_get_article_id(self, topic_key):

        # Configure headless browser using Selenium (adjust options as needed)
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')
        driver = webdriver.Chrome(options = options)

        # Initial GET request and parsing
        url = f'https://www.ytn.co.kr/news/list.php?mcd={topic_key}'
        driver.get(url)
        soup = BeautifulSoup(driver.page_source, 'html.parser')

        # Click load more to get 100 articles
        load_more_button = driver.find_element(By.CLASS_NAME, 'btn_white_arr_down')
        key = list()
        while load_more_button:
            try:
                load_more_button.click()
                time.sleep(2)
            except:
                break

        soup = BeautifulSoup(driver.page_source, 'html.parser')
        soup = soup.find('div', class_='news_list_wrap')
        spans = soup.find_all('div', class_='join_key')
        for span in spans:
            key.append(span.get_text())
        driver.quit()
        return key

    # Scrape past 2 days news in YTN
    def ytn_news_scrape(self):

        # Parameters
        topics = {'0101': '정치',
                  '0102': '경제',
                  '0103': '사회',
                  '0115': '전국',
                  '0104': '국제',
                  '0105': '과학',
                  '0106': '문화', 
                  '0107': '스포츠'}
        
        # Search by topics
        for key, value in tqdm(topics.items(), desc = f'ytn scripts'):
            article_ids = self.ytn_get_article_id(key)

            # Update
            contents_df = pd.DataFrame(columns = ['journalist', 'company', 'headline', 'display_date', 'description', 'topic'])
            journalist_df = pd.DataFrame(columns = ['journalist', 'company', 'en_journalist', 'e-mail', 'department', 'id'])

            for _id in article_ids:
                url = f'https://www.ytn.co.kr/_ln/{key}_{_id}'      
                response = requests.request("GET", url)
                
                if (response.status_code == 200):
                    soup = BeautifulSoup(response.content, 'html.parser')
                    error_check = soup.find('script').get_text()
                    if '/_comm/ytn_error.php' not in error_check:

                        content =  soup.find('div', class_='paragraph').get_text().replace('\n', '').replace('\r', '')
                        author = soup.find('meta', attrs={'name': 'author'}).get('content')
                        headline = soup.find('h2', class_='news_title').get_text()
                        
                        # update contents
                        contents_row = {'journalist': author,
                                    'company': 'ytn',
                                    'headline': headline,
                                    'display_date': soup.find('meta', attrs={'name': 'article:modified_time'}).get('content'),
                                    'description': content[:500],
                                    'topic': topics[key]}
                        
                        contents_df.loc[len(contents_df)] = contents_row 
                        
                        # update journalist
                        try:
                            email = self.find_word_in_parenthesis(total_text = content, search_word = author)[0]
                        except:
                            email = None

                        journalist_row = {'journalist': author,
                                        'company': 'ytn',
                                        'en_journalist': None,
                                        'e-mail': email,
                                        'department': topics[key],
                                        'id': None}
                        journalist_df.loc[len(journalist_df)] = journalist_row 
                        
            original_contents_df = self.load_gsheet('journalist_contents')
            final_contents_df = pd.concat([original_contents_df, contents_df]).drop_duplicates(subset = ['journalist', 'company', 'headline'], keep = 'last')
            self.pd_to_gsheet(df = final_contents_df, sheet_name = 'journalist_contents')
            original_journalists_df = self.load_gsheet('journalists')
            final_contents_df = pd.concat([original_journalists_df, journalist_df]).drop_duplicates(subset = ['journalist', 'company'], keep = 'first')
            self.pd_to_gsheet(df = final_contents_df, sheet_name = 'journalists')

    def ytn_entertainment(self):
        return None
    
    def cnn_journalists(self):

        url = "https://edition.cnn.com/profiles/faces-of-cnn"

        response = requests.request("GET", url)
        if response.status_code == 200:
            final_dict = dict()
            soup = BeautifulSoup(response.content, 'html.parser')
            spans = soup.find_all("div", attrs={"class":re.compile("^card container__item container__item--type-media-image container__item--type-section container_grid-4__item container_grid-4__item--type-section")})
            for span in tqdm(spans, desc = 'cnn_journalists'):
                try:
                    # Get name
                    name = span.find('span', attrs={"data-editable":re.compile("^headline")}).get_text()
                    final_dict[name] = dict()
                    final_dict[name]['company'] = 'cnn'
                    final_dict[name]['en_journalist'] = name

                    # link
                    link_ = span.find('a', attrs = {"data-link-type": re.compile("^profile")})['href']
                    link =  f"https://edition.cnn.com{link_}"
                    final_dict[name]['id'] = link

                    # Next stage soup
                    response_2 = requests.request("GET", link)
                    if response_2.status_code == 200:
                        soup_2 = BeautifulSoup(response_2.content, 'html.parser')

                        # Job title
                        job_title = soup_2.find('h2', attrs = {'data-editable': re.compile("^title")}).get_text().replace('\n', '').strip()
                        final_dict[name]['department'] = job_title
                        
                        # social
                        sns_links = soup_2.find_all('a', attrs = {'class': re.compile("^profile__social-link")})
                        sns_list = list()
                        for link in sns_links:
                            sns_list.append(link['href'])
                        final_dict[name]['e-mail'] = sns_list
                except:
                    pass
    
        # Converting dictionary to dataframe
        processed_data = [{'journalist': key, **value} for key, value in final_dict.items()]
        final_df = pd.DataFrame(processed_data)
        final_df = final_df[['journalist', 'company', 'en_journalist', 'e-mail', 'department', 'id']]
        
        # upload
        original_journalists_df = self.load_gsheet('journalists')
        final_contents_df = pd.concat([original_journalists_df, final_df]).drop_duplicates(subset = ['journalist', 'company'], keep = 'first')
        final_contents_df = final_contents_df[final_contents_df['department'] != 'CNN Profiles A-Z'].reset_index(drop = True)
        self.pd_to_gsheet(df = final_contents_df, sheet_name = 'journalists')

    def cnn_contents(self):
        journalists_df = self.load_gsheet('journalists')
        journalists_df = journalists_df[journalists_df['company'] == 'cnn'][['journalist', 'company', 'id']].reset_index(drop  = True)
        journalists_df = journalists_df[journalists_df['id'].notnull()]
        final_df = pd.DataFrame(columns = ['journalist', 'company', 'headline', 'display_date', 'description'])
        for idx, row in tqdm(journalists_df.iterrows(), 
                             total = journalists_df.shape[0],
                             desc = 'cnn_contents'):
            response = requests.request("GET", row['id'])
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                spans = soup.find_all('div', attrs = {'data-component-name': re.compile("^card")})
                for span in spans:
                    if span.find('span', attrs = {'data-editable': re.compile("^headline")}).get_text().replace('\n', '').strip() is not None:
                        try:
                            final_dict = dict()
                            display_date = span.find('div', attrs = {'data-editable': re.compile("^lastPublishedString")}).get_text().replace('\n', '').strip()
                            date_obj = datetime.strptime(display_date, '%b %d, %Y')
                            final_dict['display_date'] = date_obj                    
                            final_dict['journalist'] = row['journalist']
                            final_dict['company'] = row['company']
                            final_dict['headline'] = span.find('span', attrs = {'data-editable': re.compile("^headline")}).get_text().replace('\n', '').strip()
                            try:
                                final_dict['description'] = span.find('div', attrs = {'data-editable': re.compile("^description")}).get_text().replace('\n', '').strip()
                            except:
                                final_dict['description'] = None
                            final_dict['topic'] = None
                            final_df.loc[len(final_df)] = final_dict 
                        except:
                            pass
                        
        original_contents_df = self.load_gsheet('journalist_contents')
        final_contents_df = pd.concat([original_contents_df, final_df]).drop_duplicates(subset = ['journalist', 'company', 'headline'], keep = 'last')
        final_contents_df = final_contents_df[final_contents_df['display_date'].notnull()].reset_index(drop= True)
        self.pd_to_gsheet(df = final_contents_df, sheet_name = 'journalist_contents')

    def ETL(self):
        
        # Chosun
        self.chosun_ilbo_journalists()
        self.chosun_ibo_contents()

        # JTBC
        self.jtbc_journalists()
        self.jtbc_contents()

        # YTN
        self.ytn_news_scrape()

        # CNN
        self.cnn_journalists()
        self.cnn_contents()

        