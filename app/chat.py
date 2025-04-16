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

import random
import json

load_dotenv()

router = APIRouter()


GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not GROQ_API_KEY:
    raise ValueError("Missing GROQ_API_KEY in environment variables")

client = Groq(api_key=GROQ_API_KEY)

class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None


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
            # Create a new conversation
            conversation = Conversation()
            db.add(conversation)
            db.commit()
            db.refresh(conversation)
            print(f"🆕 Created new conversation {conversation.id}")
        
            # Choose model config variant 
            conversation.config = os.getenv("DEFAULT_MODEL_GROUP", "A")

            # Add default prompt and knowledge sources
            addConfigurations(db, conversation, conversation.config)

            print(f"🧩 Added configurations to conversation {conversation.id}")

        user_msg = Message(
            conversation_id=conversation.id,
            role="user",
            content=req.message
        )
        db.add(user_msg)
        db.commit()
        print(f"💾 Saved user message to conversation {conversation.id}")


        config_history = create_config_history(conversation)

        # Build full message history (including system context)
        history = config_history + [
            {"role": msg.role, "content": msg.content}
            for msg in db.query(Message)
                        .filter_by(conversation_id=conversation.id)
                        .order_by(Message.timestamp)
                        .all()
        ]

        # Send the request to the Groq API
        completion = create_groq_model(history, conversation.config)
        
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
    except HTTPException as http_exc:
        raise http_exc
    
    except Exception as e:
        db.rollback()
        print("❌ Exception:", e)
        raise HTTPException(status_code=500, detail=f"Groq API error: {str(e)}")

    finally:
        db.close()
        print("🔚 DB session closed")


def addConfigurations(db, conversation, variant, config_path="config/model_variants.json"):
    system_context = []

    # Load group-specific model config including prompt and knowledge sources
    with open(config_path) as f:
        MODEL_CONFIGS = json.load(f)

    config = MODEL_CONFIGS.get(variant)
    if not config:
        raise ValueError(f"No configuration '{variant}'")

    # Load and assign default prompt profile
    prompt_text = config.get("system_prompt")
    prompt = db.query(PromptProfile).filter_by(system_prompt=prompt_text).first()
    if not prompt:
        prompt = PromptProfile(system_prompt=prompt_text)
        db.add(prompt)
        db.commit()
        db.refresh(prompt)

    conversation.prompt_profile_id = prompt.id
    db.commit()
    print(f"🧠 Attached PromptProfile {prompt.id} to conversation {conversation.id}")


    # Load knowledge sources directly from config JSON
    sources = config.get("knowledge_sources", [])


    for src in sources:
        ks = KnowledgeSource(content=src, conversation_id=conversation.id)
        db.add(ks)

    db.commit()
    print(f"📚 Attached {len(sources)} knowledge sources to conversation {conversation.id}")

    return 

def create_config_history(conversation):
    system_context = []

    # Add the system prompt from the associated profile
    if conversation.prompt_profile:
        system_context.append({
            "role": "system",
            "content": conversation.prompt_profile.system_prompt
        })

    # Fetch all knowledge sources linked to this conversation
    sources = conversation.knowledge_sources 

    if sources:
        system_context.append({
            "role": "system",
            "content": "The following sources are for your knowledge context:"
        })

        for src in sources:
            system_context.append({
                "role": "system",
                "content": src.content
            })

    return system_context



def create_groq_model(history, variant):

    # Load model variants from JSON config
    with open("config/model_variants.json") as f:
        MODEL_CONFIGS = json.load(f)

    config = MODEL_CONFIGS.get(variant)

    try:
        completion = client.chat.completions.create(
            messages=history,
            max_tokens=config["max_tokens"],
            stream=False,
            model=config["model"],
            temperature=config["temperature"],
            frequency_penalty=config["frequency_penalty"],
        )
        return completion
    except Exception as e:
        print(f"❌ Error calling Groq API config {variant}: {e}")
        raise HTTPException(status_code=502, detail="Groq API failed. Please try again.")
