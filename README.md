# Weather Q&A: Natural Language to SQL

This is a **web application** that allows users to ask weather-related questions in natural language. The app translates those questions into SQL queries and returns answers based on weather data stored in a database.

This project was developed as a take-home task for an AI/ML internship at Evertz.


---

## Technologies used

- **FastAPI** – Web backend and interactive interface.
- **LangChain** – Handles prompt logic and LLM orchestration.
- **OpenAI / HuggingFace / Ollama** – Backends for running different language models.
- **Docker & Docker Compose** – For easy deployment and environment isolation.
- **PyODBC / SQL Server** – Database engine and Python connectivity.
- **Autocorrect** – Improves robustness by correcting minor typos in natural language queries.

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

## ✅ Getting started – Step-by-Step Setup

### 1. Requirements

Before running the project, make sure you have:

- [Docker](https://www.docker.com/) and [Docker Compose](https://docs.docker.com/compose/) installed
- A valid **OpenAI API key** (optional, for GPT-based models)
- (Optional) [Ollama](https://ollama.com/) installed — to use local language models

---

### 2. Clone the repository

```bash
git clone https://github.com/annaostrowska03/weather_qa_nl2sql.git
cd weather_qa_nl2sql
```

---

### 3. Create your `.env` file

Create a file named `.env` in the project root:

```env
# SQL Server configuration
SA_PASSWORD=MyStr0ngP@ssword!     # Required when using Docker for SQL Server
DB_SERVER=sqlserver               # Use 'sqlserver' with docker-compose, or 'host.docker.internal' if running SQL Server separately
DB_PORT=1433
DB_NAME=WeatherDB
DB_USER=sa
DB_PASSWORD=MyStr0ngP@ssword!     # Should match SA_PASSWORD
SQL_DRIVER=ODBC Driver 17 for SQL Server

# OpenAI (optional)
OPEN_API_KEY=sk-...

# Ollama (for local models)
OLLAMA_BASE_URL=http://host.docker.internal:11434
```

#### Password requirements for `SA_PASSWORD`:
Your password **must be strong**:
- Min. 8 characters
- Must include **uppercase**, **lowercase**, **digit**, and **special character** (e.g. `@`, `!`, `#`)

---

### 4. Choose how you want to run the app

---

#### Option A: **Using Docker Compose (recommended)**

This runs the **app and SQL Server together**, fully automated.

```bash
docker compose up --build
```

Stop with:
```bash
docker compose down
```

Open your browser at: [http://localhost:8000](http://localhost:8000)

---

#### Option B: **Using plain Docker (`docker run`)**

1. (Only once) create a Docker network:
   ```bash
   docker network create weather-net
   ```

2. Start SQL Server:
   ```bash
   docker run -d --name sqlserver --network weather-net -e SA_PASSWORD=MyStr0ngP@ssword! -e ACCEPT_EULA=Y -p 1433:1433 mcr.microsoft.com/mssql/server:2022-latest
   ```

3. Start the app:
   ```bash
   docker build -t weather-nl2sql .
   docker run -d --name weather-app --network weather-net --env-file .env -p 8000:8000 weather-nl2sql
   ```

Open your browser at: [http://localhost:8000](http://localhost:8000)

---

#### 🔹 Option C: **Run locally (without Docker)**

```bash
# Create virtual environment (optional)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Start the app
uvicorn app.main:app --reload
```
Open your browser at: [http://localhost:8000](http://localhost:8000)

---

### 5. (Optional) Running local models with Ollama

To use local models like `phi3:mini`, `mistral`, or `llama3`:

#### 1. Install Ollama
```bash
curl -fsSL https://ollama.com/install.sh | sh
```

#### 2. Run a model
```bash
ollama run mistral
# or
ollama run phi3:mini
```

The app will connect to Ollama at `http://host.docker.internal:11434`.

---


## Model Recommendation

The recommended and most accurate model is **GPT-4o mini** – highest precision, fast and best overall results.

However, this model requires a valid OpenAI API key. If you don’t have one, you can still choose from several alternative models (e.g., phi3:mini, mistral, or juierror/text-to-sql-with-table-schema) that are open-source and run locally using Ollama – although their accuracy may be lower.

To use GPT-4o mini:

- [Get your OpenAI API key](https://platform.openai.com/account/api-keys)

- Enter it into the web interface when prompted.

---

### Summary: Model Options

| Model                 | Source      | Requires API Key |
|-----------------------|-------------|------------------|
| `gpt-4o-mini`         | OpenAI      | ✅ Yes            |
| `phi3:mini`, `mistral`, `llama3` | Ollama | ❌ No             |
| `tscholak/1zha5ono`   | HuggingFace | ❌ No             |

---

You’re now ready! Open your browser at:

```text
http://localhost:8000
```

Use the web UI to enter questions and select the model you want.

  
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

**Hyperparameters tested:**

- SQL generation temp: 0.0, 0.1, 0.3,

- Answer temp: 0.5, 0.7, 1.0,

- Context length: 2048, Tokens: 64, 128.


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

## Example query

Query: 

```json
{
  "question": "Where is it raining?",
  "model": "phi3:mini",
  "api_key": ""
}
```

Response:

```json

    "sql": "SELECT City FROM Weather WHERE Weather LIKE '%rainy%'"
    "result": "Bangalore"
    "answer": "It is raining in Bangalore."
```


---

## Sample database


The default database (`WeatherDB`) is automatically created and initialized using the `init-db` service defined in `docker-compose.yml`. This service runs a provided SQL script (`init_db.sql`) to seed example weather data during startup.

If you wish to use your own custom database schema, you can modify or replace the `init_db.sql` script. However, please note that prompt templates and model behavior are aligned to the original column names and data structure — adjustments may be required to maintain accuracy if your schema differs significantly.

---

## Error Handling

Returns clear messages on:

- Empty or invalid questions
- Query translation failure
- No matching results
- Wrong/missing API Key value (when using gpt)

---

## API Documentation

This project includes automatic, interactive documentation thanks to FastAPI.

- **Swagger UI** – Full interactive docs with try-it-now interface: [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc** – Clean, readable OpenAPI spec documentation: [http://localhost:8000/redoc](http://localhost:8000/redoc)

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
├── init_db.sql             # SQL init script
```


## Author

[Anna Ostrowska](https://github.com/annaostrowska03)
 
