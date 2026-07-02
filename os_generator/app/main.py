from fastapi import FastAPI
from app.database import Base, engine
from app.routes.os_routes import router as os_router
from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

Base.metadata.create_all(bind=engine)

app = FastAPI(title="OS Generator API")

app.include_router(os_router)

app.mount("/static", StaticFiles(directory="app/static"), name="static")

templates = Jinja2Templates(directory="app/templates")

@app.get("/")
def home():
    return {"message": "OS Generator API rodando com sucesso!"}

@app.get("/form")
def abrir_formulario(request: Request):
    return templates.TemplateResponse(
        request=request,
          name="form.html"
    )