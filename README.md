# DocuMind AI - FastAPI Backend (Ollama Edition)

A production-ready FastAPI backend for AI-powered Document Q&A using RAG (Retrieval Augmented Generation), powered by your local **Ollama** instance.

## Features

- 📄 **PDF & TXT Support**: Process PDF and plain text documents
- 🔍 **Smart Chunking**: Automatically splits documents into 1500-character overlapping chunks
- 🤖 **Local LLM**: Powered by local Ollama (default: `llama3.1:8b`)
- 💬 **Conversation Memory**: Maintains last 6 messages for context
- 🎯 **Suggested Questions**: Auto-generates relevant questions from document
- 🔒 **Privacy Focused**: No data leaves your machine

## Architecture

```
┌─────────────┐
│   Upload    │
│   PDF/TXT   │
└──────┬──────┘
       │
       ▼
┌─────────────────┐
│ Document        │
│ Processor       │
│ - Extract text  │
│ - Create chunks │
└──────┬──────────┘
       │
       ▼
┌─────────────────┐
│ RAG Engine      │
│                 │
│ 1. Retrieve     │◄───┐
│    (TF-IDF)     │    │
│                 │    │ User
│ 2. Generate     │    │ Question
│    (Ollama LLM) │    │
└──────┬──────────┘    │
       │                │
       ▼                │
┌─────────────────┐    │
│   AI Answer     │────┘
│ + Sources       │
└─────────────────┘
```

## Setup

### 1. Requirements
- [Ollama](https://ollama.com/) installed and running.
- Model `llama3.1:8b` pulled: `ollama pull llama3.1:8b`

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure Environment
Create `.env` file:
```env
OLLAMA_API_URL=http://localhost:11434/api/chat
OLLAMA_MODEL=llama3.1:8b
```

### 4. Run the Server
```bash
python main.py
```

The API will be available at: `http://localhost:8000`
Documentation: `http://localhost:8000/docs`

## API Endpoints

### 📤 Upload Document
`POST /upload` - Multipart form-data with `file` field.

### 💬 Ask Question
`POST /ask` - JSON with `question`, `document_id`, and `conversation_history`.

### 💡 Suggested Questions
`POST /suggest-questions` - Generates questions based on document content.

## License
MIT License
