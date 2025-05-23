default_prompt = """
Table 'Weather' has columns: 
- City (text)
- Temperature (int)
- Weather (text): e.g., 'sunny', 'rainy', 'cloudy'
- Climate (text): e.g., 'temperate', 'tropical'

Use fuzzy matching for textual data when needed (e.g., weather LIKE '%rain%').
Write a correct and minimal SQL query for the question below.
Only return SQL. No explanations. Stop after the query. DO not add any comments or extra text.
If the question is about a **value in the city**, return both the value and the related city. Use:
- `temperature` for numerical temperature questions,
- `weather` for descriptive weather questions,
- `climate` if the question is about long-term conditions.

Question: {corrected_question}
SQL:"""

# Schema-only (baseline)
schema_only_prompt = """
The 'Weather' table has the following columns:
- City (text)
- Temperature (int)
- Weather (text)
- Climate (text)

Write an SQL query that answers the user's question.

Question: {corrected_question}
SQL:
"""

# Instructional Prompt (emphasizes accuracy and brevity)
instructional_prompt = """
You're an expert data analyst. Generate an accurate and efficient SQL query for the following natural language question.

Table: Weather(City TEXT, Temperature INT, Weather TEXT, Climate TEXT)

Avoid SELECT * and prefer WHERE clauses when appropriate.
Question: {corrected_question}
SQL:
"""

# Few-shot example prompt (based on pattern learning)
few_shot_prompt = """
Table: Weather(City TEXT, Temperature INT, Weather TEXT, Climate TEXT)

Examples:
Q: Which cities have a tropical climate?
A: SELECT City FROM Weather WHERE Climate LIKE '%tropical%';

Q: What is the temperature in Warsaw?
A: SELECT Temperature FROM Weather WHERE City = 'Warsaw';

Q: Where is it raining?
A: SELECT City FROM Weather WHERE Weather LIKE '%rain%';

Q: Where is it the hottest?
A: SELECT City, Temperature FROM Weather ORDER BY Temperature DESC LIMIT 1;

Now answer:
Q: {corrected_question}
A:"""

# RAG-style: With natural language context
rag_prompt = """
You are given a database table named 'Weather' with the following meaning:
- 'City': name of the city
- 'Temperature': temperature in Celsius
- 'Weather': description like 'sunny', 'cloudy', 'rainy'
- 'Climate': long-term climate type like 'temperate', 'tropical'

Write an SQL query that correctly answers the question using this schema.

Question: {corrected_question}
SQL:
"""

# Conversational Style Prompt (optional)
conversational_prompt = """
You're a helpful assistant converting questions to SQL for a table with weather data.

'Weather' table columns: City, Temperature, Weather, Climate

Just return SQL, no explanation.

Question: {corrected_question}
SQL:
"""

prompt_templates_llms = {
    "default": default_prompt,
    "schema_only": schema_only_prompt,
    "instructional": instructional_prompt,
    "few_shot": few_shot_prompt,
    "rag_style": rag_prompt,
    "conversational": conversational_prompt
}


prompt_templates_other = {
    "tscholak/1zha5ono": "{corrected_question} | Weather : City, Temperature, Weather, Climate",
    "juierror/text-to-sql-with-table-schema": "question: {corrected_question} Weather: City,Temperature,Weather,Climate"
}
