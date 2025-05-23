import pandas as pd
import ast
import re
from app.nlp import execute_sql, generate_sql
from tests.prompt_templates import prompt_templates_other
import tests.questions as questions

def extract_sql_from_response(response_text):
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
        'rain': "'rainy'"
    }

    for old, new in replacements.items():
        # Replace only column names (not part of strings or function calls)
        sql = re.sub(rf'\b{old}\b', new, sql, flags=re.IGNORECASE)

    return sql
def normalize_result(result):
    """
    Converts SQL result list of tuples to a flattened, comma-separated string
    """
    return ", ".join(str(cell) for row in result for cell in row)

def is_match(result_str, ideal_list):
    result_str = result_str.lower().strip()

    for ideal in ideal_list:
        required_parts = [part.strip().lower() for part in ideal.split(",")]
        if all(part in result_str for part in required_parts):
            return True
    return False

import re

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
    sql = re.sub(r'\bAVG\s+(\w+)', r'AVG(\1)', sql, flags=re.IGNORECASE)

    # Replace common misused column names or keywords
    replacements = {
        'cloudy': 'Weather',
        'ethical': 'Weather',
        'location': 'City',
        'rain': "'rainy'",
        'sky clear': "'clear'"
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



def evaluate_model_outputs(model_outputs_path, ideal_answers_path):
    # Load data
    df_model = pd.read_csv(model_outputs_path)
    df_ideal = pd.read_csv(ideal_answers_path)

    # Parse ideal answers into list
    df_ideal['ideal_answers'] = df_ideal['ideal_answers'].apply(ast.literal_eval)

    # Merge on question
    df = df_model.merge(df_ideal, on="question")

    # Evaluate
    results = []
    for _, row in df.iterrows():
        sql = extract_sql_from_response(row['sql_query'])
        print(f"Evaluating question: {row['question']}")
        print("Current results:", results[-1] if results else "No results yet")
        print("Current row:", row.to_dict())
        if not sql:
            results.append({
                "question": row['question'],
                "model": row['model'],
                "prompt_template": row['prompt_template'],
                "response_time": row.get("response_time", None),
                "status": "no_sql", "match": False})
            continue

        if row['model'] == "juierror/text-to-sql-with-table-schema" or row['model'] == "tscholak/1zha5ono":
            sql_repaired = repair_sql_query(sql)
        else:
            sql_repaired = sql
        result, has_error = execute_sql(sql_repaired)
        if has_error:
            results.append({
                "question": row['question'],
                "model": row['model'],
                "prompt_template": row['prompt_template'],
                "response_time": row.get("response_time", None),
                "status": "sql_error", "match": False})
            continue

        result_str = normalize_result(result)
        match = is_match(result_str, row['ideal_answers'])
        results.append({
            "question": row['question'],
            "model": row['model'],
            "prompt_template": row['prompt_template'],
            "response_time": row.get("response_time", None),
            "sql_query": sql_repaired,
            "sql_result": result_str,
            "status": "ok",
            "match": match
        })

    # Summary by model and prompt
    df_results = pd.DataFrame(results)
    grouped = df_results.groupby(['model', 'prompt_template'])
    summary = grouped.agg(
        accuracy=('match', 'mean'),
        valid_sql_rate=('status', lambda x: (x == 'ok').mean()),
        avg_response_time=('response_time', 'mean'),
        count=('question', 'count')
    ).reset_index()

    print("\nEvaluation Summary:")
    print(summary.to_string(index=False))

    return df_results, summary

# Example usage:
# results_df = evaluate_model_outputs("model_outputs.csv", "ideal_answers.csv")
# results_df.to_csv("evaluation_results.csv", index=False)

if __name__ == "__main__":
    # i have results in 3 different files, i want to merge them into one file
    '''paths = [
    "tests/output/model_test_results_llama.csv",
    "tests/output/model_test_results_phi3.csv",
    "tests/output/model_test_results_without_llama.csv"
    ]

    dfs = [pd.read_csv(path) for path in paths]
    df_merged = pd.concat(dfs, ignore_index=True)
    df_merged.to_csv("merged_model_outputs.csv", index=False)'''

    '''print("Merged data from 3 models and saved to: merged_model_outputs.csv")

    model_outputs_path = "tests/output/merged_model_outputs.csv"
    ideal_answers_path = "tests/ideal_answers_from_data.csv"
    results_df, summary = evaluate_model_outputs(model_outputs_path, ideal_answers_path)
    results_df.to_csv("evaluation_results.csv", index=False)
    print("Evaluation results saved to: evaluation_results.csv")
    summary.to_csv("evaluation_summary.csv", index=False)
    print("Evaluation summary saved to: evaluation_summary.csv")'''
'''
    for q in questions.questions:
        print(q)
        corrected_question, output = generate_sql(q, "tscholak/1zha5ono", api_key = "", prompt_template=prompt_templates_other["tscholak/1zha5ono"])
        sql_repaired = repair_sql_query(output)
        print("Corrected question:", corrected_question)
        print("Output:", output)
        print("Repaired SQL:", sql_repaired)
        print("SQL:", extract_sql_from_response(output))
'''

