import os
import json
from dotenv import load_dotenv
from sqlalchemy.orm import Session
from collections import defaultdict
from db.database import SessionLocal
from db.models import Conversation, Message
from groq import Groq

load_dotenv()

groq = Groq(api_key=os.getenv("GROQ_API_KEY"))

def evaluate_conversations():
    db: Session = SessionLocal()
    conversations = db.query(Conversation).all()
    results = []

    for convo in conversations:
        messages = (
            db.query(Message)
            .filter_by(conversation_id=convo.id)
            .order_by(Message.timestamp)
            .all()
        )

        dialogue = ""
        for m in messages:
            role = "User" if m.role == "user" else "Assistant"
            dialogue += f"{role}: {m.content}\n"

        evaluation_prompt = f"""
            Evaluate the quality of the assistant's responses in the following conversation.
            Score the conversation from 1 to 10 based on relevance, clarity, and helpfulness.
            Then explain your reasoning in 1-2 sentences.

            Conversation:
            {dialogue}

            Return your answer in the following format:
            {{"score": <1-10>, "comment": "..."}}
            """

        try:
            # Model chosen for evaluation
            response = groq.chat.completions.create(
                model="llama3-70b-8192",
                messages=[
                    {"role": "user", "content": evaluation_prompt}
                ],
                temperature=0.3,
                max_tokens=300,
                stream=False,
            )

            raw = response.choices[0].message.content.strip()
            result = json.loads(raw)
            results.append({
                "conversation_id": str(convo.id),
                "config": convo.config,
                "score": result.get("score"),
                "comment": result.get("comment")
            })

        except Exception as e:
            print(f"⚠️ Evaluation failed for conversation {convo.id}: {e}")

    return results

def evaluate_configurations(evaluations):
    config_scores = defaultdict(list)

    for eval in evaluations:
        if eval["score"] is not None:
            config_scores[eval["config"]].append(eval["score"])

    averages = {
        config: sum(scores) / len(scores)
        for config, scores in config_scores.items()
    }

    return averages

if __name__ == "__main__":
    evaluations = evaluate_conversations()
    print("\n=== Evaluation Results ===")
    for e in evaluations:
        print(f"\nConversation: {e['conversation_id']} | Config: {e['config']}")
        print(f"Score: {e['score']} | Comment: {e['comment']}")

    print("\n=== Configuration Averages ===")
    config_summary = evaluate_configurations(evaluations)
    for config, avg_score in config_summary.items():
        print(f"Config {config}: Average Score = {avg_score:.2f}")