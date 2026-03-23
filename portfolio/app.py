import sys, ssl, os
import pandas as pd
import streamlit as st
from streamlit_option_menu import option_menu
import functions as fu

# # Fix SSL issues if needed (unrelated to file reading)
# ssl._create_default_https_context = ssl._create_stdlib_context

# Determine the base directory where the script is located
base_dir = os.path.dirname(os.path.abspath(__file__))

#source venv/bin/activate

st.set_page_config(
    page_title = "PJ's Portfolio", # chorm tab title
    page_icon=os.path.join(base_dir,'logo.png'),
    layout="wide" # can be horizontal
    )
if 'reset_status' not in st.session_state:
    st.session_state['reset_status'] = False
else:
    pass

if 'youtube_run' not in st.session_state:
    st.session_state['youtube_run'] = False

# Side bar
with st.sidebar:
    col1, col2, col3 = st.columns([2,8,2])
    with col2:
        st.image(os.path.join(base_dir,'logo.png'))

    st.markdown(f'<div style="text-align: center; font-size: 30px; font-weight: bold;">Welcome!</div>', unsafe_allow_html=True)
    st.write('')
    # Create the option menu
    
    option = option_menu("",
                         ["GRI Cheat Sheet", 'ESG CCTV', "Korea Toolkits"
                          #, "Youtube Analyzer (Beta)"
                          ], 
                        icons=['pen', 'globe-americas', 'clipboard2-data-fill'], 
                        styles={
                            "container": {"padding": "0!important", "background-color": "white"},
                            "icon": {"font-size": "25px"}, 
                            "nav-link": {"font-size": "20px", "text-align": "left", "margin":"5px", 
                                         "--hover-color": "#e2e2e9", 
                                         "color": "black"},
                            "nav-link-selected": {"background-color": "black", "color": "white"},
                        },
                        default_index=0)

    # Buttons to Link
    st.write("")
    col1, col2 = st.columns([4,4])
    with col1:
        # Display the button
        st.link_button(label = ":blue[LinkedIn]", url = "https://www.linkedin.com/in/pjhan94/", use_container_width= True)
    with col2:
        st.link_button(label = ":green[Website]", url = "https://pjhan94.wixsite.com/pjhan", use_container_width= True)

# Main menu
if option == 'ESG CCTV':
    fu.esg()
elif option == 'Korea Toolkits':
    fu.Korea()
elif option == 'GRI Cheat Sheet':
    fu.GRI()
# elif option == 'Youtube Analyzer (Beta)':
#     fu.Youtube()