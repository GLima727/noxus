from fastapi.testclient import TestClient
from app.main import app
from db.database import SessionLocal
from db.models import Conversation, Message

client = TestClient(app)

def test_conversation_missing_prompt():
    db = SessionLocal()
    try:
        # Create a conversation without assigning a prompt_profile_id or knowledge sources
        convo = Conversation()
        db.add(convo)
        db.commit()
        db.refresh(convo)

        response = client.post("/chat", json={
            "message": "Hello, test edge case!",
            "conversation_id": str(convo.id)
        })

        assert response.status_code != 500, "Should handle missing prompt gracefully"

        data = response.json()
        assert "reply" in data or "detail" in data  

    finally:
        db.close()


client = TestClient(app)

def test_feedback_adds_prompt_profile():
    db = SessionLocal()
    try:
        # Create a conversation with no prompt profile
        convo = Conversation()
        db.add(convo)
        db.commit()
        db.refresh(convo)

        # Add a bot message (to be the one receiving feedback)
        msg = Message(
            conversation_id=convo.id,
            role="assistant",
            content="This is a basic bot reply."
        )
        db.add(msg)
        db.commit()
        db.refresh(msg)

        # Submit feedback to trigger a new system prompt
        response = client.patch("/feedback", json={
            "message_id": str(msg.id),
            "thumbs_up": True,
            "feedback_text": "Very helpful!"
        })

        assert response.status_code == 200

        # Reload conversation and assert a prompt was assigned
        db.refresh(convo)
        assert convo.prompt_profile_id is not None

    finally:
        db.close()
