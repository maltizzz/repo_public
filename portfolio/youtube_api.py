import requests
from pprint import pprint
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound, CouldNotRetrieveTranscript
from stqdm import stqdm
import datetime
import os
import ssl
from dotenv import load_dotenv
import streamlit as st

# Environment settings
base_dir = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(os.path.dirname(base_dir), '_secrets', '.env'))
secret_path = os.path.join(os.path.dirname(base_dir), '_secrets', 'pj_han_official.json')


class YoutubeAnalyzer:
    def __init__(self, channel_name, number_of_videos):
        # Get API key from env or streamlit secrets
        self.API_KEY = os.getenv('YOUTUBE_API_KEY') or st.secrets.get('YOUTUBE_API_KEY')
        self.channel_name = channel_name.lower().replace(" ", "")
        self.number_of_videos = number_of_videos
        self.status = 0
        self.error_message = None
        self.video_details = {}
        self.total_transcripts_txt = ''

    def search_channel_by_name(self):
        url = f'https://www.googleapis.com/youtube/v3/search?part=snippet&type=channel&q={self.channel_name}&key={self.API_KEY}'
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            if data.get('items'):
                channel_info = data['items'][0]['snippet']

                self.channel_id = data['items'][0]['snippet']['channelId']
                self.channel_title = channel_info.get('channelTitle', '')
                self.channel_description = channel_info.get('description', '')
                self.thumbnail = channel_info.get('thumbnails', {}).get('default', {}).get('url', '')

                self.status = 1
            else:
                self.error_message = "No channel found."
        else:
            self.error_message = f"API error: {response.status_code} - {response.text}"

    def get_uploads_playlist_id(self):
        if self.status != 1:
            return
        url = f'https://www.googleapis.com/youtube/v3/channels?part=contentDetails&id={self.channel_id}&key={self.API_KEY}'
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            if data.get('items'):
                self.playlist_id = data['items'][0]['contentDetails']['relatedPlaylists']['uploads']
                self.status = 2
            else:
                self.error_message = "Channel details not found."
        else:
            self.error_message = f"API error: {response.status_code} - {response.text}"

    def get_video_info_from_channel(self):
        if self.status != 2:
            return
        url = f'https://www.googleapis.com/youtube/v3/playlistItems?part=snippet&playlistId={self.playlist_id}&maxResults={self.number_of_videos}&key={self.API_KEY}'
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            if data.get('items'):
                video_details = {}
                for item in data['items']:
                    snippet = item['snippet']
                    title = snippet.get('title', '')
                    video_id = snippet.get('resourceId', {}).get('videoId', '')
                    published_at = snippet.get('publishedAt', '')

                    if title and video_id:
                        video_details[title] = {
                            'id': video_id,
                            'publishedAt': published_at,
                        }
                # Sort videos by published date descending
                video_details = dict(sorted(
                    video_details.items(),
                    key=lambda x: datetime.datetime.fromisoformat(x[1]['publishedAt'].replace('Z', '+00:00')),
                    reverse=True
                ))
                # Limit to number_of_videos
                self.video_details = dict(list(video_details.items())[:self.number_of_videos])
                self.status = 3
            else:
                self.error_message = "No videos found in playlist."
        else:
            self.error_message = f"API error: {response.status_code} - {response.text}"

    def get_video_transcription(self):
        if self.status != 3:
            return

        supported_langs = [
            'en', 'ko', 'af', 'ak', 'sq', 'am', 'ar', 'hy', 'as', 'ay', 'az', 'bn', 'eu', 'be', 'bho',
            'bs', 'bg', 'my', 'ca', 'ceb', 'zh-Hans', 'zh-Hant', 'co', 'hr', 'cs', 'da', 'dv', 'nl',
            'eo', 'et', 'ee', 'fil', 'fi', 'fr', 'gl', 'lg', 'ka', 'de', 'el', 'gn', 'gu', 'ht', 'ha',
            'haw', 'iw', 'hi', 'hmn', 'hu', 'is', 'ig', 'id', 'ga', 'it', 'ja', 'jv', 'kn', 'kk', 'km',
            'rw', 'ko', 'kri', 'ku', 'ky', 'lo', 'la', 'lv', 'ln', 'lt', 'lb', 'mk', 'mg', 'ms', 'ml',
            'mt', 'mi', 'mr', 'mn', 'ne', 'nso', 'no', 'ny', 'or', 'om', 'ps', 'fa', 'pl', 'pt', 'pa',
            'qu', 'ro', 'ru', 'sm', 'sa', 'gd', 'sr', 'sn', 'sd', 'si', 'sk', 'sl', 'so', 'st', 'es',
            'su', 'sw', 'sv', 'tg', 'ta', 'tt', 'te', 'th', 'ti', 'ts', 'tr', 'tk', 'uk', 'ur', 'ug',
            'uz', 'vi', 'cy', 'fy', 'xh', 'yi', 'yo', 'zu'
        ]

        filtered_videos = {}

        for title, info in stqdm(self.video_details.items(), desc='Getting transcripts'):
            video_id = info['id']
            try:
                transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
                # Try to find manual transcript first
                transcript = None
                try:
                    transcript = transcript_list.find_transcript(supported_langs)
                except NoTranscriptFound:
                    # If no manual transcript, try autogenerated
                    transcript = transcript_list.find_generated_transcript(supported_langs)
                
                # If transcript found and translatable, translate to English
                if transcript and transcript.is_translatable:
                    transcript = transcript.translate('en')
                
                transcription_text = ' '.join([entry['text'] for entry in transcript.fetch()])
                transcription_text = transcription_text.replace('\n', ' ').strip()
                
                self.video_details[title]['transcript'] = transcription_text

            except (TranscriptsDisabled, NoTranscriptFound, CouldNotRetrieveTranscript):
                # No transcript available
                continue
            except Exception as e:
                st.write(f"Error getting transcript for video {video_id}: {e}")
                continue

        self.video_details = filtered_videos

        if self.video_details:
            self.total_transcripts_txt = ' '.join([v['transcript'] for v in self.video_details.values()])
            if self.total_transcripts_txt:
                self.status = 4
            else:
                self.error_message = "No transcripts fetched"
        else:
            self.error_message = "No videos with transcripts found"

    def run(self):
        self.search_channel_by_name()
        if self.status != 1:
            return

        self.get_uploads_playlist_id()
        if self.status != 2:
            return

        self.get_video_info_from_channel()
        if self.status != 3:
            return

        self.get_video_transcription()

# Usage example:
# agent = YoutubeAnalyzer(channel_name='쯔양', number_of_videos=20)
# agent.run()
# print(agent.total_transcripts_txt)
