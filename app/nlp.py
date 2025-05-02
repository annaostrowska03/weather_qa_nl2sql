from langchain.llms import Ollama
from autocorrect import Speller
import requests
import re
from app.database import get_db_connection

# Autocorrect
spell = Speller(lang='en')


def clean_sql_output(text: str) -> str:
    sql =  re.sub(r"(?i)^```sql\s*|```$", "", text.strip()).strip()
    match = re.search(r"LIMIT\s+(\d+)", sql, re.IGNORECASE)
    if match:
        limit_value = match.group(1)
        sql = re.sub(r"(?i)^SELECT\s+", f"SELECT TOP {limit_value} ", sql)
        sql = re.sub(r"\s+LIMIT\s+\d+\s*;?$", "", sql, flags=re.IGNORECASE)
    return sql

def generate_sql(question: str, model_name: str, api_key: str, prompt_template: str = None, 
temperature: float = 0.1, num_ctx: int = 2048, num_predict: int = 256) -> tuple:
    corrected_question = " ".join([spell(word) for word in question.split()])

    if prompt_template is None:
        prompt_template = """
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
    prompt = prompt_template.format(corrected_question=corrected_question)

    if model_name == "sqlcoder":
        from transformers import AutoTokenizer, AutoModelForCausalLM
        import torch
        # Load the model and tokenizer
        tokenizer = AutoTokenizer.from_pretrained("defog/sqlcoder")
        model = AutoModelForCausalLM.from_pretrained("defog/sqlcoder").to("cuda" if torch.cuda.is_available() else "cpu")

        inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
        outputs = model.generate(**inputs, max_new_tokens=128)
        output = tokenizer.decode(outputs[0], skip_special_tokens=True)
        sql = "SELECT" + output.split("SELECT", 1)[-1]
        return corrected_question, sql
    
    if model_name == "crack-sql":
        from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
        tokenizer = AutoTokenizer.from_pretrained("bjin/crack-sql")
        model = AutoModelForSeq2SeqLM.from_pretrained("bjin/crack-sql").to("cuda" if torch.cuda.is_available() else "cpu")

        inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
        outputs = model.generate(**inputs, max_new_tokens=128)
        output = tokenizer.decode(outputs[0], skip_special_tokens=True)
        return corrected_question, output


    if "gpt" in model_name.lower():
        # Use OpenAI API for gpt models
        from openai import OpenAI
        client = OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model=model_name,
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature
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
                    "temperature": temperature, 
                    "num_ctx": num_ctx,
                    "num_predict": num_predict,
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
        has_error = False
    except Exception as e:
        return [("Error executing SQL", str(e))]
        has_error = True
    finally:
        cursor.close()
        conn.close()

    return results, has_error

def answer_question(question: str, model_name: str, api_key: str, prompt_template: str = None, temperature: float = 0.1, num_ctx: int = 2048, num_predict: int = 256, final_prompt: str = None, answer_temperature: float = 0.5) -> tuple:
    corrected_question, sql_query = generate_sql(
        question, model_name, api_key,
        prompt_template=prompt_template,
        temperature=temperature,
        num_ctx=num_ctx,
        num_predict=num_predict
    )
    results, has_error = execute_sql(sql_query)

    if not results:
        return sql_query, "No results", "No matching results found.", corrected_question, has_error
    
    if has_error:
        return sql_query, "Error executing SQL", "Error executing SQL query.", corrected_question, has_error

    
    result_summary = "; ".join([", ".join(map(str, row)) for row in results])

    if model_name == "sqlcoder":
        return sql_query, results, "", corrected_question, has_error

    if final_prompt is None:
        final_prompt = """
You are an assistant helping users understand weather data. Based on the user's question and this SQL query result, write a short answer.

Question: {corrected_question}
SQL Result: {result_summary}

Answer:"""

    answer_prompt = final_prompt.format(
        corrected_question=corrected_question, 
        result_summary=result_summary)

    if "gpt" in model_name.lower():
        from openai import OpenAI
        client = OpenAI(api_key=api_key)
        final_response = client.chat.completions.create(
            model=model_name,
            messages=[{"role": "user", "content": answer_prompt}],
            temperature=answer_temperature
        ).choices[0].message.content.strip()
    else:
        final_response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": model_name,
                "prompt": answer_prompt,
                "stream": False,
                "options": {
                    "temperature": answer_temperature,
                    "num_ctx": 2048,
                    "num_predict": 128
                },
                "keep_alive": "10m"
            }
        ).json()["response"].strip()

    return sql_query, result_summary, final_response, corrected_question, has_error
