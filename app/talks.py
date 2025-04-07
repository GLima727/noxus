from fastapi import APIRouter, Depends
from fastapi.responses import HTMLResponse, FileResponse
from sqlalchemy.orm import Session
from db.database import SessionLocal
from db.models import Conversation, Message
import os

router = APIRouter()

FRONTEND_PATH = os.path.join(os.path.dirname(__file__), "..", "frontend")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/talks", response_class=HTMLResponse)
def serve_conversations_page():
    return FileResponse(os.path.join(FRONTEND_PATH, "talks.html"))


@router.get("/talks-data")
def get_conversations_data(db: Session = Depends(get_db)):
    conversations = db.query(Conversation).all()
    data = []

    for convo in conversations:
        messages = db.query(Message).filter_by(conversation_id=convo.id).order_by(Message.timestamp).all()
        data.append({
            "conversation_id": str(convo.id),
            "started_at": convo.started_at.isoformat(),
            "messages": [
                {
                    "role": msg.role,
                    "content": msg.content,
                    "timestamp": msg.timestamp.isoformat(),
                    "thumbs_up": msg.thumbs_up,
                    "thumbs_down": msg.thumbs_down,
                    "feedback_text": msg.feedback_text
                } for msg in messages
            ]
        })

    return data
