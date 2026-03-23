import sys
import pandas as pd
import streamlit as st 
import urllib.request
import requests
import plotly.express as px
import plotly.graph_objects as go
import matplotlib.pyplot as plt
from streamlit_option_menu import option_menu
import datetime, ssl, pygsheets, os, sys, ssl, json
from bs4 import BeautifulSoup
import matplotlib.pyplot as plt
import pandas as pd
from collections import Counter
from urllib.parse import quote
from konlpy.tag import Okt
from googleapiclient.discovery import build
from html.parser import HTMLParser
from typing import List
import time, certifi
import os, ssl, socket
import numpy as np
from dotenv import load_dotenv

# Internal module
sys.path.append('./cheat_sheet/youtube/')
from repo_public.youtube_analyzer.youtube_api import YoutubeAnalyzer
from repo_public.coupang_analyzer.coupang import *
from utill import *
from repo_public.naverblog_analyzer.naver import *

# Environment settings
# Set the SSL context
base_dir = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(os.path.dirname(base_dir), '_secrets', '.env'))
secret_path = os.path.join(os.path.dirname(base_dir), '_secrets', 'pj_han_official.json')
hostname = socket.gethostname()
local_ip = socket.gethostbyname(hostname)

# ca_bundle_path = os.path.join(base_dir, 'cacert.pem')
# ssl_context = ssl.create_default_context(cafile=ca_bundle_path)
# ssl._create_default_https_context = ssl._create_unverified_context

# if 'youtube_run' not in st.session_state:
#     st.session_state['youtube_run'] = False

# Call the CSS
with open(os.path.join(base_dir, 'css', 'header.css'), 'r') as f:
    header = f.read()
with open(os.path.join(base_dir, 'css', 'header_2.css')) as f:
    header_2 = f.read()
with open(os.path.join(base_dir, 'css', 'sub_header.css'), 'r') as f:
    sub_header = f.read()
with open(os.path.join(base_dir, 'css', 'sub_header_left.css'), 'r') as f:
    sub_header_left = f.read()

# Headers candidate
candidate_headers = [
    {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36", "Accept-Language": "ko-KR,ko;q=0.8,en-US;q=0.5,en;q=0.3"},
    {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.102 Safari/537.36", "Accept-Language": "en-US,en;q=0.9"},
    {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:98.0) Gecko/20100101 Firefox/98.0", "Accept-Language": "en-US,en;q=0.5"}
]


# Create Air-pollution dictionary
@st.cache_data(show_spinner= False)
def emission_dict(country_df):
    final_dict = dict()
    for emission in country_df.columns[3:].tolist():
        country_df[emission] = country_df[emission].astype(float)
        if emission == 'SF6':
            final_dict[emission] = 'Sulfur Hexafluoride(SF6) can cause the lung disease'
        elif emission == 'HFCs':
            final_dict[emission] = 'Hydrofluorocarbons (HFCs) is Green House gas created by the usage of use in refrigeration and air-conditioning'
        elif emission == 'N2O':
            final_dict[emission] = 'Nitrous Oxide (N2O) can cause the brain damage'
        elif emission == 'NF3':
            final_dict[emission] = 'Nitrogen trifluoride (NF3) can cause the liver and kidney disease'
        elif emission == 'GHGs':
            final_dict[emission] = 'Green House Gas (GHGs) is the major cause of the global warming'
        elif emission == 'PFCs':
            final_dict[emission] = 'Perfluorochemicals (PFCs) is Green house gas created by the chemical activities'
        elif emission == 'CH4':
            final_dict[emission] = 'Methane (CH4) is Green house gas created by the usage of oil'
        elif emission == 'CO2':
            final_dict[emission] = 'Carbon dioxide (CO2) is the major part of Green house gas created by human industry activities'
        else:
            pass
    return final_dict

# ESG Metrics page
def esg():
    st.markdown(f'<div class="header">{header}ESG CCTV</div>', unsafe_allow_html=True)
    st.write('')
    option = option_menu(menu_title = None,
                         options = ["Environmental", "Social", "Governance"], 
                         orientation="horizontal", 
                        styles={
                            "container": {"padding": "0!important", "background-color": "#eee"},
                            "icon": {"color": "orange", "font-size": "20px"}, 
                            "nav-link": {"font-size": "20px", 
                                         "text-align": "center", 
                                         "margin":"5px", 
                                         "--hover-color": "#9eb3be",
                                         "color": "black"},
                            "nav-link-selected": {"background-color": "#043e76", "color": "white"},
                        },
                         key='esg_option')#
    st.write('')

    # Environmental
    if option == 'Environmental':
        st.markdown(f'<div class="header_2">{header_2}Global Air-Pollution CCTV</div>', unsafe_allow_html=True)
        st.write('')

        # Load data
        country_df = load_data('UNData_air_emission')
        country_df = country_df.replace('Null', None)
        country_df['year'] = pd.to_datetime(country_df['year'], format='%Y')
        
        # Inputs
        country_list = sorted(country_df['country'].unique())
        emission_list = sorted(country_df.columns[3:].tolist())
        emission_dictionary = emission_dict(country_df)
        
        # Show country level data
        with st.expander(label = '*Historical Air pollution level by Countries*', expanded = True):
            col1, col2 = st.columns(2)
            with col1:
                countries = st.multiselect(label = "Country selections",
                                        options = country_list,
                                        default = country_list[0:3])
            with col2:
                emission = st.selectbox(label = 'Air Emission type',
                                        options = emission_list)
                st.write(emission_dictionary[emission])
            
            # Filtering 
            country_df_filtered = country_df[(country_df['country'].isin(countries))]
            country_df_filtered[emission] = country_df_filtered[emission].astype(float)
            country_df_filtered = country_df_filtered[['country', 'year', emission]]
            st.write('')

            # Visulalizations            
            st.markdown(f'<div style="text-align: center; font-size: 30px; font-weight: bold;">Historical Trends</div>', unsafe_allow_html=True)
            summary_line_fig = px.line(country_df_filtered, x='year', 
                    y= emission, 
                    color = 'country',
                    labels={'year': 'year', 'value': 'Values'}, 
                    markers=True
                    )
            st.plotly_chart(summary_line_fig, use_container_width = True)

            # Show world map
            country_df_filtered_map = country_df[country_df[emission].notnull()]
            country_df_filtered_map = country_df_filtered_map.groupby('country').agg({
                emission: 'mean'
            })
            country_df_filtered_map[emission] = country_df_filtered_map[emission].astype(float)
            country_df_filtered_map = country_df_filtered_map.reset_index(drop = False)

            st.markdown(f'<div style="text-align: center; font-size: 30px; font-weight: bold;">World Map</div>', unsafe_allow_html=True)
            fig = px.choropleth(country_df_filtered_map, 
                                locations='country', locationmode='country names', 
                                color=emission,
                                color_continuous_scale="YlOrRd", 
                                range_color=(0, country_df_filtered_map[emission].max()),
                                labels={'value': 'Value'},
                                )
            st.plotly_chart(fig, use_container_width = True)

        # Show Korea data
        st.markdown(f'<div class="header_2">{header_2}Korea Air-pollution CCTV</div>', unsafe_allow_html=True)

        # load data
        kr_data = load_data('korea_air_emission')
        with st.expander(label = '*Air emission level in Korea*', expanded = True):
            col1, col2 = st.columns(2)
            analysis_type_list = ['Green House Gas emission level', 
                                  'Energy Usage level',
                                  'Energy Efficiency level']
            with col1:
                analysis_type_field = st.selectbox(label = 'Choice of Fields', options = ['Industry', 'Companies'], key = 'fields')
                analysis_type_metrics = st.selectbox(label = 'Choice of metrics', options = analysis_type_list, key = 'metrics')
            index_col = ''
            if analysis_type_field == 'Industry':
                index_col = 'industry'
            elif analysis_type_field == 'Companies':
                index_col = 'company'
            
            # Transforming
            kr_data_2 = kr_data[[index_col, 'GHG_emission_amount', 'energy_usage_TJ', 'energy_efficiency_rate']].reset_index(drop = True)
            metrics_columns = kr_data_2.columns[1:].tolist()
            kr_data_2[metrics_columns] = kr_data_2[metrics_columns].astype(float)
            kr_data_2 = kr_data_2.groupby(index_col, as_index=False).agg({'GHG_emission_amount': 'sum', 'energy_usage_TJ': 'sum', 'energy_efficiency_rate': 'mean'}).reset_index(drop = True)
            kr_data_2 = kr_data_2.rename(columns={'energy_efficiency_rate': 'avg_energy_efficiency_rate'})
            
            # define columns
            if analysis_type_metrics == 'Green House Gas emission level':
                metrics_col = 'GHG_emission_amount'
            elif analysis_type_metrics == 'Energy Usage level':
                metrics_col = 'energy_usage_TJ'
            elif analysis_type_metrics == 'Energy Efficiency level':
                metrics_col = 'avg_energy_efficiency_rate'

            kr_data_2 = kr_data_2[[index_col, metrics_col]].sort_values(by = metrics_col, ascending = False).reset_index(drop = True)
            kr_data_2.index = kr_data_2.index + 1

            with col2:
                st.dataframe(kr_data_2, use_container_width = True)

    # Social
    elif option == 'Social':
        st.markdown(f'<div class="header_2">{header_2}Global Culture CCTV</div>', unsafe_allow_html=True)
        text = '''
        The Following section was built to compare the ***'Relative'*** cultural differences between countries based on the research by Erin Meyer. 
        
        
        [Erin Meyer](https://erinmeyer.com/), a professor at INSEAD Business School, has dedicated her academic carrer on researching ****"how the global companies manage the gloal team"****.
        
        
        As the result, she succeeded in organizing the 8 areas of the culture differences around the world that the global company has focused on to build the global team. 
        
        
        Through the book "The Culture Map", professor Meyer summarized how 20+ countries are ***Relatively*** difference in 8 areas, and this section is built to provide the summarization of the professor Meyer's findings.

        '''

        with st.expander(label = 'Base logisticss', expanded = True):
            col1, col2, col3 = st.columns([4,3,4])
            with col2:
                st.image(os.path.join(base_dir, 'image', 'culture_map.jpg'), use_container_width= True, caption = 'Culture Map by Erin Meyer')
            st.markdown(text)
            st.write('')
        
        # Prepare data
        culture_map_df = load_data('culture_map')
        country_list = sorted(culture_map_df['country'].unique())
        with st.expander(label = '', expanded = True):
            col1, col2 = st.columns(2)
            with col1:
                country_1 = st.selectbox(label = 'First country',
                                     options = country_list)
            with col2:
                country_list_2 = country_list
                country_list_2.remove(country_1)
                country_2 = st.selectbox(label = 'Second country',
                        options = country_list_2)
            
            # Prepare dataset
            country_combo = [country_1, country_2]
            culture_map_df = culture_map_df[culture_map_df['country'].isin(country_combo)].reset_index(drop = True)

            output_dict = dict()
            for col in culture_map_df.columns[1:].tolist():
                output_dict[col] = dict()
                culture_map_df_2 = culture_map_df[['country', col]].sort_values(by = col, ascending = False).reset_index(drop = True)
                output_dict[col]['country'] = culture_map_df_2['country'][0]

                # differences
                metrics_difference = culture_map_df_2[col][0] - culture_map_df_2[col][1]
                if metrics_difference > 8:
                    output_dict[col]['difference'] = '**:red[MUCH]**'
                elif (metrics_difference >= 4) and (metrics_difference <= 8):
                    output_dict[col]['difference'] = '**:blue[LITTLE]**'
                else: 
                    output_dict[col]['difference'] = None
                
                # context
                if col == 'Indirect_communication_level':
                    output_dict[col]['context'] = 'communicate important messages indirectly'
                elif col == 'direct_negative_feedback':
                    output_dict[col]['context'] = 'give negative feedback more directly'
                elif col == 'flexible_scheduling':
                    output_dict[col]['context'] = 'schedule the meeting times more flexibly'
                elif col == 'hierarchical_culture':
                    output_dict[col]['context'] = 'have more hierarchical culture'
                elif col == 'avoid_confrontation':
                    output_dict[col]['context'] = 'prefer avoiding the confrontation during the meeting'
                elif col == 'relation_focused':
                    output_dict[col]['context'] = 'put more importance in building the relationship outside of working space'
                elif col == 'theory_first_approach':
                    output_dict[col]['context'] = 'discuss more deeply about the accruacy of the theory before making the decision'
                elif col == 'top_down_decision_making':
                    output_dict[col]['context'] = 'have the top down decision making process'

            output_dict = {k: v for k, v in output_dict.items() if v['difference'] is not None}
            country_1_txt = ''
            country_2_txt = ''
            for k, v in output_dict.items():
                if v['country'] == country_1:
                    country_1_txt +=  f"\n - {v['difference']} higher tendency to *{v['context']}*."
                else:
                    country_2_txt +=  f"\n - {v['difference']} higher tendency to *{v['context']}*."
            # text = f"""
            # Followings are summary of the culture differences between **{country_1}** and **{country_2}**:
            # """
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f'<div style="text-align: center; font-size: 20px; font-weight: bold;">{country_1}</div>', unsafe_allow_html=True)
                st.markdown(country_1_txt)
            with col2:
                st.markdown(f'<div style="text-align: center; font-size: 20px; font-weight: bold;">{country_2}</div>', unsafe_allow_html=True)
                st.markdown(country_2_txt)

            # st.markdown(text)

    # Governance
    elif option == 'Governance':
        
        # Setup session state
        if 'run' not in st.session_state:
            st.session_state['run'] = False
        if 'journalist' not in st.session_state:
            st.session_state['journalist'] = 'None'

        st.markdown(f'<div class="header_2">{header_2}Media Governance CCTV</div>', unsafe_allow_html=True)
        with st.expander(label = '*Background of the Project*', expanded = True):

            col1, col2, col3 = st.columns([3,4,3])
            with col2:
                st.image(os.path.join(base_dir, 'image', 'media_governance.png'), use_container_width= True, caption = 'https://partnershiponai.org/program/ai-media-integrity/')
            text = '''
            **"Governance"** has a meaning of [the act or process of governing or overseeing the control and direction of something]. And, I believe that "the Media" is taking a majority the governance in the modern socity. 
            
            However, with the popularity of SNS, the media integrety seemed to be decreasing due to few "bad" journalists. Therefore, I decided to build the system where people can analyze ****"the charcteristics of journalists"**** with the help of AI.  

            With this section, you will be able to have visibility on characteristics of the selected journalists with the help of AI. Even if the section is only covering few media currently, it will expand the coverage gradually. Hope this experiment can contribute in increasing the quality of ***Media Governance***.
            '''
            st.markdown(text, unsafe_allow_html= True)
        
        with st.expander(label = '**Media Governance CCTV**', expanded = True):
            journalists_df = load_data('journalist_contents')
            journalists_info_df = load_data('journalists')
            col1, col2, col3 = st.columns(3)
            with col1:
                # Get the media list
                media_company_list = journalists_df['company'].unique().tolist()
                media_company_list = [x for x in media_company_list if len(x) > 0]
                media_company_list.sort()
                media_company_option = st.selectbox(label = "Media Companies", 
                                                    options = media_company_list,
                                                    key = 'media_company_list')
            with col2:    
                # Get the journalist list
                journalists_df_2 = journalists_df[journalists_df['company'] == media_company_option].reset_index(drop = True)
                journalist_list = journalists_df_2['journalist'].unique().tolist()
                journalist_list.sort()
                journalist_option = st.selectbox(label = "Journalist", options = journalist_list, key = 'journalist_list')
            
            with col3:
                language_option = st.selectbox(label = 'Answer Language', options = ['English', 'Korean'], key = 'language')
            
            # Get the filtered data sets
            journalists_info_df_2 = journalists_info_df[(journalists_info_df['journalist'] == journalist_option) & 
                                                        (journalists_info_df['company'] == media_company_option)].reset_index(drop = True)
            
            # Show description
            journalist_desc = f"""
            email: {journalists_info_df_2['e-mail'][0]}                
            
            department: {journalists_info_df_2['department'][0]}
            """
            st.markdown(journalist_desc)
        
        # Journalist Summary
        col1, col2, col3 = st.columns([4,2,4])
        with col1:
            if st.button('Analyze the selected journalist', key = 'analyze', type = "primary", use_container_width = True):
                st.session_state['run'] = True
                st.session_state['journalist'] = journalist_option
                # st.session_state['language'] = language_option
        with col3:
            if st.button('Reset the answer', key = 'reset', use_container_width = True):
                st.session_state['run'] = False
                st.session_state['journalist'] = 'None'
        
        if (st.session_state['run'] == True) and (st.session_state['journalist'] == journalist_option):
            with st.status("AI is running..."):
                journalists_df_3 = journalists_df_2[(journalists_df_2['journalist'] == journalist_option)].reset_index(drop =True)
                journalists_df_3['merged_text'] = journalists_df_3.apply(lambda row: f"{row['headline']} [{row['description']}]", axis=1)
                all_desc = journalists_df_3['merged_text'].str.cat(sep=' ')
                response = journalist_summary(all_desc, language_option)
                
            # Generate response
            if response != None:
                st.write_stream(stream_data(response))
            else:
                st.write(response)
                st.warning("Would you try again?")

def Korea():

    # Load the app data
    app_data = load_data(sheet_name = 'naver')

    # Header
    st.markdown(f'<div class="header">{header}Korea Toolkits</div>', unsafe_allow_html=True)
    st.write('')

    # Option Menu to select the option
    option = option_menu(menu_title = None,
                         options = ["Naver Blog Trends", "Coupang Pricing"], 
                         orientation="horizontal",
                        styles={
                            "container": {"padding": "0!important", "background-color": "#eee"},
                            "icon": {"color": "orange", "font-size": "20px"}, 
                            "nav-link": {"font-size": "20px", 
                                         "text-align": "center", 
                                         "margin":"5px", 
                                         "--hover-color": "#9eb3be",
                                         "color": "black"},
                            "nav-link-selected": {"background-color": "#043e76", "color": "white"},
                        },
                         key='naver_option')
    st.write('')
    
    # Naver Blog
    if option == 'Naver Blog Trends':
        st.markdown(f'<div class="header_2">{header_2}When people search my keywords most in Naver Blog?</div>', unsafe_allow_html=True)
        st.write('')
        st.write('')

        # Inputs
        topics = sorted(app_data['topics'].tolist())

        with st.expander(label = '', expanded = True):
            col1, col2 = st.columns(2)
            with col1:
                groupName = st.selectbox('Please choose topics', options = topics, key = 'groupName')
                keywords = st.text_input('Please write Keywords', value = '네이버', key = 'keywords')
            with col2: 
                startDate = st.date_input(label = "Start Date", 
                                        value = datetime.date(2023, 1, 1), 
                                        min_value = datetime.date(2020, 1, 1),
                                        max_value = datetime.date.today(),
                                        key = 'startdate')
                
                endDate = st.date_input(label = "End date", 
                                        value = datetime.date.today() ,
                                        min_value = datetime.date(2020, 1, 1),
                                        max_value = datetime.date.today(),
                                        key = 'end_date')
        st.write('')
        st.write('')
    
        # Organize inputs as dictionary
        input_dict = dict()
        input_dict['groupName'] = groupName
        input_dict['keywords'] = [x.strip() for x in keywords.split(",")]
        input_dict['startDate'] = startDate
        input_dict['endDate'] = endDate

        # Setup 'Run' Status
        run = False        
        response_check = check_null_values(input_dict)

        # App running logistics
        if response_check == True:
            run = True
        elif response_check== False:
            st.warning("Please insert Topics and Keywords")
            run = False

        # Run the program
        if run == True:
            # https://developers.naver.com/docs/serviceapi/datalab/search/search.md#%ED%8C%8C%EB%9D%BC%EB%AF%B8%ED%84%B0
           
            naver_search_result(input_dict, groupName, keywords)
    
    # Coupang
    elif option == 'Coupang Pricing':
        st.markdown(f'<div class="header_2">{header_2}What is the average price of my item in Coupang?</div>', unsafe_allow_html=True)
        st.write('')
        if hostname == 'hanchaeyun-ui-iMac.local':            
            col1, col2 = st.columns(2)
            with col1: 
                # Item name insert
                with st.expander(label = '', expanded = True):
                    _item = st.text_input('Please type item name', value = '맥북', key = 'coupang')
            with col2:
                coupang_df = coupang_scrape(_item)
                average_price = round(coupang_df['price'].mean())
                average_price = format_amount(average_price)
                if coupang_df['unit_price'].isnull().all():
                    average_unit_price = 'Not Available'
                else:
                    average_unit_price_num = round(coupang_df['unit_price'].mean(),2)
                    average_unit_price_num = format_amount(average_unit_price_num)
                    average_unit_price = f"{average_unit_price_num}원"
                #
                text = f'''
                Analyzed Items: {len(coupang_df)}<br> Average price: {average_price}원<br>Average Unit Price : {average_unit_price}
                '''
                st.markdown(f'<div class="sub_header_left">{sub_header_left}{text}</div>', unsafe_allow_html=True)
                #st.markdown(text, unsafe_allow_html= True)
            st.write('')
            with st.expander(label = f'**Total Data**', expanded = True):

                if coupang_df['unit_price'].isnull().all():
                    st.data_editor(
                            coupang_df[['item_name', 'price', 'link']],
                            column_config={
                                "item_name": st.column_config.TextColumn('item_name'),
                                "price": st.column_config.NumberColumn(
                                    "price",
                                    format="%d원"
                                ),
                                "link": st.column_config.LinkColumn(
                                    "링크",
                                    max_chars=100,
                                    display_text= "Coupang Link"
                                ),
                            },
                            hide_index=False,
                            use_container_width = True
                        )
                else:
                    st.data_editor(
                            coupang_df[['item_name', 'price', 'unit_price', 'link']],
                            column_config={
                                "item_name": st.column_config.TextColumn('item_name'),
                                "price": st.column_config.NumberColumn(
                                    "price",
                                    format="%d원"
                                ),
                                "unit_price": st.column_config.NumberColumn(
                                    "unit_price",
                                    format="%d원"
                                ),
                                "link": st.column_config.LinkColumn(
                                    "링크",
                                    max_chars=100,
                                    display_text= "Coupang Link"
                                ),
                            },
                            hide_index=False,
                            use_container_width = True,  
                        )
        else:       
            st.warning("Due to Coupang's proxy-security program, the current system only runs in the local environment. Please reach out to pjhan94@gmail.com", icon = "🥲")
            # Demo video
            with st.expander(label = "demo video", expanded = True):
                st.video(os.path.join(base_dir, 'video', 'coupang_demo.mov'), format = "video/mp4", loop = True, autoplay = True)
        
def GRI():
    st.markdown(f'<div class="header">{header}GRI Cheat Sheet</div>', unsafe_allow_html=True)
    st.write('')
    option = option_menu(menu_title = None,
                         options = ["What is GRI?", "GRI Content Index Builder"], 
                         orientation="horizontal", 
                        styles={
                            "container": {"padding": "0!important", "background-color": "#eee"},
                            "icon": {"color": "orange", "font-size": "20px"}, 
                            "nav-link": {"font-size": "20px", 
                                         "text-align": "center", 
                                         "color": "black",
                                         "margin":"5px", 
                                         "--hover-color": "#9eb3be"},
                            "nav-link-selected": {"background-color": "#043e76", "color": "white"},
                        },
                         key='GRI_Options')#
    st.write('')

    if option == "What is GRI?":
        text = """
        <div style="text-align:center">
        <h3>What is GRI?</h3>
        </div>

        The Global Reporting Initiative (GRI) is an independent international organization that provides a comprehensive framework for sustainability reporting, which is widely used by organizations to disclose their environmental, social, and governance (ESG) impacts. 

        The GRI Standards are designed to help businesses, governments, and other organizations understand and communicate their impacts on critical sustainability issues such as climate change, human rights, governance, and social well-being.

        <div style="text-align:center">
        <h3>What logistics does GRI use?</h3>
        </div>

        The GRI Standards are organized into three types: **Universal Standards, Sector Standards, and Topic Standards**. 
        
        In summary, all organizations start with the Universal Standards, then use the Sector Standards relevant to their industry, and finally, the Topic Standards based on their material topics.

        """

        st.markdown(text, unsafe_allow_html = True)
        st.write("")
        col1, col2, col3 = st.columns([2,5,2])
        with col2:
            st.image(
                os.path.join(base_dir, 'image', 'gri_logistics.png'), use_container_width = True)
        st.write("")

        text_2 = """
        <div style="text-align:center">
        <h3>What are steps to write ESG reports using GRI Standards?</h3>
        </div>
        
        ##### Step 1: Fill in the GRI content index
        Download [GRI content index template](https://www.globalreporting.org/reporting-support/reporting-tools/content-index-template/) and fill in the sheets based on the [GRI Guidelines](https://www.globalreporting.org/standards/download-the-standards/).

        In this app, the **"GRI Content Index Builder"** will do the job for you.

        ##### Step 2: Publish GRI Index and Reports
        Publish the [GRI content index template](https://www.globalreporting.org/reporting-support/reporting-tools/content-index-template/) and Reports while include a statement in the content index that the report is in accordance with the GRI Standards.

        *Ex. ‘ABC Limited has reported in accordance with the GRI Standards for the period from 1 January 2022 to 31 December 2022.’*

        ##### Step 3: Publication and Communication
        Inform GRI (reportregistration@globalreporting.org) by email while including the following elements in the email. 

        - The legal name of the organization.
        - The link to the GRI content index.
        - The link to the report, if publishing a standalone sustainability report.
        - The statement of use.
        - A contact person in the organization and their contact details.

        """

        st.markdown(text_2, unsafe_allow_html = True)
        st.write('')

    elif option == "GRI Content Index Builder":
        # Open and load the JSON file
        with open(
            os.path.join(base_dir, 'etl', 'gri_summary.json'), 'r') as file:
            gri_data = json.load(file)

        # Now `data` is a Python dictionary containing the JSON data
        @st.cache_data
        def lev_listing(input:None, input2:None , data, option):
            final_list = list()
            # GRI Standards
            if option == 'lv1':
                for lev_1 in data:
                    final_list.append(lev_1)

            # GRI sub-Standards
            elif option == 'lv2':
                data = data.get(input)
                for lev_2 in data:
                    final_list.append(lev_2)

            elif option == 'lv3':
                data = data.get(input)
                data = data.get(input2)
                final_list = data

            return final_list
        st.markdown(f'<div class="header_2">{header_2}Choose Standards</div>', unsafe_allow_html=True)
        with st.expander(label = '', expanded = True):
            lev_1_list = lev_listing(data = gri_data, option = 'lv1', input = None, input2 = None)
            
            lev_1_choice = st.selectbox(label = "**Select GRI standards**", options = lev_1_list, key = 'lev1')

            lev_2_list = lev_listing(data = gri_data, option = 'lv2', input = lev_1_choice, input2 = None)
            lev_2_choice = st.selectbox(label = "**Select GRI Sub Standards**", options = lev_2_list, key = 'lev2')

        st.markdown(f'<div class="sub_header">{sub_header}Below are questions to answer for <br> "{lev_2_choice}"</div>', unsafe_allow_html=True)
        questions = lev_listing(data = gri_data, option = 'lv3', input = lev_1_choice, input2 = lev_2_choice)

        for topic in questions:
            st.markdown(f'#### {topic}')
            for question in questions[topic]:
                st.markdown(f'- {question}')

def Youtube():

    # Header
    st.markdown(f'<div class="header">{header}Youtube Analyzer</div>', unsafe_allow_html=True)
    st.write('')
    
    with st.expander(label = '', expanded = True):
        channel_name = st.text_input(label = 'Type in name of Youtube Channel', key = 'youtube')
        number_of_videos = st.number_input(label = "Select the number of videos to analyze (maximum 100)", 
                                           min_value = 1, 
                                           max_value = 100, 
                                           value = 20, 
                                           key = 'video_number')
        col1, col2, col3 = st.columns([4,2,4])
        with col1:
            if st.button(label = 'Run', 
                         type = 'primary', 
                         use_container_width = True,
                         key = 'button'):
                st.session_state['youtube_run'] = True
        with col3:
            if st.button(label = 'Re-set', 
                         use_container_width = True,
                         key = 'button_2'):
                st.session_state['youtube_run'] = False
        
    if (len(channel_name) > 0) & (st.session_state['youtube_run'] == True): 
        try: 
            with st.status("Scrapping Youtube Information..."):
                @st.cache_data(ttl = 60*60*24*2 # 2 days
                , show_spinner=False)
                def youtube_anaylze(channel_name, number_of_videos):
                    channel_name = channel_name.replace(' ', '-')
                    agent = YoutubeAnalyzer(channel_name = channel_name, 
                                            number_of_videos = number_of_videos)
                    agent.run()
                    return agent
                agent = youtube_anaylze(channel_name, number_of_videos)
            if agent.status == 4:
                with st.expander(label = 'Youtuber Information', expanded = True):
                    col1, col2 = st.columns([3,7])
                    with col1:
                        st.image(agent.thumbnail)
                    with col2:
                        st.write(agent.channel_title)
                        st.write(agent.channel_description)
                    st.write("")
                    questions = st.text_input(label = "Ask any questions about this youtube channel", key = "questions")  
                    
                    if st.button(label = 'Ask question to AI'):
                        if len(questions) >0:  
                            script = f"""
                            I want to know '{questions}' about the {agent.channel_title} youtube channel.
                            Based on the following video trasnscripts of the channel, answer my questions: {agent.total_transcripts_txt}"""
                            with st.spinner('AI is running...'):
                                response = gemini_run(script)
                                if len(response) > 0:
                                    st.write_stream(stream_data(response))
                        else:
                            st.warning('Please type in questions')
            else:
                st.warning(f"pipeline ran incorrectly during the {agent.status} stage: {agent.error_message}")

        except Exception as e:
            st.error(e)



 
   ##
#