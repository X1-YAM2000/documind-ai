# DocuMind AI - API Documentation

Complete API reference for the DocuMind AI Document Q&A system.

## Base URL

```
http://localhost:8000
```

## Authentication

Currently no authentication required. For production, implement API keys or JWT tokens.

---

## Endpoints

### 1. Health Check

Check if the API is running and healthy.

**Endpoint:** `GET /health`

**Response:**
```json
{
  "status": "healthy",
  "documents_loaded": 3,
  "total_chunks": 127,
  "uptime": "running"
}
```

---

### 2. Root Endpoint

Basic service information.

**Endpoint:** `GET /`

**Response:**
```json
{
  "status": "online",
  "service": "DocuMind AI",
  "version": "1.0.0",
  "timestamp": "2025-03-14T12:00:00.000000"
}
```

---

### 3. Upload Document

Upload a PDF or TXT file for processing.

**Endpoint:** `POST /upload`

**Content-Type:** `multipart/form-data`

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| file | File | Yes | PDF or TXT file to upload |

**Request Example (cURL):**
```bash
curl -X POST http://localhost:8000/upload \
  -F "file=@document.pdf"
```

**Request Example (JavaScript):**
```javascript
const formData = new FormData();
formData.append('file', fileInput.files[0]);

const response = await fetch('http://localhost:8000/upload', {
  method: 'POST',
  body: formData
});

const data = await response.json();
```

**Success Response (200 OK):**
```json
{
  "document_id": "doc_20250314120000_research_paper.pdf",
  "filename": "research_paper.pdf",
  "total_chunks": 42,
  "upload_time": "2025-03-14T12:00:00.123456",
  "file_size": 245680,
  "file_type": "pdf"
}
```

**Error Response (400 Bad Request):**
```json
{
  "detail": "Only PDF and TXT files are supported"
}
```

---

### 4. Ask Question

Ask a question about an uploaded document.

**Endpoint:** `POST /ask`

**Content-Type:** `application/json`

**Request Body:**
```json
{
  "question": "What is the main conclusion of this paper?",
  "conversation_history": [
    {
      "role": "user",
      "content": "What is this document about?",
      "timestamp": "2025-03-14T12:00:00"
    },
    {
      "role": "assistant",
      "content": "This document discusses machine learning applications...",
      "timestamp": "2025-03-14T12:00:05"
    }
  ],
  "document_id": "doc_20250314120000_research_paper.pdf"
}
```

**Request Parameters:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| question | string | Yes | The user's question |
| conversation_history | array | No | Previous chat messages (max 6 kept) |
| document_id | string | No | Specific document to query (uses latest if omitted) |

**Request Example (JavaScript):**
```javascript
const response = await fetch('http://localhost:8000/ask', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    question: "What are the main findings?",
    conversation_history: [],
    document_id: "doc_20250314120000_research_paper.pdf"
  })
});

const data = await response.json();
```

**Success Response (200 OK):**
```json
{
  "answer": "Based on the document, the main findings indicate that machine learning models achieve 95% accuracy when trained on diverse datasets. The study found three key factors contributing to this success: data quality, model architecture, and training methodology.",
  "relevant_chunks": [
    {
      "text": "Our experiments demonstrate that machine learning models...",
      "source": "Page 5",
      "page": 5,
      "chunk_index": 12,
      "type": "pdf",
      "relevance_score": 0.87
    },
    {
      "text": "The results show significant improvements in accuracy...",
      "source": "Page 12",
      "page": 12,
      "chunk_index": 28,
      "type": "pdf",
      "relevance_score": 0.82
    }
  ],
  "sources": ["Page 5", "Page 12"],
  "timestamp": "2025-03-14T12:05:30.123456"
}
```

**Error Response (400 Bad Request):**
```json
{
  "detail": "No document uploaded. Please upload a document first."
}
```

---

### 5. List Documents

Get all uploaded documents.

**Endpoint:** `GET /documents`

**Response (200 OK):**
```json
[
  {
    "document_id": "doc_20250314120000_research_paper.pdf",
    "filename": "research_paper.pdf",
    "total_chunks": 42,
    "upload_time": "2025-03-14T12:00:00.123456",
    "file_size": 245680,
    "file_type": "pdf"
  },
  {
    "document_id": "doc_20250314130000_notes.txt",
    "filename": "notes.txt",
    "total_chunks": 15,
    "upload_time": "2025-03-14T13:00:00.123456",
    "file_size": 12450,
    "file_type": "txt"
  }
]
```

---

### 6. Delete Document

Delete a document and its chunks from the system.

**Endpoint:** `DELETE /documents/{document_id}`

**Path Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| document_id | string | ID of document to delete |

**Request Example (cURL):**
```bash
curl -X DELETE http://localhost:8000/documents/doc_20250314120000_research_paper.pdf
```

**Success Response (200 OK):**
```json
{
  "message": "Document deleted successfully",
  "document_id": "doc_20250314120000_research_paper.pdf"
}
```

**Error Response (404 Not Found):**
```json
{
  "detail": "Document not found"
}
```

---

### 7. Suggest Questions

Generate suggested questions based on document content.

**Endpoint:** `POST /suggest-questions`

**Content-Type:** `application/json`

**Request Body:**
```json
{
  "document_id": "doc_20250314120000_research_paper.pdf"
}
```

**Request Parameters:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| document_id | string | No | Specific document to analyze (uses latest if omitted) |

**Success Response (200 OK):**
```json
{
  "questions": [
    "What methodology was used in the research?",
    "What are the key findings of the study?",
    "What datasets were used for training?",
    "How does this compare to previous research?",
    "What are the limitations of this approach?"
  ]
}
```

---

## Data Models

### ChatMessage

```typescript
{
  role: "user" | "assistant",
  content: string,
  timestamp?: string  // ISO 8601 format
}
```

### DocumentChunk

```typescript
{
  text: string,           // Chunk content
  source: string,         // e.g., "Page 5" or "Section 3"
  page?: number,          // Page number (PDF only)
  chunk_index: number,    // Index in document
  type: "pdf" | "txt",    // File type
  relevance_score?: number // 0-1 similarity score
}
```

---

## Error Codes

| Code | Description |
|------|-------------|
| 200 | Success |
| 400 | Bad Request (invalid input) |
| 404 | Resource Not Found |
| 500 | Internal Server Error |

**Error Response Format:**
```json
{
  "detail": "Error message explaining what went wrong"
}
```

---

## Rate Limits

No rate limits currently implemented. For production:
- Recommend: 100 requests per minute per IP
- Implement using FastAPI middleware or nginx

---

## CORS Configuration

Default allowed origins:
- `http://localhost:3000`
- `http://localhost:5173`
- `http://127.0.0.1:3000`
- `http://127.0.0.1:5173`

To add more origins, update `ALLOWED_ORIGINS` in `.env`:

```env
ALLOWED_ORIGINS=http://localhost:3000,https://your-domain.com
```

---

## Interactive API Documentation

FastAPI provides interactive documentation:

- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

These provide:
- Full API schema
- Try-it-out functionality
- Request/response examples
- Schema definitions

---

## Example: Complete Workflow

### Step 1: Upload Document

```javascript
// Upload a PDF
const formData = new FormData();
formData.append('file', pdfFile);

const uploadRes = await fetch('http://localhost:8000/upload', {
  method: 'POST',
  body: formData
});

const { document_id } = await uploadRes.json();
```

### Step 2: Get Suggested Questions

```javascript
const suggestRes = await fetch('http://localhost:8000/suggest-questions', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ document_id })
});

const { questions } = await suggestRes.json();
```

### Step 3: Ask Questions

```javascript
const conversationHistory = [];

// First question
const ask1 = await fetch('http://localhost:8000/ask', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    question: questions[0],
    conversation_history: conversationHistory,
    document_id
  })
});

const answer1 = await ask1.json();

// Add to history
conversationHistory.push(
  { role: 'user', content: questions[0] },
  { role: 'assistant', content: answer1.answer }
);

// Follow-up question (with context)
const ask2 = await fetch('http://localhost:8000/ask', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    question: "Can you elaborate on that?",
    conversation_history: conversationHistory,
    document_id
  })
});

const answer2 = await ask2.json();
```

---

## WebSocket Support (Future Enhancement)

For real-time streaming responses, consider adding WebSocket endpoint:

```python
@app.websocket("/ws/ask")
async def websocket_ask(websocket: WebSocket):
    await websocket.accept()
    # Stream AI responses in real-time
```

---

## Best Practices

1. **Document Management:** Delete old documents to free memory
2. **Conversation History:** Keep last 6 messages for context
3. **Error Handling:** Always check response status codes
4. **File Size:** Limit uploads to 50MB
5. **Question Quality:** Be specific for better answers

---

## Support

- API Issues: Check `/health` endpoint
- Documentation: Visit `/docs` for interactive testing
- Logs: Check server console output for errors
