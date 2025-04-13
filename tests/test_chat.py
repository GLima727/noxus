# tests/test_chat.py

from fastapi.testclient import TestClient
from app.main import app
from unittest.mock import patch

client = TestClient(app)

# Test the chat endpoint with a basic request
def test_chat_endpoint_basic():
    response = client.post("/chat", json={"message": "Hello!", "max_length": 50, "temperature": 0.7})
    assert response.status_code == 200
    data = response.json()
    assert "reply" in data
    assert "conversation_id" in data
    assert "message_id" in data

# Test creating a new conversation
def test_chat_creates_new_conversation():
    response = client.post("/chat", json={"message": "Start a new one!"})
    assert response.status_code == 200
    data = response.json()
    assert data["conversation_id"] is not None

# Test providing feedback to a message
def test_feedback_update():
    chat_res = client.post("/chat", json={"message": "Test feedback"})
    message_id = chat_res.json()["message_id"]

    patch_res = client.patch("/feedback", json={
        "message_id": message_id,
        "thumbs_up": True,
        "feedback_text": "Great reply!"
    })
    assert patch_res.status_code == 200

# Test for sendin a message without conversation_id
def test_invalid_conversation_id_format():
    res = client.post("/chat", json={"message": "--------------", "conversation_id": "not-a-uuid"})
    assert res.status_code == 400

# Test for feedback on message that doesn't exist
def test_feedback_invalid_message():
    res = client.patch("/feedback", json={"message_id": "00000000-0000-0000-0000-000000000000", "thumbs_up": True})
    assert res.status_code == 404

# Test for checking Groq API failure
def test_groq_api_failure():
    with patch("app.chat.client.chat.completions.create") as mock_groq:
        mock_groq.side_effect = Exception("Simulated Groq failure")
        
        response = client.post("/chat", json={
            "message": "Trigger failure",
            "max_length": 50,
            "temperature": 0.7
        })

        assert response.status_code == 502
        assert "Groq API failed" in response.json()["detail"]