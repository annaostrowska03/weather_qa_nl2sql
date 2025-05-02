from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from app.database import get_db_connection
from app.models import Question as QuestionModel
from app.nlp import answer_question
from fastapi.staticfiles import StaticFiles


app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="app/templates")

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/ask")
async def ask_question(request: Request,
                       question: str = Form(...),
                       model: str = Form(...),
                       api_key: str = Form("")):
    try:
        question_model = QuestionModel(question=question, model=model, api_key=api_key)
    except Exception as e:
        return templates.TemplateResponse("index.html", {"request": request, "error": str(e)})
    
    sql, result, final_answer, has_error = answer_question(question, model, api_key)
    return templates.TemplateResponse("index.html", {"request": request, "sql": sql, "result": result, "answer": final_answer, "model": model, "question": question, "api_key": api_key, "has_error": has_error})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)

 
