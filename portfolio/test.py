from youtube_api import YoutubeAnalyzer

agent = YoutubeAnalyzer(channel_name = 'ESPN', number_of_videos = 2)
agent.run()
print(agent.total_transcripts_txt)