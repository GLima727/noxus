# tests/test_config.py

import os
import tempfile
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

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

# Create a temporary directory for testing
@pytest.fixture
def temp_config_files(tmp_path):
    # Create temp default prompt and knowledge source files
    prompt_file = tmp_path / "default_prompt.txt"
    prompt_file.write_text("You are a helpful assistant.")

    ks_file = tmp_path / "knowledge_sources.txt"
    ks_file.write_text("This is source one.\nThis is source two.")

    os.makedirs("config_test", exist_ok=True)
    os.replace(prompt_file, "config_test/default_prompt.txt")
    os.replace(ks_file, "config_test/knowledge_sources.txt")

    #waits for tests to be over
    yield

    # Cleanup
    os.remove("config_test/default_prompt.txt")
    os.remove("config_test/knowledge_sources.txt")
    os.rmdir("config_test")

# Test the addConfigurations function to verify knowledge sources and prompt profile creation
def test_add_configurations(db_session, temp_config_files):
    conversation = Conversation()
    db_session.add(conversation)
    db_session.commit()
    db_session.refresh(conversation)

    system_context = addConfigurations(db_session, conversation, prompt_path="config_test/default_prompt.txt", sources_path="config_test/knowledge_sources.txt")

    db_session.refresh(conversation)
    assert conversation.prompt_profile_id is not None

    sources = db_session.query(KnowledgeSource).filter_by(conversation_id=conversation.id).all()
    assert len(sources) == 2
    print(system_context)

    assert system_context[0]["role"] == "system"
    assert system_context[0]["content"] == "You are a helpful assistant."
    assert system_context[1]["content"] == "The following sources are for your knowledge context:"
    assert system_context[2]["content"] == "This is source one."
    assert system_context[3]["content"] == "This is source two."
