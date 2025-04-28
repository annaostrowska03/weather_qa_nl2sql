from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from app.database import get_db_connection
from app.models import Question
from app.nlp import generate_sql

app = FastAPI()
templates = Jinja2Templates(directory="app/templates")

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/ask")
async def ask_question(question: Question):
    sql_query = generate_sql(question.question)
    return {"sql_query": sql_query}
    '''conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(sql_query)
        results = cursor.fetchall()
        return {"results": [tuple(row) for row in results]}
    except Exception as e:
        return {"error": str(e)}
    finally:
        cursor.close()
        conn.close()'''

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)

 
