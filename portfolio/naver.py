import json, urllib, ssl, os
from bs4 import BeautifulSoup
import pandas as pd
from collections import Counter
from urllib.parse import quote
from konlpy.tag import Okt
import streamlit as st
from dotenv import load_dotenv

# Environment settings
ssl._create_default_https_context = ssl._create_stdlib_context
base_dir = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(os.path.dirname(base_dir), '_secrets', '.env'))
secret_path = os.path.join(os.path.dirname(base_dir), '_secrets', 'pj_han_official.json')


# Call the CSS
with open(os.path.join(base_dir, 'css', 'header.css'), 'r') as f:
    header = f.read()
with open(os.path.join(base_dir, 'css', 'header_2.css')) as f:
    header_2 = f.read()
with open(os.path.join(base_dir, 'css', 'sub_header.css'), 'r') as f:
    sub_header = f.read()

def naver_keyword_result(input_dict):
    st.markdown(f'<div class="header_2">{header_2}What are "TOP 20 blogs" and "Most-used words"?</div>', unsafe_allow_html=True)
    st.write('')
    # Run the api
    client_id = 'kbbwlDVOIRCRKMeXN0lf'
    client_secret = 'ac30qTN7wY'

    final_df = pd.DataFrame()
    for text in input_dict['keywords']:
        search_text = text
        encText = urllib.parse.quote(search_text)
        context = ssl._create_unverified_context()
        url = "https://openapi.naver.com/v1/search/blog.json?query=" + encText + "&display=20&sort=sim"# JSON 결과
        # url = "https://openapi.naver.com/v1/search/blog.xml?query=" + encText # XML 결과

        request = urllib.request.Request(url)
        request.add_header("X-Naver-Client-Id",client_id)
        request.add_header("X-Naver-Client-Secret",client_secret)
        response = urllib.request.urlopen(request, context = context)
        rescode = response.getcode()
        if(rescode==200):
            response_body = response.read()
            response_body = json.loads(response_body.decode('utf-8'))
            response_body = response_body['items']
            sub_df = pd.DataFrame(response_body)
            final_df = pd.concat([final_df, sub_df], ignore_index=True)
        else:
            pass

    if len(final_df) >0:
        # def make_clickable(link):
        #     return f'<a href="{link}" target="_blank">{link}</a>'
        # Function to clean HTML tags from a string
        def clean_html_tags(text):
            return BeautifulSoup(text, 'html.parser').get_text()

        # final_df['link'] = final_df['link'].apply(make_clickable)
        final_df['title'] = final_df['title'].apply(clean_html_tags)
        final_df['description'] = final_df['description'].apply(clean_html_tags)
        final_df['postdate']  = pd.to_datetime(final_df['postdate'] , format='%Y%m%d').dt.strftime('%Y-%m-%d')
        final_df.index = final_df.index + 1
        
        # Show data
        with st.expander('', expanded = True):
            # Function to generate word cloud
            def top20_keywords(df_column):
                # Tokenization for Korean text
                okt = Okt()
                tokens = []
                words_to_remove = input_dict['keywords']
                for text in df_column:
                    tokens.extend([word for word in okt.nouns(text) if word not in words_to_remove and len(word) > 1])
                
                # Count word frequency
                top_20_words = Counter(tokens).most_common(20)
                top_20_words_df = pd.DataFrame(top_20_words)
                top_20_words_df = top_20_words_df.rename(columns={0: '키워드', 1: '쓰인 숫자'})
                top_20_words_df.index = top_20_words_df.index + 1

                return top_20_words_df
            
            top_20_words_df = top20_keywords(final_df['description'])

            # Display data
            col1, col2 = st.columns([6,4])
            with col1:
                st.markdown(f'<div style="text-align: center; font-size: 30px; font-weight: bold;">Top 20 Blogs</div>', unsafe_allow_html=True)
                st.write('')
                st.data_editor(
                    final_df[['bloggername', 'title', 'link', 'postdate']],
                    column_config={
                        "bloggername": st.column_config.TextColumn('블로거'),
                        "title": st.column_config.TextColumn(
                            "제목"
                        ),
                        "link": st.column_config.LinkColumn(
                            "링크",
                            max_chars=100,
                            display_text= "LINK"
                        ),
                        "postdate": st.column_config.TextColumn('포스팅 날짜')
                    },
                    hide_index=False,
                    use_container_width = True,
                    
                )
            with col2:
                st.markdown(f'<div style="text-align: center; font-size: 30px; font-weight: bold;">Top 20 Most-used words</div>', unsafe_allow_html=True)
                st.write('')
                st.dataframe(top_20_words_df, use_container_width= True)
    else:
        st.warning('데이터가 올바르지 않습니다.')

def naver_search_result(input_dict, groupName, keywords):
    client_id = "qE_cfFC_bMrUPwpAJqwv"
    client_secret = "WtenLMPFwa"
    url = "https://openapi.naver.com/v1/datalab/search"
    params = {"startDate": input_dict['startDate'].strftime('%Y-%m-%d'),
                "endDate": input_dict['endDate'].strftime('%Y-%m-%d'),
                "timeUnit": "week",
                "keywordGroups": [
                    {
                    "groupName": input_dict['groupName'],
                    "keywords": input_dict['keywords']
                    }
                ]
                # "device": "pc",
                # "ages": [
                #     "1",
                #     "2"
                # ],
                # "gender": "f"
                }
    
    # Convert params to JSON string
    params = json.dumps(params)

    # Request
    request = urllib.request.Request(url)
    request.add_header("X-Naver-Client-Id",client_id)
    request.add_header("X-Naver-Client-Secret",client_secret)
    request.add_header("Content-Type","application/json")
    context = ssl._create_unverified_context()
    request_response = urllib.request.urlopen(request, data=params.encode("utf-8"), context = context)
    rescode = request_response.getcode()

    if(rescode==200):
        response_body = request_response.read()
        response_data = json.loads(response_body.decode('utf-8'))
        response_data = response_data['results'][0]['data']

        # Get Top 5 dates
        response_data_top10 = pd.DataFrame(response_data)
        if len(response_data_top10) > 0:

            response_data_top10 = response_data_top10.sort_values(by='ratio', ascending=False).head(10)
            response_data_top10['period'] = pd.to_datetime(response_data_top10['period'])
            response_data_top10['month'] = response_data_top10['period'].dt.month
            response_data_top10.drop_duplicates(subset=['month'], keep='first', inplace=True)

            response_data_top_months = sorted(response_data_top10['month'].tolist()[:3])

            top_months = ''
            for idx, month in enumerate(response_data_top_months):
                if idx != len(response_data_top_months) -1 :
                    top_months += f'{month}월, '
                else:
                    top_months += f'{month}월'

            # Convert to graph
            response_df = pd.DataFrame(response_data)
            response_df["period"] = pd.to_datetime(response_df["period"])
            response_df.set_index("period", inplace=True)

            with st.expander(label = '**Search-frequency graph**', expanded = True):
                st.write('')
                st.line_chart(response_df)

            # Display summary
            msg = f'For [{groupName}] topics <br> [{keywords}] was searched most in [{top_months}]'
            st.markdown(f'<div class="sub_header">{sub_header}{msg}</div>', unsafe_allow_html=True)
        else:
            st.warning("검색된 기록이 없습니다")

        
        naver_keyword_result(input_dict)
    else:
        st.write("Error Code:" + rescode)