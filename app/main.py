from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import chat
import uvicorn
import os
from db.init_db import init_db
init_db()


app = FastAPI()
app.include_router(chat.router)

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/ping")
def ping():
    return {"message": "pong"}

@app.get("/chat", response_class=FileResponse)
def serve_chat_page():
    return FileResponse("static/index.html")

@app.get("/db-tables")
def check_tables():
    from sqlalchemy import inspect
    from db.database import engine
    inspector = inspect(engine)
    return {"tables": inspector.get_table_names()}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
