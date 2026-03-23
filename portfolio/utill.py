from google.oauth2 import service_account
import time, ssl, os, json
import streamlit as st
import time, pygsheets
from googleapiclient.discovery import build
from dotenv import load_dotenv
from google import genai

# Environment settings
ssl._create_default_https_context = ssl._create_stdlib_context
base_dir = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(os.path.dirname(base_dir), '_secrets', '.env'))
secret_path = os.path.join(os.path.dirname(base_dir), '_secrets', 'pj_han_official.json')


# Function to convert text to stream
def stream_data(input_text):
    for word in input_text.split(" "):
        yield word + " "
        time.sleep(0.02)

# Load Gsheet data
@st.cache_data(ttl = 3600, show_spinner = False)
def load_data(sheet_name):
    gc = pygsheets.authorize(service_file=secret_path)
    # Open the Google Sheets spreadsheet by its URL
    spreadsheet_url = 'https://docs.google.com/spreadsheets/d/1xQbkWb0iVlYmNQO4DyjDCbrr6qVBNf9ptSG6uMJznnw'
    sh = gc.open_by_url(spreadsheet_url)

    # Select the worksheet by its title
    worksheet = sh.worksheet_by_title(sheet_name)

    # Read the data into a pandas DataFrame
    df = worksheet.get_as_df()
    return df

def load_data_not_cache(sheet_name):
    gc = pygsheets.authorize(service_file=secret_path)
    # Open the Google Sheets spreadsheet by its URL
    spreadsheet_url = 'https://docs.google.com/spreadsheets/d/1xQbkWb0iVlYmNQO4DyjDCbrr6qVBNf9ptSG6uMJznnw'
    sh = gc.open_by_url(spreadsheet_url)

    # Select the worksheet by its title
    worksheet = sh.worksheet_by_title(sheet_name)

    # Read the data into a pandas DataFrame
    df = worksheet.get_as_df()
    return df

def pd_to_gsheet(df, sheet_name):
    
    # Open the Google Sheet (by title)
    gc = pygsheets.authorize(service_file=secret_path)
    spreadsheet_url = 'https://docs.google.com/spreadsheets/d/1xQbkWb0iVlYmNQO4DyjDCbrr6qVBNf9ptSG6uMJznnw'
    sh = gc.open_by_url(spreadsheet_url)

    # Select the first sheet
    wks = sh.worksheet_by_title(sheet_name)
    
    # Post the DataFrame to the Google Sheet
    wks.clear()
    wks.set_dataframe(df, (1, 1))  # (1, 1) specifies the starting cell (A1)


@st.cache_data(show_spinner = False)
def check_null_values(dictionary):
    if (dictionary['groupName'] == '') or (dictionary['groupName'] == None):
        return False
    elif (len(dictionary['keywords']) == 1) and (dictionary['keywords'][0] == ''):
        return False
    else:
        return True

# Load Google doc
def google_doc_etl(document_id):
    
    # Authenticate 
    credentials = service_account.Credentials.from_service_account_file(
        secret_path,
        scopes=['https://www.googleapis.com/auth/drive.readonly']
    )
    service = build('drive', 'v3', credentials=credentials)

    # Retrieve the content of the Google Docs document
    document = service.files().export(fileId=document_id, mimeType='text/plain').execute()
    document = document.decode('utf-8')
    document = document.replace('\n', '  \n')
    
    return document

# Show Gfiles preview
def embed_google_doc_preview(url):
    st.markdown(f'<iframe src="{url}" width="100%" height="600" frameborder="0"></iframe>', unsafe_allow_html=True)

# Run Gemini
def gemini_run(question):
    question = question[:30000]
    # 2. Determine API Key (Prioritize Env Var, fallback to Streamlit Secrets)
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        try:
            api_key = st.secrets["GEMINI_API_KEY"]
        except FileNotFoundError:
            return "Error: API Key not found in env vars or st.secrets."

    # 3. Initialize Client (New SDK standard)
    client = genai.Client(api_key=api_key)
    # 4. Generate Content
    try: 
        response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=question
        )
        return response.text
    except Exception as e:
        return e
    

@st.cache_data(ttl = 60*60*24*2 # 2 days
                , show_spinner=False)
def journalist_summary(all_desc, language_option):
    all_desc = all_desc[:8000]
    try:
        response = gemini_run(f"Followings are the collection of headlines and description that one journalist wrote. Please Summarize [Tendencies, Pros and Cons] of the journalists in {language_option} while title to be 'Results of Media CCTV AI': {all_desc}")
    except Exception as e:
        response = None
    return response

def format_amount(amount):
    return '{:,.0f}'.format(amount)