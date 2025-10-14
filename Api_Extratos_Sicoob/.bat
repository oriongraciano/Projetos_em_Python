cd C:\sicoob_api
call C:\sicoob_api\venv\Scripts\activate.bat
uvicorn app.main:app --host 0.0.0.0 --port 8000
