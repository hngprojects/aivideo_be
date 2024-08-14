from pydantic import BaseModel

class CreateProject(BaseModel):

    title : str
    project_type : str
    


class UpdateProject(BaseModel):
    
    title : str
    description: str
    

