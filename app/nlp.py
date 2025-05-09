from langchain.llms import Ollama
import language_tool_python
import requests
import re
from app.database import get_db_connection
from tests.prompt_templates import prompt_templates_llms, prompt_templates_other
import pyodbc
import os
from openai import AuthenticationError, RateLimitError, APIError
from dotenv import load_dotenv

# Autocorrect
autocorrect = language_tool_python.LanguageTool('en-US')

def get_db_type():
    try:
        conn = get_db_connection()
        driver = conn.getinfo(pyodbc.SQL_DRIVER_NAME)  
        conn.close()
        print(f"Detected driver: {driver}")
        if "msodbcsql" in driver.lower():
            return "sqlserver"
    except Exception as e:
        print(f"Could not detect driver: {e}")
    return "sqlite"



model_prompt_styles = {
    "phi3:mini": "few_shot",
    "gpt-4o-mini": "default",
    "gpt-3.5-turbo": "default",
    "gpt-4o": "default",
    "mistral": "default",
    "llama3": "default",
    "tscholak/1zha5ono": "tscholak/1zha5ono",
    "juierror/text-to-sql-with-table-schema": "juierror/text-to-sql-with-table-schema"
}
def quote_values_after_equals(sql: str) -> str:
    """
    Finds values after '=' (or LIKE, <>, !=) and wraps them in single quotes if not already quoted or numeric.
    """
    def replacer(match):
        operator = match.group(1)
        value = match.group(2).strip()
        # Ignore if already quoted or numeric
        if value.startswith("'") or value.startswith('"') or re.match(r'^\d+(\.\d+)?$', value):
            return f"{operator} {value}"
        return f"{operator} '{value}'"

    # Match expressions like "= value", "!= value", "<> value", "LIKE value"
    pattern = re.compile(r'(=|!=|<>|LIKE)\s+([a-zA-Z_][a-zA-Z0-9_]*)', flags=re.IGNORECASE)
    return pattern.sub(replacer, sql)

def extract_sql_from_response(response_text, db_type: str = "sqlserver", model_name: str = None) -> str:
    """
    Extracts SQL from response starting at 'SELECT', applies normalization:
    - Replaces generic or lowercase column/table names with correct ones.
    - Ensures basic consistency for evaluation.
    """
    # Find the first occurrence of 'select' (case-insensitive)
    match = re.search(r'select\s.+', response_text, re.IGNORECASE)
    if not match:
        return None

    sql = match.group().strip().rstrip(';')

    # Normalize table name
    sql = re.sub(r'\bfrom\s+table\b', 'FROM Weather', sql, flags=re.IGNORECASE)
    sql = re.sub(r'\bfrom\s+weather\b', 'FROM Weather', sql, flags=re.IGNORECASE)

    # Normalize columns
    replacements = {
        'location': 'City',
        'weather': 'Weather',
        'climate': 'Climate',
        'temperature': 'Temperature',
        'city': 'City',
        'rain': "rainy"
    }

    for old, new in replacements.items():
        # Replace only column names (not part of strings or function calls)
        sql = re.sub(rf'\b{old}\b', new, sql, flags=re.IGNORECASE)

   # add FROM Weather if not present and if the query is a SELECT statement
    if not re.search(r'\bfrom\b', sql, re.IGNORECASE):
            if re.search(r'\bselect\b.+\b(city|temperature|weather|climate)\b', sql, re.IGNORECASE):
                sql += " FROM Weather"

    # Check for SQL Server specific syntax and convert LIMIT to TOP
    print(f"DB Type: {db_type}")
    if db_type == "sqlserver" and re.search(r'\bLIMIT\s+1\b', sql, flags=re.IGNORECASE):
        sql = re.sub(r'\bLIMIT\s+1\b', '', sql, flags=re.IGNORECASE).strip()
        sql = re.sub(r'(?i)^SELECT\s+', 'SELECT TOP 1 ', sql, count=1)



    if model_name == "tscholak/1zha5ono" or model_name == "juierror/text-to-sql-with-table-schema":
        sql = repair_sql_query(sql)

    sql = quote_values_after_equals(sql)


    return sql

def repair_sql_query(sql: str) -> str:
    """
    Cleans and repairs common issues in SQL queries generated by models.
    - Replaces invalid names.
    - Fixes broken expressions like 'sky clear' → 'Weather = 'clear''
    - Fixes AVG and other function calls.
    - Normalizes table and column names.
    """
    if not sql:
        return sql

    # Remove invalid JOINs
    sql = re.sub(r'\bjoin\s+it\s+as\s+t\d+\s+on\s+[^\n]+?(?=where|\bjoin|\Z)', '', sql, flags=re.IGNORECASE)
    sql = re.sub(r'\bt\d+\.', '', sql, flags=re.IGNORECASE)

    # Normalize table name
    sql = re.sub(r'\bfrom\s+table\b', 'FROM Weather', sql, flags=re.IGNORECASE)
    sql = re.sub(r'\bfrom\s+weather\b', 'FROM Weather', sql, flags=re.IGNORECASE)

    # Fix common broken value expressions (e.g. sky clear, 20 degrees)
    sql = re.sub(r"=\s*sky clear", "= 'clear'", sql, flags=re.IGNORECASE)
    sql = re.sub(r"=\s*20 degrees", "= 20", sql, flags=re.IGNORECASE)
    sql = re.sub(r"=\s*sunny", "= 'sunny'", sql, flags=re.IGNORECASE)

    # Fix function syntax (AVG Temperature → AVG(Temperature))
    # Fix function syntax (e.g. AVG Temperature → AVG(Temperature))
    sql = re.sub(r'\b(AVG|MAX|MIN|SUM|COUNT)\s+(\w+)', r'\1(\2)', sql, flags=re.IGNORECASE)


    # Replace common misused column names or keywords
    replacements = {
        'ethical': 'Weather',
        'location': 'City',
        'rain': "'rainy'",
        'sky clear': "'clear'",
        'raining': "rainy",
        'drizzly': "drizzle"
    }
    for old, new in replacements.items():
        sql = re.sub(rf'\b{old}\b', new, sql, flags=re.IGNORECASE)

    # Normalize casing for known columns
    casing_map = {
        'city': 'City',
        'weather': 'Weather',
        'climate': 'Climate',
        'temperature': 'Temperature'
    }
    for old, new in casing_map.items():
        sql = re.sub(rf'\b{old}\b', new, sql, flags=re.IGNORECASE)

    # Convert "value" → 'value'
    sql = re.sub(r'"([^"]+)"', r"'\1'", sql)

    # Cleanup
    sql = re.sub(r'\s+', ' ', sql).strip()
    sql = sql.rstrip(';')

    return sql


def generate_sql(question: str, model_name: str, api_key: str=None, prompt_template: str = None, 
temperature: float = 0.1, num_ctx: int = 2048, num_predict: int = 256) -> tuple:
    db_type = get_db_type()
    load_dotenv()
    matches = autocorrect.check(question)
    corrected_question = language_tool_python.utils.correct(question, matches)
    try:
        if prompt_template is None:
            # Determine the prompt key (style) based on model
            prompt_style = model_prompt_styles.get(model_name, "default")

            if model_name not in ["tscholak/1zha5ono", "juierror/text-to-sql-with-table-schema"] and prompt_style is not None:
                prompt_template = prompt_templates_llms[prompt_style]
            elif prompt_style is not None:
                prompt_template = prompt_templates_other[prompt_style]
            else:
                prompt_template = prompt_templates_llms["default"]


        prompt = prompt_template.format(corrected_question=corrected_question)

        if model_name == "juierror/text-to-sql-with-table-schema":
            from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
            import torch
            tokenizer = AutoTokenizer.from_pretrained(model_name)
            model = AutoModelForSeq2SeqLM.from_pretrained(model_name).to("cuda" if torch.cuda.is_available() else "cpu")

            inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
            outputs = model.generate(inputs=inputs["input_ids"], num_beams=10, max_length=700)
            output = tokenizer.decode(outputs[0], skip_special_tokens=True)
            output = extract_sql_from_response(output.strip(), db_type=db_type, model_name=model_name)
            return corrected_question, output

        
        if model_name == "tscholak/1zha5ono":
            from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
            import torch
            tokenizer = AutoTokenizer.from_pretrained("tscholak/1zha5ono")
            model = AutoModelForSeq2SeqLM.from_pretrained("tscholak/1zha5ono").to("cuda" if torch.cuda.is_available() else "cpu")

            inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
            outputs = model.generate(**inputs, max_new_tokens=128)
            output = tokenizer.decode(outputs[0], skip_special_tokens=True)
            output = extract_sql_from_response(output, db_type=db_type, model_name=model_name)
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

            ollama_base = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434").rstrip("/")
            response = requests.post(
                f"{ollama_base}/api/generate",
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
        answer = extract_sql_from_response(answer, db_type=db_type, model_name=model_name)
        return corrected_question, answer

    except APIError as e:
        if "insufficient_quota" in str(e).lower():
            return corrected_question, "insufficient_quota"
        return corrected_question, f"Error generating SQL: {e}"
    except Exception as e:
        return corrected_question, f"Error generating SQL: {str(e)}"


    
def execute_sql(sql_query: str) -> list:
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
    except Exception as e:
        return ["Error connecting to database"], True
    try:
        cursor.execute(sql_query)
        results = cursor.fetchall()
        has_error = False
    except Exception as e:
        return ["Error executing SQL."], True
    finally:
        try:
            cursor.close()
            conn.close()
        except Exception as e:
            print("Error closing connection.")

    return results, has_error

def answer_question(question: str, model_name: str, api_key: str, prompt_template: str = None, temperature: float = 0.1, num_ctx: int = 2048, num_predict: int = 256, final_prompt: str = None, answer_temperature: float = 0.5) -> tuple:
    db_type = get_db_type()
    corrected_question, sql_query = generate_sql(
            question, model_name, api_key,
            prompt_template=prompt_template,
            temperature=temperature,
            num_ctx=num_ctx,
            num_predict=num_predict
        )

    if sql_query.startswith("-- Error"):
            return sql_query, sql_query, sql_query, corrected_question, True
    results, has_error = execute_sql(sql_query)

    if has_error:
        result_summary = "Error executing SQL query."
    elif not results:
        result_summary = "No matching results found."
    else:
        result_summary = "; ".join([", ".join(map(str, row)) for row in results])
    if model_name in ["tscholak/1zha5ono", "juierror/text-to-sql-with-table-schema"]:
        return sql_query, result_summary, result_summary, corrected_question, has_error

    try:
        if has_error:
            return sql_query, "Error executing SQL", "Error executing SQL query.", corrected_question, True

        if not results:
            return sql_query, "No results", "No matching results found.", corrected_question, False

        if final_prompt is None:
            final_prompt = """
        You are a helpful assistant. Write a short, direct sentence in natural language answering the user's weather question.

        Avoid repeating the question or mentioning SQL. Just answer clearly and concisely.

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
            ollama_base = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434").rstrip("/")
            final_response = requests.post(
                f"{ollama_base}/api/generate",
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
    
    except Exception as e:
        return sql_query, result_summary, f"Error: {e}", corrected_question, True
