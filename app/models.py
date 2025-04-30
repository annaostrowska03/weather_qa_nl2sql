from pydantic import BaseModel

class Question(BaseModel):
    question: str
    model: str # Model name (phi:mini, llama3 or gpt 3.5)
    api_key: str = " " # API key for OpenAI  