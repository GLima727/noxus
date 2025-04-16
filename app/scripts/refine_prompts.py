# scripts/refine_prompts.py

import os
import json
from dotenv import load_dotenv
from sqlalchemy.orm import Session
from db.database import SessionLocal
from db.models import Conversation, Message, PromptProfile
from groq import Groq
from .evaluate import evaluate_conversations

load_dotenv()
groq = Groq(api_key=os.getenv("GROQ_API_KEY"))


def get_feedback_prompt(convo_text, current_prompt):
    return f"""
            You are an expert in prompt engineering.

            You are given a system prompt used by a chatbot and a sample conversation. Your task is to make small but meaningful refinements to the system prompt, so that future responses align better with the user’s needs — as demonstrated in the conversation — while preserving the original intention of the prompt.

            Please return an improved version of the prompt that:

            1. Maintains the original role and boundaries of the assistant.
            2. Better handles the type of interaction shown (e.g., emotional support, clarifications, technical detail).
            3. Is only adjusted if the conversation shows real room for improvement.

            Current system prompt:
            \"\"\"{current_prompt}\"\"\"

            Conversation sample:
            {convo_text}

            Return only the improved system prompt (no explanations).
            """

# Update the system prompt of conversations with a lower rating than 6
def refine_prompts(evaluations):
    db: Session = SessionLocal()
    updated_prompts = 0

    for eval in evaluations:
        if eval["score"] is None or eval["score"] >= 6:
            continue  # Only refine for low scores

        convo = db.query(Conversation).filter_by(id=eval["conversation_id"]).first()
        if not convo or not convo.prompt_profile:
            continue

        messages = (
            db.query(Message)
            .filter_by(conversation_id=convo.id)
            .order_by(Message.timestamp)
            .all()
        )

        convo_text = "\n".join([
            f"{'User' if m.role == 'user' else 'Assistant'}: {m.content}" for m in messages
        ])

        prompt = get_feedback_prompt(convo_text, convo.prompt_profile.system_prompt)

        try:
            #LLM chosen for the system prompt update
            res = groq.chat.completions.create(
                model="llama3-70b-8192",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=500,
            )

            new_prompt = res.choices[0].message.content.strip()

            if new_prompt and new_prompt != convo.prompt_profile.system_prompt:
                print(f"🔄 Updating prompt for convo {convo.id}")
                convo.prompt_profile.system_prompt = new_prompt
                updated_prompts += 1
        except Exception as e:
            print(f"⚠️ Failed to refine prompt for convo {convo.id}: {e}")

    db.commit()
    db.close()
    print(f"✅ Refined {updated_prompts} prompts.")


if __name__ == "__main__":
    
    evaluations = evaluate_conversations()
    refine_prompts(evaluations)
