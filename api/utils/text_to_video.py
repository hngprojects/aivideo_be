import aiohttp

from api.utils.settings import settings

async def create_video_from_text(input_text: str):
    """
    Makes external API call.
    """
    headers = {
            'x-rapidapi-key': settings.X_RAPIDAPI_KEY,
            'x-rapidapi-host': settings.X_RAPIDAPI_HOST,
            'Content-Type': "application/json"
        }
    async with aiohttp.ClientSession(headers=headers) as conn:
        url = "https://runwayml.p.rapidapi.com/generate/text"
        payload = {
            "text_prompt": input_text,
            'model': "gen3",
            "width": 1344,
            "height": 768,
            "motion": 5,
            "seed": 0,
            "upscale": True,
            "interpolate": True,
            "callback_url": ""
        }

        async with conn.post(url=url, data=payload) as response:
            if response.status == 200:
                return await response.json()
            else:
                raise aiohttp.ClientError(f'An error occurred with {response.status} status code')
