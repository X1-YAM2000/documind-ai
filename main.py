"""
DocuMind AI - FastAPI Backend
AI-powered Document Q&A system with RAG pipeline
"""

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import uvicorn
import os
from datetime import datetime

from document_processor import DocumentProcessor
from rag_engine import RAGEngine
from config import settings

# Initialize FastAPI app
app = FastAPI(
    title="DocuMind AI API",
    description="AI-powered Document Q&A System with RAG",
    version="1.0.0"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize processors
doc_processor = DocumentProcessor()
rag_engine = RAGEngine()

# Request/Response Models
class ChatMessage(BaseModel):
    role: str  # 'user' or 'assistant'
    content: str
    timestamp: Optional[str] = None

class QuestionRequest(BaseModel):
    question: str
    conversation_history: Optional[List[ChatMessage]] = []
    document_id: Optional[str] = None

class QuestionResponse(BaseModel):
    answer: str
    relevant_chunks: List[dict]
    sources: List[str]
    timestamp: str

class DocumentInfo(BaseModel):
    document_id: str
    filename: str
    total_chunks: int
    upload_time: str
    file_size: int
    file_type: str

class SuggestedQuestionsResponse(BaseModel):
    questions: List[str]


# In-memory storage (replace with database in production)
documents_store = {}
chunks_store = {}


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "online",
        "service": "DocuMind AI",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat()
    }


@app.post("/upload", response_model=DocumentInfo)
async def upload_document(file: UploadFile = File(...)):
    """
    Upload and process a document (PDF or TXT)
    
    Returns:
        - document_id: Unique identifier for the document
        - filename: Original filename
        - total_chunks: Number of chunks created
        - upload_time: Upload timestamp
    """
    try:
        # Validate file type
        if not file.filename.endswith(('.pdf', '.txt')):
            raise HTTPException(
                status_code=400,
                detail="Only PDF and TXT files are supported"
            )
        
        # Read file content
        content = await file.read()
        file_size = len(content)
        
        # Generate document ID
        document_id = f"doc_{datetime.now().strftime('%Y%m%d%H%M%S')}_{file.filename}"
        
        # Process document
        if file.filename.endswith('.pdf'):
            chunks = await doc_processor.process_pdf(content)
        else:
            chunks = await doc_processor.process_text(content.decode('utf-8'))
        
        # Store document metadata and chunks
        documents_store[document_id] = {
            'filename': file.filename,
            'upload_time': datetime.now().isoformat(),
            'file_size': file_size,
            'file_type': 'pdf' if file.filename.endswith('.pdf') else 'txt',
            'total_chunks': len(chunks)
        }
        chunks_store[document_id] = chunks
        
        return DocumentInfo(
            document_id=document_id,
            filename=file.filename,
            total_chunks=len(chunks),
            upload_time=documents_store[document_id]['upload_time'],
            file_size=file_size,
            file_type=documents_store[document_id]['file_type']
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing document: {str(e)}")


@app.post("/ask", response_model=QuestionResponse)
async def ask_question(request: QuestionRequest):
    """
    Ask a question about the uploaded document
    
    Args:
        - question: The user's question
        - conversation_history: Previous chat messages
        - document_id: ID of the document to query
    
    Returns:
        - answer: AI-generated answer
        - relevant_chunks: Text chunks used to generate answer
        - sources: Page/section references
    """
    try:
        # Get document chunks
        if request.document_id and request.document_id in chunks_store:
            chunks = chunks_store[request.document_id]
        elif chunks_store:
            # Use the most recent document if no ID specified
            latest_doc = max(chunks_store.keys())
            chunks = chunks_store[latest_doc]
        else:
            raise HTTPException(
                status_code=400,
                detail="No document uploaded. Please upload a document first."
            )
        
        # Retrieve relevant chunks
        relevant_chunks = rag_engine.retrieve_chunks(request.question, chunks)
        
        # Generate answer using RAG
        answer = await rag_engine.generate_answer(
            question=request.question,
            chunks=relevant_chunks,
            conversation_history=request.conversation_history
        )
        
        # Extract sources
        sources = [chunk.get('source', 'Unknown') for chunk in relevant_chunks]
        
        return QuestionResponse(
            answer=answer,
            relevant_chunks=relevant_chunks,
            sources=list(set(sources)),  # Remove duplicates
            timestamp=datetime.now().isoformat()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating answer: {str(e)}")


@app.get("/documents", response_model=List[DocumentInfo])
async def list_documents():
    """List all uploaded documents"""
    return [
        DocumentInfo(
            document_id=doc_id,
            filename=info['filename'],
            total_chunks=info['total_chunks'],
            upload_time=info['upload_time'],
            file_size=info['file_size'],
            file_type=info['file_type']
        )
        for doc_id, info in documents_store.items()
    ]


@app.delete("/documents/{document_id}")
async def delete_document(document_id: str):
    """Delete a document and its chunks"""
    if document_id not in documents_store:
        raise HTTPException(status_code=404, detail="Document not found")
    
    del documents_store[document_id]
    del chunks_store[document_id]
    
    return {"message": "Document deleted successfully", "document_id": document_id}


@app.post("/suggest-questions", response_model=SuggestedQuestionsResponse)
async def suggest_questions(document_id: Optional[str] = None):
    """
    Generate suggested questions based on the document content
    """
    try:
        # Get document chunks
        if document_id and document_id in chunks_store:
            chunks = chunks_store[document_id]
        elif chunks_store:
            latest_doc = max(chunks_store.keys())
            chunks = chunks_store[latest_doc]
        else:
            return SuggestedQuestionsResponse(questions=[
                "What is this document about?",
                "Can you summarize the main points?",
                "What are the key takeaways?"
            ])
        
        # Generate contextual questions
        questions = await rag_engine.generate_suggested_questions(chunks[:5])
        
        return SuggestedQuestionsResponse(questions=questions)
        
    except Exception as e:
        # Return default questions if generation fails
        return SuggestedQuestionsResponse(questions=[
            "What is this document about?",
            "Can you summarize the main points?",
            "What are the key topics discussed?",
            "Are there any important conclusions?",
            "What recommendations are made?"
        ])


@app.get("/health")
async def health_check():
    """Detailed health check"""
    return {
        "status": "healthy",
        "documents_loaded": len(documents_store),
        "total_chunks": sum(len(chunks) for chunks in chunks_store.values()),
        "uptime": "running"
    }


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )
