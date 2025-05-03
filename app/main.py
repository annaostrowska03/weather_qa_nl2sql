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
        if "gpt" in model.lower() and not api_key.strip():
            return templates.TemplateResponse("index.html", {
                "request": request,
                "error": "API key is required for GPT-based models.",
                "model": model,
                "question": question,
                "api_key": api_key,
                "was_submitted": True,
                "is_gpt_and_missing_key": True
            })
        
        question_model = QuestionModel(question=question, model=model, api_key=api_key)
        sql, result_summary, final_answer, corrected_question, has_error = answer_question(question, model, api_key)
        has_error = bool(has_error)

        # if invalid api key, return error message
        if isinstance(sql, str) and "invalid_api_key" in sql.lower():
            return templates.TemplateResponse("index.html", {
                "request": request,
                "error": "Your OpenAI API key is invalid. Please double-check and try again.",
                "model": model,
                "question": question,
                "api_key": api_key,
                "was_submitted": True,
                "sql": None,
                "result": None,
                "answer": None,
                "has_error": True,
                "is_gpt_and_missing_key": True
                })
        elif isinstance(sql, str) and "insufficient_quota" in sql.lower():
            return templates.TemplateResponse("index.html", {
                    "request": request,
                    "error": "You have exceeded your OpenAI API quota. Please check your billing settings or upgrade your plan.",
                    "model": model,
                    "question": question,
                    "api_key": api_key,
                    "was_submitted": True,
                    "sql": None,
                    "result": None,
                    "answer": None,
                    "has_error": True,
                    "is_gpt_and_missing_key": True
                })

        return templates.TemplateResponse("index.html", {
            "request": request,
            "sql": sql,
            "result": result_summary,
            "answer": final_answer,
            "model": model,
            "question": question,
            "api_key": api_key,
            "has_error": has_error, 
            "was_submitted": True,
            "is_gpt_and_missing_key": False
        })

    except Exception as e:
        return templates.TemplateResponse("index.html", {
            "request": request,
            "error": f"Something went wrong: {str(e)}",
            "model": model,
            "question": question,
            "api_key": api_key,
            "was_submitted": True,
            "is_gpt_and_missing_key": False
        })

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)

 
