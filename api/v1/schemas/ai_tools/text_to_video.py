from pydantic import BaseModel


class ScriptSchema(BaseModel):

    script: str