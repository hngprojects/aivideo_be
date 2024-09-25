import requests, json, os
from bs4 import BeautifulSoup

from api.v1.services.ai_tools.general import general_service
from api.v1.services.ai_tools.pdf_summarizer import pdf_summary_service
from api.v1.services.ai_tools.audio_summarizer import audio_summary_service


class PodcastSummaryService:
    '''This is limited to only apple podcasts for now'''

    def fetch_page(self, url):
        response = requests.get(url)
        response.raise_for_status()
        return response.text
    
    
    def get_podcast_details(self, podcast_url: str):
        """Get the details of a podcast"""

        try:
            content = self.fetch_page(podcast_url)

            # Scrape url to get podcast data
            soup = BeautifulSoup(content, 'html.parser')
            apple_title_meta = soup.find('meta', attrs={'name': 'apple:title'})

            title = apple_title_meta['content']
            li_tags = soup.select('ul.metadata li')
            duration = li_tags[-2].text.strip()
            host = soup.select('img', attrs={'class': 'artwork-component__contents artwork-component__image svelte-3e3mdo'})
            host_name = host[1]['alt']

            return {
                "title": title,
                "duration": duration,
                "host": host_name
            }
        
        except Exception as e:
            raise e
        
    
    def extract_scripts_with_asseturl(self, url):
        try:
            content = self.fetch_page(url)
            soup = BeautifulSoup(content, 'html.parser')
            script_tags = soup.find_all('script')

            for tag in script_tags:
                if tag.get('id') == 'serialized-server-data':
                    script_content = tag.string
                    return json.loads(script_content)
                
        except Exception as e:
            raise e
        

    def get_audio_url(self, podcast_url: str):
        data = self.extract_scripts_with_asseturl(podcast_url)

        if data and isinstance(data, list) and len(data) > 0:
            first_item = data[0]
            if isinstance(first_item, dict):
                intent_data = first_item.get('data', {})
            else:
                intent_data = {}
        else:
            intent_data = {}

        if not data:
            raise Exception("Unable to retrieve audio from the provided URL")
        
        intent_data = data[0].get('data', {})
        shelves = intent_data.get('shelves', [])

        stream_url = None
        for shelf in shelves:
            items = shelf.get('items', [])
            for item in items:
                context_action = item.get('contextAction', {})
                episode_offer = context_action.get('episodeOffer', {})
                stream_url = episode_offer.get('streamUrl')

                if stream_url:
                    return stream_url
                
        if not stream_url:
            raise Exception("Unable to retrieve audio from the provided URL")


    def download_audio(self, audio_url: str):

        file_path = general_service.download_file(
            url=audio_url,
            extension='mp3',
            prefix_file_name='pdcstaud'
        )

        return file_path
    
    
    def transcribe_audio(self, audio_path_or_url: str):
        '''This function transcribes audio into text'''

        return audio_summary_service.transcribe_audio(audio_path_or_url)
    

    def summarize_transcript(self, transcript: str, detail_level: str = 'short'):
        '''This function summarizes the transcript'''

        return pdf_summary_service.summarize_text(
            text=transcript, 
            detail_level=detail_level
        )

    
    def generate_transcript_with_timestamp(self, audio_path_or_url: str):
        '''This function generates a transcript with timestamps'''

        return audio_summary_service.generate_transcript_with_timestamp(
            audio_path_or_url,
            as_srt=False
        )
    

    def save_to_pdf(self, summary: str, transcript: str):
        '''This saves the generated summary and transcript to a file as a pdf'''

        return audio_summary_service.save_to_pdf(
            summary=summary,
            transcript=transcript,
            prefix_file_name='pdcstsum'
        )
    

podcast_summary_service = PodcastSummaryService()
