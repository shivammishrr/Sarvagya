from pydantic import BaseModel

class ChatRequest(BaseModel):
    user_query: str

class ChatUpdate(BaseModel):
    event: str
    data: str
