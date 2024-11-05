from typing import Dict, Any
import replicate

from api.utils.settings import settings


class ReplicateService:
    
    def __init__(self):
        self.client = replicate.Client(api_token=settings.REPLICATE_API_TOKEN)
        
    
    def __run_model(self, model_id: str, input: Dict[str, Any]):
        print(f'Running model {model_id}')
        result = self.client.run(
            model_id,
            input=input
        )
        
        print(result)
        return result
    
    
    def convert_text_to_speech(
        self, 
        text: str, 
        sample_audio_file: str,
        language: str = 'en'
    ):
        """This function converts text to speech

        Args:
            text (str): Text to be converted to audio file
            sample_audio_file (str): This is a file or url that links to a sample voice that willbe used as the voice for the generated audio file
            language (str, optional): Language of the generated audio. Defaults to 'en'.

        Returns:
            str: The URL of the audio generated
        """
        
        output = self.__run_model(
            "lucataco/xtts-v2:684bc3855b37866c0c65add2ff39c78f3dea3f4ff103a436465326e0f438d55e",
            input={
                "text": text,
                "speaker": sample_audio_file,
                "language": language,
                "cleanup_voice": False
            }
        )
        
        return output
    
    
    def generate_image(self, prompt: str, num_outputs: int=5, img_width: int=1024, img_height: int=1024):
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
            # "stability-ai/stable-diffusion:ac732df83cea7fff18b8472768c88ad041fa750ff7682a21affe81863cbe77e4",
            # input={
            #     "width": img_width,
            #     "height": img_height,
            #     "prompt": prompt,
            #     "scheduler": "K_EULER",
            #     "num_outputs": num_outputs,
            #     "guidance_scale": 7.5,
            #     "num_inference_steps": 50
            # }
            
            "bytedance/sdxl-lightning-4step:5599ed30703defd1d160a25a63321b4dec97101d98b4674bcc56e41f62f35637",
            input={
                "width": img_width,
                "height": img_height,
                "prompt": prompt,
                "scheduler": "K_EULER",
                "num_outputs": num_outputs,
                "guidance_scale": 0,
                "negative_prompt": "worst quality, low quality",
                "num_inference_steps": 4
            }
        )
        
        return output
    
    
    def generate_talking_avatar(self, image_url: str, audio_url: str):
        
        # output = self.__run_model(
        #     "lucataco/sadtalker:85c698db7c0a66d5011435d0191db323034e1da04b912a6d365833141b6a285b",
        #     input={
        #         "driven_audio": audio_url,
        #         "source_image": image_url,
        #         "still": True,
        #         "enhancer": "gfpgan",
        #         "preprocess": "full"
        #     }
        # )
        
        output = self.__run_model(
            "cjwbw/sadtalker:a519cc0cfebaaeade068b23899165a11ec76aaa1d2b313d40d214f204ec957a3",
            input={
                "facerender": "facevid2vid",
                "pose_style": 0,
                "preprocess": "crop",
                "still_mode": True,
                "driven_audio": audio_url,
                "source_image": image_url,
                "use_enhancer": True,
                "use_eyeblink": True,
                "size_of_image": 256,
                "expression_scale": 1
            }
        )
        
        return output
    
    
    
    def generate_video(self, prompt: str, width: int=1024, height: int=1024, num_outputs: int=3):
        
        final_output = []
        
        for _ in range(num_outputs):
            output = self.__run_model(
                "lucataco/hotshot-xl:78b3a6257e16e4b241245d65c8b2b81ea2e1ff7ed4c55306b511509ddbfd327a",
                input={
                    "mp4": True,
                    "seed": 6226,
                    "steps": 30,
                    "width": width,
                    "height": height,
                    "prompt": prompt,
                    "scheduler": "EulerAncestralDiscreteScheduler",
                    "negative_prompt": "blurry"
                }
            )
            
            final_output.append(output)
        return final_output


replicate_service = ReplicateService()
