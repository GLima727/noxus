import os
import uuid
from typing import Optional

from dotenv import load_dotenv
from fastapi import APIRouter, Body, HTTPException
from groq import Groq
from pydantic import BaseModel
from sqlalchemy.orm import Session

from db.database import SessionLocal
from db.models import Conversation, KnowledgeSource, Message, PromptProfile

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

def addConfigurations(db, conversation):
    system_context = []

    # Load and assign default prompt profile
    with open("config/default_prompt.txt", "r") as f:
        prompt_text = f.read().strip()

    prompt = db.query(PromptProfile).filter_by(system_prompt=prompt_text).first()
    if not prompt:
        prompt = PromptProfile(name="Default Prompt", system_prompt=prompt_text)
        db.add(prompt)
        db.commit()
        db.refresh(prompt)

    conversation.prompt_profile_id = prompt.id
    db.commit()
    print(f"🧠 Attached PromptProfile {prompt.id} to conversation {conversation.id}")

    # Add prompt to system_context
    system_context.append({
        "role": "system",
        "content": prompt.system_prompt
    })

    # Load and assign knowledge sources
    with open("config/knowledge_sources.txt", "r") as f:
        sources = [line.strip() for line in f if line.strip()]

    if sources:
        system_context.append({
            "role": "system",
            "content": "The following sources are for your knowledge context:"
        })

    for src in sources:
        ks = KnowledgeSource(content=src, conversation_id=conversation.id)
        db.add(ks)
        system_context.append({
            "role": "system",
            "content": src
        })

    db.commit()
    print(f"📚 Attached {len(sources)} knowledge sources to conversation {conversation.id}")

    return system_context


@router.post("/chat")
async def chat(req: ChatRequest):
    db: Session = SessionLocal()
    try:
        print("🔹 Incoming request:")

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
        

        config_history = addConfigurations(db, conversation)
        print(f"🧩 Added configurations to conversation {conversation.id}")

        user_msg = Message(
            conversation_id=conversation.id,
            role="user",
            content=req.message
        )
        db.add(user_msg)
        db.commit()
        print(f"💾 Saved user message to conversation {conversation.id}")

        # Build full message history
        history = config_history + [
            {"role": msg.role, "content": msg.content}
            for msg in db.query(Message)
                        .filter_by(conversation_id=conversation.id)
                        .order_by(Message.timestamp)
                        .all()
        ]

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

        bot_msg = Message(
            conversation_id=conversation.id,
            role="assistant",
            content=bot_reply
        )
        db.add(bot_msg)
        db.commit()
        print(f"💾 Saved bot reply to conversation {conversation.id}")

        return {
            "reply": bot_reply,
            "conversation_id": str(conversation.id),
            "message_id": str(bot_msg.id) 
        }

    except Exception as e:
        db.rollback()
        print("❌ Exception:", e)
        raise HTTPException(status_code=500, detail=f"Groq API error: {str(e)}")

    finally:
        db.close()
        print("🔚 DB session closed")

@router.patch("/feedback")
async def submit_feedback(
    message_id: str = Body(...),
    thumbs_up: Optional[bool] = Body(None),
    thumbs_down: Optional[bool] = Body(None),
    feedback_text: Optional[str] = Body(None)
):
    db = SessionLocal()
    try:
        message = db.query(Message).filter_by(id=message_id).first()
        if not message:
            raise HTTPException(status_code=404, detail="Message not found")

        if thumbs_up is not None:
            message.thumbs_up = thumbs_up
        if thumbs_down is not None:
            message.thumbs_down = thumbs_down
        if feedback_text:
            message.feedback_text = feedback_text

        db.commit()
        return {"success": True, "message_id": message_id}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()