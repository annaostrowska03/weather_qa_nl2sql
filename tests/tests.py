import time
from app.nlp import answer_question, generate_sql, execute_sql
from app.database import get_db_connection
from tests import questions
import pandas as pd
from tests.prompt_templates import prompt_templates_llms, prompt_templates_other
import os
from dotenv import load_dotenv

def measure_response_time(question, model, api_key="", sql_temperature=0.1, final_temperature=0.5, prompt_template=None, num_ctx=2048, num_predict=256, prompt_name =None):
    start = time.time()
    sql, sql_result, answer, corrected_question, has_error = answer_question(question, model, api_key, prompt_template=prompt_template, temperature=sql_temperature, num_ctx=num_ctx, num_predict=num_predict, answer_temperature=final_temperature)
    elapsed = time.time() - start
    return {
        "question": question,
        "corrected_question": corrected_question,
        "model": model,
        "sql_query": sql,
        "sql_result": sql_result,
        "final_answer": answer,
        "response_time": elapsed,
        "has_error": has_error,
        "sql_temperature": sql_temperature,
        "final_temperature": final_temperature,
        "prompt_template": prompt_name,
        "num_ctx": num_ctx,
        "num_predict": num_predict
    }

if __name__ == "__main__":
    load_dotenv()

    results = []

    for question in questions.questions:
        result = measure_response_time(question, 'tscholak/1zha5ono', prompt_template=prompt_templates_other["tscholak/1zha5ono"], prompt_name="tscholak/1zha5ono")
        results.append(result)
        print(f"Model: tscholak/1zha5ono, Question: {question}, SQL: {result['sql_query']}, Response Time: {result['response_time']:.2f} seconds, prompt template: tscholak/1zha5ono")

        result = measure_response_time(question, 'juierror/text-to-sql-with-table-schema', prompt_template=prompt_templates_other["juierror/text-to-sql-with-table-schema"], prompt_name="juierror/text-to-sql-with-table-schema")
        results.append(result)
        print(f"Model: juierror/text-to-sql-with-table-schema, Question: {question}, SQL: {result['sql_query']}, Response Time: {result['response_time']:.2f} seconds, prompt template: juierror/text-to-sql-with-table-schema")

    for model in ["phi3:mini", "llama3", "gpt-4o-mini", "mistral"]:
        for sql_temperature in [0.1, 0.3, 0.0]:
            for final_temperature in [0.7, 0.5, 1.0]:
                for name, prompt in prompt_templates_llms.items():
                    for num_ctx in [2048]:
                        for num_predict in [128, 64]:
                            for question in questions.questions:
                                result = measure_response_time(question, model, api_key=os.getenv("OPEN_API_KEY", ""), sql_temperature=sql_temperature, final_temperature=final_temperature, prompt_template=prompt, num_ctx=num_ctx, num_predict=num_predict, prompt_name=name)
                                results.append(result)
                                print(f"Model: {model}, Question: {question}, SQL: {result['sql_query']}, Response Time: {result['response_time']:.2f} seconds, sql temperature: {sql_temperature}, final temperature: {final_temperature}, prompt template: {name}, num_ctx: {num_ctx}, num_predict: {num_predict}")

    df = pd.DataFrame(results)
    df.to_csv("tests/output/model_test_results.csv", index=False)
    print("Saved to model_test_results.csv")

