# Noxus Chatbot

An LLM-powered chatbot built with FastAPI, Groq API (LLaMA 3 70B), and PostgreSQL.

## Features

-  Fast, streaming LLM responses using Groq's API
-  Preprompt configuration & knowledge source injection
-  User feedback with thumbs up/down + custom comments
-  Adaptive behavior based on user feedback

## Requirements

- Docker + Docker Compose
- Python 3.9+ (if running locally)
- Groq API key

## Getting a Groq API Key

1. Go to https://console.groq.com/keys

2. Log in or create a free account

3. Click "Create Key" and copy the generated token

4. Add it to your .env file as GROQ_API_KEY

## Environment Setup

Create a `.env` file in the root directory:

```env
GROQ_API_KEY = groq_key
DATABASE_URL = postgresql://postgres:postgres@db:5432/noxus
FRONTEND_PATH = frontend
DEFAULT_MODEL_GROUP=A
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
├── app/scripts       # Scripts for evaluation and configuration refinement  
├── db/               # Database models & DB init
├── frontend/         # HTML/CSS/JS static assets
├── config/           # Default prompts & knowledge sources
├── tests/            # Unit & integration tests
├── Dockerfile
├── docker-compose.yml
├── .env
```

## Customization

The chatbot supports different Groq model settings. Each new conversation is assigned to a configuration variant (`A`, `B`, etc.), and the chatbot's behavior changes accordingly. The model variant is chosen in the `.env` file in `DEFAULT_MODEL_GROUP=`. The default option is currently `A`

You can add as many variants as you want in `model_variants.json` to test different strategies, such as more verbose prompts, different temperature values, different tones, or using another LLM as long as it is available in the Groq API.

Each variant contains:
- `model`: the Groq model ID to use (e.g., `llama3-70b-8192`)
- `temperature`, `frequency_penalty`, `presence_penalty`, `max_tokens`.
- `system_prompt`: custom instructions for that group
- `knowledge_sources`: could be URLs, personal information or extra custom instructions that are added to the context.


## Thought Process and Decisions

This project was my first time working with LLMs. Downloading a full LLM to run locally wasn’t an option due to the limited memory of my machine, and I wanted to avoid token-based costs or paid APIs. After researching free LLM APIs, I came across Groq, which offered fast inference with a generous free tier.

As for the database, I chose PostgreSQL because I had already worked with it on multiple projects and was comfortable using it. It provided the relational structure and flexibility I needed for storing conversations, feedback, and configurations.

Managing the Groq API was quite straight-forward. The first obstacle was providing context for the conversation.
To address this, I opted on creating a database structure that would facilitate providing a history to the conversation, comprising of multiple messages and providing the necessary context to the LLM. 

The database is structured in a simple manner:

- Conversation: Represents a full chat session. It may include preprompts and knowledge sources.
- Message: Each entry in a conversation. Linked to exactly one conversation, and has a role (user or assistant).
- PromptProfile: Optional configuration linked to a conversation to influence model behavior.
- KnowledgeSource: Additional context lines injected into the start of a conversation. A conversation can have multiple.

With this structure, each conversation can contain many messages, but each message belongs to one conversation.
Prompt profiles and knowledge sources are optional but useful for context and control. For their management, I opted for a simple solution. These prompts and knowledge sources are written in text files in the config folder, so that when the conversation is being created, these are added automatically. 

For the frontend I opted on using a simple html, css and javascript combination.

The application has two main user pages:

- /chat: This is the primary chatbot interface. It provides a simple UI where users can interact with the LLM-powered assistant, receive responses, and optionally provide feedback. Each time the page is refreshed, a new conversation is generated.

- /talks: This page displays all previously stored conversations and their associated messages, including feedback. It's useful for reviewing history, analyzing interaction quality and debugging.

These pages are rendered using static HTML served by FastAPI, and they connect to backend endpoints via JavaScript to send/receive messages or retrieve conversation data.

## A/B Testing

Our project, as mentioned before, supports different Groq model settings and configurations. Each configuration has a letter assigned to a configuration variant (`A`, `B`, etc.).
To evaluate the effectiveness of different language model configurations we can collect the amount of feedback given to each model configuration and evaluate which model has the most positive or negative reviews (in the form of thumbs up or down).
For custom reviews we can utilize the LLM to evaluate if the review is positive or not.

## Conversation and Configuration Evaluation

To assess the effectiveness of the chatbot's responses, this project includes a built-in evaluation framework powered by another LLM (via Groq API). The goal is to automatically rate the quality of each conversation and compare performance across different chatbot configurations.

The quality of each conversation is based on:

- **Relevance**: Are the assistant's responses aligned with the user's intent?
- **Clarity**: Are the replies easy to understand and well-structured?
- **Helpfulness**: Do the answers solve or meaningfully respond to the user's query?

The LLM returns a **score from 1 to 10** and a brief **commentary** explaining the evaluation.

To evaluate each configuration associated with one or more conversations, the evaluation framework computes the **average score per configuration**. This allows for easy identification of which model variant leads to higher quality interactions.

Execute this command as the app is running:

```bash
docker compose exec app python app/scripts/evaluate.py
```

## Prompt Refinement

To enhance the chatbot's adaptability, the platform includes a script for a **prompt refinement system**. This mechanism uses conversation evaluations and user feedback to continuously improve the system prompt associated with each chatbot configuration.

Once a conversation receives a **low evaluation score** (currently less than 6), the script uses a separate LLM to rewrite the prompt in a way that better fits the observed user needs, based on the original system prompt and full conversation history. It makes sure to preserve the original role and only make small and purposeful adjustments.

This script is used after evaluations have been generated. To manually refine prompts based on the latest evaluations run this command:

```bash
docker compose exec app python app/scripts/refine_prompts.py
```

## Automatic Adaptive Learning

The chatbot implements an adaptive learning mechanism that improves its behavior in real time based on user feedback.

After each bot response, users can give thumbs up/down or provide free-form feedback.
When feedback is given, it is immediately used to update and refine the existing chatbot's system prompt, reinforcing helpful patterns when feedback is positive and avoiding undesired behavior when feedback is negative. 