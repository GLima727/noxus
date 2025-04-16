from fastapi import APIRouter, Body, HTTPException
from typing import Optional
from sqlalchemy.orm import Session
from db.database import SessionLocal
from db.models import Message
from app.scripts.refine_prompts import refine_prompts
from db.database import SessionLocal
from db.models import Conversation, Message, PromptProfile
from groq import Groq
import os
from dotenv import load_dotenv

router = APIRouter()


load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

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
        
        refine_prompt(message.conversation_id, feedback_text, thumbs_up, thumbs_down)
            

        db.commit()
        return {"success": True, "message_id": message_id}
    
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()



def refine_prompt(conversation_id, feedback_text, thumbs_up, thumbs_down):
    db = SessionLocal()
    try:
        convo = db.query(Conversation).filter_by(id=conversation_id).first()
        if not convo:
            return

        # If no prompt profile exists, create a basic one to update based on feedback
        if not convo.prompt_profile:
            default_text = "You are a helpful assistant."
            prompt = PromptProfile(system_prompt=default_text)
            db.add(prompt)
            db.commit()
            db.refresh(prompt)
            convo.prompt_profile_id = prompt.id
            db.commit()

        messages = db.query(Message).filter_by(conversation_id=conversation_id).order_by(Message.timestamp).all()
        convo_text = "\n".join([
            f"{'User' if m.role == 'user' else 'Assistant'}: {m.content}" for m in messages
        ])

        feedback_summary = ""
        if feedback_text:
            feedback_summary += f"User feedback: \"{feedback_text}\"\n"
        if thumbs_up:
            feedback_summary += "User gave a thumbs up.\n"
        elif thumbs_down:
            feedback_summary += "User gave a thumbs down.\n"

        prompt_engineering = f"""
        You are a prompt engineering assistant.
        Your goal is to refine chatbot system prompts.

        Given the original system prompt and user feedback on the assistant's performance,
        adjust the prompt slightly to better align the assistant's behavior with the feedback —
        either reinforcing what worked well, or fixing what went wrong.

        Keep the assistant's core role intact.

        Original system prompt:
        {convo.prompt_profile.system_prompt}
       
        User feedback:
        {feedback_summary}

        Conversation sample:
        {convo_text}

        Return ONLY the updated prompt.
            """
        # LLM used for system refinement
        res = client.chat.completions.create(
            model="llama3-70b-8192",
            messages=[{"role": "user", "content": prompt_engineering}],
            temperature=0.3,
            max_tokens=500,
        )

        new_prompt = res.choices[0].message.content.strip()

        if new_prompt and new_prompt != convo.prompt_profile.system_prompt:
            print(f"🧠 Refining system prompt for conversation {conversation_id}")
            convo.prompt_profile.system_prompt = new_prompt
            db.commit()

    except Exception as e:
        print(f"❌ Prompt refinement failed: {e}")
    finally:
        db.close()
