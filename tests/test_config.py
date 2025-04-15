# tests/test_config.py

import os
import tempfile
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import json
from db.models import Base, Conversation, PromptProfile, KnowledgeSource
from app.chat import addConfigurations 

@pytest.fixture
def db_session():
    # Use an in-memory SQLite DB for isolated testing
    engine = create_engine("sqlite:///:memory:")
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


# Test the addConfigurations function to verify knowledge sources and prompt profile creation
def test_add_configurations(db_session):
    # Temporarily replace the config file
    with open("config/test_model_variants.json", "w") as f:
        json.dump({
            "D": {
                "model": "llama3-8b-8192",
                "temperature": 0.5,
                "frequency_penalty": 0,
                "max_tokens": 300,
                "system_prompt": "This is a test prompt for variant D.",
                "knowledge_sources": [
                    "Test source one.",
                    "Test source two."
                ]
            }
        }, f)

    conversation = Conversation()
    db_session.add(conversation)
    db_session.commit()
    db_session.refresh(conversation)

    # Override your function to read the test file
    system_context = addConfigurations(db_session, conversation, "D", config_path="config/test_model_variants.json")

    sources = db_session.query(KnowledgeSource).filter_by(conversation_id=conversation.id).all()
    print([s.content for s in sources])
    assert len(sources) == 2
    assert sources[0].content == "Test source one."
    assert sources[1].content == "Test source two."