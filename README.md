# Noxus Chatbot

An LLM-powered chatbot built with FastAPI, Groq API (LLaMA 3 70B), and PostgreSQL.

## Features

-  Fast, streaming LLM responses using Groq's API
-  Persistent conversations with PostgreSQL
-  Preprompt configuration & knowledge source injection
-  User feedback with thumbs up/down + custom comments
-  Fully isolated test environment

## Requirements

- Docker + Docker Compose
- Python 3.9+ (if running locally)
- Groq API key

## Getting a Groq API Key

1. Go to https://console.groq.com/keys

2. Log in or create a free account

3. Click "Create Key" and copy the generated token

4. Add it to your .env file as GROQ_API_KEY

5. Alternatively, you can use my key:

```
GROQ_API_KEY=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
```
## Environment Setup

Create a `.env` file in the root directory:

```env
DATABASE_URL=postgresql://postgres:postgres@db:5432/noxus
GROQ_API_KEY=your-groq-api-key
FRONTEND_PATH=frontend
```

## Running the App

```bash
# Stops all containers, removes all containers, deletes all database data
docker compose down --volumes

# Builds and runs the app
docker compose up --build app db

# Runs the tests 
# Tests will use a separate test database (`noxus_test`) that is auto-created and wiped.
docker compose run --rm test

# Builds, runs the app and the tests
docker compose up --build
```

## Folder Structure

```
├── app/              # FastAPI routes & logic
├── db/               # SQLAlchemy models & DB init
├── frontend/         # HTML/CSS/JS static assets
├── config/           # Default prompts & knowledge sources
├── tests/            # Unit & integration tests
├── Dockerfile
├── docker-compose.yml
├── .env
```

## Customization

The chatbot supports different Groq model settings. Each new conversation is assigned to a configuration variant (`A`, `B`, etc.), and the chatbot's behavior changes accordingly.

You can add as many variants as you want in `model_variants.json` to test different strategies — such as more verbose prompts, different temperature values, or using another LLM.

Each variant contains:
- `model`: the Groq model ID to use (e.g., `llama3-70b-8192`)
- `temperature`, `frequency_penalty`, `presence_penalty`, `max_tokens`.
- `system_prompt`: custom instructions for that group
- `knowledge_sources`: a list of lines of context to inject at runtime


## Thought Process and Decisions

This project was my first time working with large language models (LLMs), and I wasn’t sure where to start. Downloading a full LLM to run locally wasn’t an option due to limited memory on my machine, and I wanted to avoid token-based costs or paid APIs. After researching free LLM APIs, I came across Groq — which offered fast inference with a generous free tier.

As for the database, I chose PostgreSQL because I had already worked with it on multiple projects and was comfortable using it. It provided the relational structure and flexibility I needed for storing conversations, feedback, and configurations.

Managing the Groq API was quite straight-forward. The first obstacle was providing context to the conversation.
To address this, I opted on creating a database stucture that would facilitate providing a history to the conversation, comprising of multiple messages and providing the necessary context to the LLM.

The database is structured in a simple manner:

- Conversation: Represents a full chat session. It may include preprompts and knowledge sources.
- Message: Each entry in a conversation. Linked to exactly one conversation, and has a role (user or assistant).
- PromptProfile: Optional configuration linked to a conversation to influence model behavior.
- KnowledgeSource: Additional context lines injected into the start of a conversation. A conversation can have multiple.

With this structure, each conversation can contain many messages, but each message belongs to one conversation.
Prompt profiles and knowledge sources are optional but useful for context and control. For their management, I opted for a simple solution. These prompts and knowledge sources are written in text files on the config folder, so that when the conversation is being created, these are added automatically. 

For the frontend I opted on using a simple html, css and javascript combination.

The application has two main user-facing pages:

- /chat: This is the primary chatbot interface. It provides a simple UI where users can interact with the LLM-powered assistant, receive responses, and optionally provide feedback. Each time the page is refreshed, a new conversation is generated.

- /talks: This page displays all previously stored conversations and their associated messages, including feedback. It's useful for reviewing history, analyzing interaction quality and debugging.

These pages are rendered using static HTML served by FastAPI, and they connect to backend endpoints via JavaScript to send/receive messages or retrieve conversation data.

