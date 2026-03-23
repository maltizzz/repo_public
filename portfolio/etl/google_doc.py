from google.oauth2 import service_account
from googleapiclient.discovery import build
import re, pygsheets
import pandas as pd

import json

def extract_text_between_words(content, start_word, end_word):
    # Use regular expression to find text between start_word and end_word
    pattern = re.compile(f'{start_word}(.*?){end_word}', re.DOTALL)
    match = pattern.search(content)
    if match:
        return match.group(1).strip()
    else:
        return None

def pd_to_gsheet(df):
    # Load the credentials file
    gc = pygsheets.authorize(service_file='SECRET')

    # Open the Google Sheet (by title)
    sh = gc.open_by_key('SECRET')

    # Select the first sheet
    wks = sh.worksheet_by_title('gri_glossary')
    wks.clear()

    # Post the DataFrame to the Google Sheet
    wks.set_dataframe(df, (1, 1))  # (1, 1) specifies the starting cell (A1)



def check_GRI(text):
    pattern = re.compile(r'\bGRI\b', re.IGNORECASE)
    return bool(pattern.search(text))

def is_all_uppercase(text):
    # Define the regex pattern
    pattern = r'^[A-Z\s\W\d]*$'
    
    # Check if the entire text matches the pattern
    return bool(re.fullmatch(pattern, text))

def text_to_nested_dictionary(text):
    
    lines = text.split('\n')
    lines_dict = dict()
    for line in lines:
        try:
            depth = line.index('*')//3
            lines_dict[line.strip().replace('*','').strip()] = depth
        except:
            pass
    
    final_dict = dict()
    core = ''
    section_1 = ''
    section_2 = ''
    section_3 = ''

    for index, (key, number) in enumerate(lines_dict.items()):
        if number == 0 and check_GRI(key):
            final_dict[key] = dict()
            core = key
            section_1 = ''
            section_2 = ''
            section_3 = ''
        elif number == 1 and (key != ''):
            final_dict[core][key] = dict()
            section_1 = key
            section_2 = ''
            section_3 = ''
        elif number == 2 and (section_1 != ''):
            final_dict[core][section_1][key] = dict()
            section_2 = key
            section_3 = ''
        elif number == 3 and (section_2 != ''):
            final_dict[core][section_1][section_2][key] = ''
            section_3 = key
        elif number ==4 and (section_3 != ''):
            final_dict[core][section_1][section_2][section_3] = dict()
            final_dict[core][section_1][section_2][section_3][key] = ''

    return final_dict
def google_doc_etl(document_id):
    # Authenticate with Google Drive API using service account credentials
    credentials = service_account.Credentials.from_service_account_file(
        'SECRET',
        scopes=['https://www.googleapis.com/auth/drive.readonly']
    )
    service = build('drive', 'v3', credentials=credentials)

    # Retrieve the content of the Google Docs document
    document = service.files().export(fileId=document_id, mimeType='text/plain').execute()
    
    document = document.decode('utf-8')
    
    return document

def save_to_json(data, filename):
    with open(f"SECRET", 'w') as json_file:
        json.dump(data, json_file, indent=4)

def save_to_text(text, file_name):
    with open(f"SECRET", 'w') as file:
        file.write(text)

def main():
    # Read the content of the Google Docs document (replace this with your method of retrieval)
    content = google_doc_etl('SECRET')
    # Extract text between start_word and end_word
    extracted_text = extract_text_between_words(content, 'Section 1-1: General disclosures', 
                                                'Step 2: Publish GRI Index')
    save_to_text(extracted_text, "google_doct.txt")
    if extracted_text:
        extracted_dict = text_to_nested_dictionary(extracted_text)
        save_to_json(extracted_dict, 'gri_summary.json')
        df = pd.DataFrame(extracted_dict)
        pd_to_gsheet(df)
    else:
        print("No text extracted.")

if __name__ == '__main__':
    main()

