from typing import Dict, Any
import replicate

from api.utils.settings import settings


class ReplicateService:
    
    def __init__(self):
        self.client = replicate.Client(api_token=settings.REPLICATE_API_TOKEN)
        
    
    def __run_model(self, model_id: str, input: Dict[str, Any]):
        result = self.client.run(
            model_id,
            input=input
        )
        return result['output']
    
    
    def convert_text_to_speech(self, text: str, sample_audio_file: str):
        """This function converts text to speech

        Args:
            text (str): Text to be converted to audio file
            sample_audio_file (str): This is a file or url that links to a sample voice that willbe used as the voice for the generated audio file

        Returns:
            str: The URL of the audio generated
        """
        
        output = self.__run_model(
            "lucataco/xtts-v2:684bc3855b37866c0c65add2ff39c78f3dea3f4ff103a436465326e0f438d55e",
            input={
                "text": text,
                "speaker": sample_audio_file,
                "language": "en",
                "cleanup_voice": False
            }
        )
        
        return output
    
    
    def generate_image(self, prompt: str, num_outputs: int, img_width: int, img_height: int):
        """This function uses stable diffusion to generate an image

        Args:
            prompt (str): Description of the image to be generated
            num_outputs (int): Number of images to be generated
            img_width (int): Width of image to be generated
            img_height (int): Height of image to be generated

        Returns:
            _type_: _description_
        """
        
        output = self.__run_model(
            "stability-ai/stable-diffusion:ac732df83cea7fff18b8472768c88ad041fa750ff7682a21affe81863cbe77e4",
            input={
                "width": img_width,
                "height": img_height,
                "prompt": prompt,
                "scheduler": "K_EULER",
                "num_outputs": num_outputs,
                "guidance_scale": 7.5,
                "num_inference_steps": 50
            }
        )
        
        return output


replicate_service = ReplicateService()
