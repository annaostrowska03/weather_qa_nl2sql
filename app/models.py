from pydantic import BaseModel

class Question(BaseModel):
    question: str
    model: str # Model name (phi3:mini, llama3 or gpt 3.5/4o-mini)
    api_key: str = " " # API key for OpenAI  