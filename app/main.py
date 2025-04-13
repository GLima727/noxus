import os

import uvicorn
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app import chat
from app import talks

from db.init_db import init_db

init_db()


app = FastAPI()
app.include_router(chat.router)
app.include_router(talks.router)

FRONTEND_PATH = os.getenv("FRONTEND_PATH", "frontend")

app.mount("/static", StaticFiles(directory=FRONTEND_PATH), name="static")


@app.get("/chat", response_class=FileResponse)
def serve_chat_page():
    return FileResponse(os.path.join(FRONTEND_PATH, "chat.html"))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
