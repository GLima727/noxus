from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import os
from dotenv import load_dotenv
from groq import Groq
from db.database import SessionLocal
from db.models import Conversation, Message
from sqlalchemy.orm import Session
import uuid
from typing import Optional

load_dotenv()

router = APIRouter()


GROQ_API_KEY = os.getenv("HF_API_KEY")

if not GROQ_API_KEY:
    raise ValueError("Missing GROQ_API_KEY in environment variables")

client = Groq(api_key=GROQ_API_KEY)

class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None
    max_length: int = 100
    temperature: float = 0.7



@router.post("/chat")
async def chat(req: ChatRequest):
    db: Session = SessionLocal()
    try:
        print("🔹 Incoming request:", req.dict())

        # Step 1: Create or fetch conversation
        if req.conversation_id:
            try:
                conversation_uuid = uuid.UUID(req.conversation_id)
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid conversation_id format")
            
            conversation = db.query(Conversation).filter_by(id=conversation_uuid).first()
            if not conversation:
                raise HTTPException(status_code=404, detail="Conversation not found")
            print(f"🔄 Continuing conversation {conversation.id}")
        else:
            conversation = Conversation()
            db.add(conversation)
            db.commit()
            db.refresh(conversation)
            print(f"🆕 Created new conversation {conversation.id}")

        # Step 2: Save user message
        user_msg = Message(
            conversation_id=conversation.id,
            role="user",
            content=req.message
        )
        db.add(user_msg)
        db.commit()
        print(f"💾 Saved user message to conversation {conversation.id}")

        # Step 3: Fetch full history
        history = [
            {"role": msg.role, "content": msg.content}
            for msg in db.query(Message)
                         .filter_by(conversation_id=conversation.id)
                         .order_by(Message.timestamp)
                         .all()
        ]
        print(f"📜 Message history for {conversation.id}: {history}")

        # Step 4: Send to Groq
        completion = client.chat.completions.create(
            model="llama3-70b-8192",
            messages=history,
            temperature=req.temperature,
            max_tokens=req.max_length,
            top_p=1,
            stream=False,
        )

        bot_reply = completion.choices[0].message.content
        print(f"🤖 Bot reply: {bot_reply}")

        # Step 5: Save bot reply
        bot_msg = Message(
            conversation_id=conversation.id,
            role="assistant",
            content=bot_reply
        )
        db.add(bot_msg)
        db.commit()
        print(f"💾 Saved bot reply to conversation {conversation.id}")

        # Step 6: Return reply and conversation ID
        return {
            "reply": bot_reply,
            "conversation_id": str(conversation.id)
        }

    except Exception as e:
        db.rollback()
        print("❌ Exception:", e)
        raise HTTPException(status_code=500, detail=f"Groq API error: {str(e)}")

    finally:
        db.close()
        print("🔚 DB session closed")
