# Weather Q\&A Natural Language to SQL (NL2SQL)

This project was developed as a take-home task for a AI/ML internship at Evertz.  It uses LangChain, FastAPI, and several LLM backends to translate natural language questions into SQL queries for weather data — and vice versa, converting SQL results back into human-readable answers.



---

## Features

* Bidirectional NL ↔ SQL conversion for weather-related queries
* Friendly web interface with model selector, live feedback and error handling
* Multiple model backends (OpenAI, Ollama, HuggingFace)
* SQL dialect adaptation for SQLite and SQL Server (LIMIT → TOP, etc.)
* Automatic query correction and schema normalization
* Integrated LangChain pipeline with prompt templating, model orchestration, and fuzzy value correction
* Prompt engineering support and evaluation utilities
* Evaluation scripts for accuracy, validity, and latency
* Dockerized deployment support

---

## Model Candidates Evaluated

| Model                                    | Source      |
| ---------------------------------------- | ----------- |
| `tscholak/1zha5ono`                      | HuggingFace |
| `juierror/text-to-sql-with-table-schema` | HuggingFace |
| `mistral`                                | Ollama      |
| `phi3:mini`                              | Ollama      |
| `llama3`                                 | Ollama      |
| `gpt-4o-mini` | OpenAI API  |

---

## Final Model Selection

After evaluation on:

* **Accuracy of SQL execution** (compared with 'ideal' results from the database)
* **Validity of SQL syntax**
* **Response time**

The selected default models in the web interface were:

* **`phi3:mini`** – for fast, accurate free use
* **`gpt-4o-mini`** – best overall accuracy with fast response (requires OpenAI API key)
* **`mistral`** – open-source fallback model (slower but reliable)
* **`juierror/text-to-sql-with-table-schema`** – baseline HuggingFace model (the fastest but lower accuracy)

---

## Running the App

You can run the app in three different ways:

---

### Docker (Recommended)

```bash
# Build the Docker image
docker build -t weather-nl2sql .

# Run with environment variables
docker run -p 8000:8000 --env-file .env weather-nl2sql
```

Then open your browser at: [http://localhost:8000](http://localhost:8000)

### Docker Compose

```bash
docker compose up --build
```

This version launches the API together with a seeded SQL Server instance.

Stop with:

```bash
docker compose down
```

### Local setup (without Docker)

```bash
# Create and activate virtual environment (optional)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Start the app
uvicorn app.main:app --reload

```

Then open your browser at: [http://localhost:8000](http://localhost:8000)

### Environment setup

Create a .env file in the project root to configure database and API access:

```dotenv
DB_SERVER=localhost
DB_NAME=WeatherDB
DB_USER=sa
DB_PASSWORD=your_password_here
SQL_DRIVER=ODBC Driver 17 for SQL Server

# OpenAI (optional)
OPEN_API_KEY=sk-...
```

---

## Prompt Engineering

### Prompt Templates Tested:

From `tests/prompt_templates.py`, the following prompt styles were tested:

* `default` – descriptive, fuzzy matching enabled, detailed task instructions
* `few_shot` – includes 4 diverse examples
* `schema_only` – minimal, schema-only baseline
* `instructional` – assumes analyst persona
* `rag_style` – schema in natural language
* `conversational` – lightweight format

Each model was mapped to its suitable prompt style in `model_prompt_styles` (it was checked in tests which prompt works the best for which model):

```python
model_prompt_styles = {
    "phi3:mini": "few_shot",
    "gpt-4o-mini": "default",
    "gpt-3.5-turbo": "default",
    "gpt-4o": "default",
    "mistral": "default",
    "llama3": "default",
    "tscholak/1zha5ono": None,
    "juierror/text-to-sql-with-table-schema": None
}
```

### Checked parameters

Other additional parameters were checked:

* SQL generation temperature: `0.0`, `0.1`, `0.3`
* Final answer generation temperature: `0.5`, `0.7`, `1.0`
* Context length (`num_ctx`): `2048`
* Prediction tokens (`num_predict`): `64`, `128`

---

## Evaluation

Using `evaluate.py`, models were scored on:

* SQL accuracy vs. ground-truth answers
* SQL validity  (via parsing)
* Query execution success
* Latency (response time)

Results were saved to:

* `tests/output/model_test_results.csv`
* `evaluation_results.csv`
* `evaluation_summary.csv`

---

## Libraries & Tools Used

* Python 
* FastAPI
* LangChain
* Ollama
* OpenAI SDK
* HuggingFace Transformers
* SQLAlchemy / pyodbc
* Docker
* Pandas
* Autocorrect
* dotenv

---

## File structure

```bash
weather_qa_nl2sql/
├── app/
│   ├── main.py             # FastAPI 
│   ├── nlp.py              # NLP logic: generation, repair
│   ├── database.py         # DB connection setup
│   ├── models.py           # Pydantic Question schema (question, model, api_key)
├── tests/
│   ├── tests.py            # Grid search on different models, prompts and hyperparamaters
│   ├── evaluate.py         # Model performance evaluator
│   ├── questions.py        # Natural language test questions
│   ├── prompt_templates.py # Tested prompts for models
├── app/templates/          # HTML (Jinja2-based)
├── Dockerfile
├── requirements.txt
├── .env                    # Config file (not committed)
```


## Author

[Anna Ostrowska](https://github.com/annaostrowska03)
 
