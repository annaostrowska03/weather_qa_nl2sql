from langchain.llms import Ollama
from autocorrect import Speller
import requests

# Autokorekta
spell = Speller(lang='en')

# Opis tabeli do prompta
table_description = """
We have a table called Weather with the following columns:
- city (text): Name of the city
- temperature (integer): Temperature in degrees Celsius
- weather (text): Description of the current weather (e.g., sunny, cloudy, rain)
- climate (text): Climate type (e.g., temperate, tropical, desert)
"""

# Połączenie z lokalnym Ollama
llm = Ollama(model="llama3")

def generate_sql(question: str) -> str:
    corrected_question = spell(question)
    prompt = f"""
{table_description}

Based on this table, write a minimal and correct SQL query to answer the following question.
Only generate a SQL query without explanations or unnecessary JOINs.

Question: {corrected_question}
SQL:"""
    response = requests.post(
        "http://localhost:11434/api/generate",
        json={
            "model": "llama3",
            "prompt": prompt,
            "stream": False
        }
    )
    response.raise_for_status()
    result = response.json()
    return result["response"].strip()