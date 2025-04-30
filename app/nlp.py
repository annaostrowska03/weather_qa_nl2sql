from langchain.llms import Ollama
from autocorrect import Speller
import requests
import re

# Autocorrect
spell = Speller(lang='en')

# Table description
table_description = "Table 'Weather' has columns: city (text), temperature (int), weather (text), climate (text)."

llm = Ollama(model="phi3:mini")  

def clean_sql_output(text: str) -> str:
    return re.sub(r"(?i)^```sql\s*|```$", "", text.strip()).strip()

def generate_sql(question: str, model_name: str, api_key: str) -> str:
    corrected_question = spell(question)

    prompt = f"""
{table_description}

Write a **minimal and correct** SQL query to answer the following question.
- **No explanations. Only the SQL.**
- **Stop after finishing the correct SQL query. Do not add anything else.**

Question: {corrected_question}
SQL:"""

    if "gpt" in model_name:
        # Use OpenAI API for gpt models
        from openai import OpenAI
        client = OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model=model_name,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1
        )
        answer = response.choices[0].message.content.strip()

    else:
        # Use Ollama API for phi models

        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": "phi3:mini",
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.1, 
                    "num_ctx": 2048,
                    "num_predict": 64
                },
                "keep_alive": "10m"
            }
        )
        response.raise_for_status()
        answer = response.json()["response"]

    # Clean the SQL output
    return clean_sql_output(answer)
