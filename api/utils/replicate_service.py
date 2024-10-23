import replicate

from api.utils.settings import settings


class ReplicateService:
    
    def __init__(self):
        self.client = replicate.Client(api_token=settings.REPLICATE_API_TOKEN)
        
    
    def __run_model(self, model_id, input_data):
        result = self.client.run(
            model_id,
            input=input_data
        )
        return result


replicate_service = ReplicateService()