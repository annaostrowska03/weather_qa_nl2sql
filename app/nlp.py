from langchain.llms import Ollama
from autocorrect import Speller
import requests
import re
from app.database import get_db_connection

# Autocorrect
spell = Speller(lang='en')

llm = Ollama(model="phi3:mini")  

def clean_sql_output(text: str) -> str:
    sql =  re.sub(r"(?i)^```sql\s*|```$", "", text.strip()).strip()
    sql = re.sub(r"(?i)^```sql\s*|```$", "", text.strip()).strip()
    match = re.search(r"LIMIT\s+(\d+)", sql, re.IGNORECASE)
    if match:
        limit_value = match.group(1)
        sql = re.sub(r"(?i)^SELECT\s+", f"SELECT TOP {limit_value} ", sql)
        sql = re.sub(r"\s+LIMIT\s+\d+\s*;?$", "", sql, flags=re.IGNORECASE)
    return sql

def generate_sql(question: str, model_name: str, api_key: str) -> str:
    corrected_question = " ".join([spell(word) for word in question.split()])


    prompt = f"""
Table 'Weather' has columns: 
- city (text)
- temperature (int)
- weather (text): e.g., 'sunny', 'rainy', 'cloudy'
- climate (text): e.g., 'temperate', 'tropical'

Use fuzzy matching for textual data when needed (e.g., weather LIKE '%rain%').
Write a correct and minimal SQL query for the question below.
Only return SQL. No explanations. Stop after the query. DO not add any comments or extra text.
If the question is about a **value in the city**, return both the value and the related city. Use:
- `temperature` for numerical temperature questions,
- `weather` for descriptive weather questions,
- `climate` if the question is about long-term conditions.

Question: {corrected_question}
SQL:"""

    if "gpt" in model_name.lower():
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
        # Use Ollama API for open-source models

        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": model_name,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.1, 
                    "num_ctx": 2048,
                    "num_predict": 256
                },
                "keep_alive": "10m"
            }
        )
        response.raise_for_status()
        answer = response.json()["response"]

    # Clean the SQL output
    return corrected_question, clean_sql_output(answer)

def execute_sql(sql_query: str) -> list:
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(sql_query)
        results = cursor.fetchall()
    except Exception as e:
        return [("Error executing SQL", str(e))]
    finally:
        cursor.close()
        conn.close()

    return results

def answer_question(question: str, model_name: str, api_key: str) -> str:
    corrected_question, sql_query = generate_sql(question, model_name, api_key)
    results = execute_sql(sql_query)

    if not results:
        return sql_query, "No results", "No matching results found."

    
    result_summary = "; ".join([", ".join(map(str, row)) for row in results])

    
    answer_prompt = f"""
You are an assistant helping users understand weather data. Based on the user's question and this SQL query result, write a short answer.

Question: {corrected_question}
SQL Result: {result_summary}

Answer:"""

    if "gpt" in model_name.lower():
        from openai import OpenAI
        client = OpenAI(api_key=api_key)
        final_response = client.chat.completions.create(
            model=model_name,
            messages=[{"role": "user", "content": answer_prompt}],
            temperature=0.5
        ).choices[0].message.content.strip()
    else:
        final_response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": model_name,
                "prompt": answer_prompt,
                "stream": False,
                "options": {
                    "temperature": 0.5,
                    "num_ctx": 2048,
                    "num_predict": 128
                },
                "keep_alive": "10m"
            }
        ).json()["response"].strip()

    return sql_query, result_summary, final_response
