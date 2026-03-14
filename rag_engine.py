"""
RAG Engine - Retrieval Augmented Generation
Handles chunk retrieval and answer generation using AI
"""

import httpx
import json
from typing import List, Dict
from config import settings
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np


class RAGEngine:
    """RAG pipeline for document Q&A"""
    
    def __init__(self):
        self.api_url = settings.OLLAMA_API_URL
        self.model = settings.OLLAMA_MODEL
        self.top_k = settings.TOP_K_CHUNKS
        self.max_history = settings.MAX_CONVERSATION_HISTORY
        
    def retrieve_chunks(self, query: str, chunks: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """
        Retrieve most relevant chunks using TF-IDF and cosine similarity
        
        Args:
            query: User's question
            chunks: All document chunks
            
        Returns:
            Top-k most relevant chunks
        """
        if not chunks:
            return []
        
        # Extract text from chunks
        chunk_texts = [chunk['text'] for chunk in chunks]
        
        # Create TF-IDF vectors
        vectorizer = TfidfVectorizer(
            lowercase=True,
            stop_words='english',
            max_features=1000
        )
        
        try:
            # Fit vectorizer on chunks and query
            tfidf_matrix = vectorizer.fit_transform(chunk_texts + [query])
            
            # Get query vector (last row)
            query_vector = tfidf_matrix[-1]
            
            # Get chunk vectors (all rows except last)
            chunk_vectors = tfidf_matrix[:-1]
            
            # Calculate cosine similarity
            similarities = cosine_similarity(query_vector, chunk_vectors).flatten()
            
            # Get top-k indices
            top_indices = np.argsort(similarities)[-self.top_k:][::-1]
            
            # Return top chunks with similarity scores
            relevant_chunks = []
            for idx in top_indices:
                chunk = chunks[idx].copy()
                chunk['relevance_score'] = float(similarities[idx])
                relevant_chunks.append(chunk)
            
            return relevant_chunks
            
        except Exception as e:
            # Fallback: return first k chunks if TF-IDF fails
            print(f"TF-IDF failed: {e}. Using fallback.")
            return chunks[:self.top_k]
    
    async def generate_answer(
        self,
        question: str,
        chunks: List[Dict[str, str]],
        conversation_history: List[Dict[str, str]] = None
    ) -> str:
        """
        Generate answer using Anthropic's Claude API
        
        Args:
            question: User's question
            chunks: Relevant document chunks
            conversation_history: Previous messages
            
        Returns:
            Ollama-generated answer
        """
        # Build context from chunks
        context = self._build_context(chunks)
        
        # Build conversation history
        messages = self._build_messages(question, context, conversation_history)
        
        # Call Ollama API
        try:
            answer = await self._call_ollama_api(messages)
            return answer
        except Exception as e:
            raise Exception(f"Error generating answer: {str(e)}")
    
    def _build_context(self, chunks: List[Dict[str, str]]) -> str:
        """Build context string from chunks"""
        if not chunks:
            return "No relevant information found in the document."
        
        context_parts = []
        for i, chunk in enumerate(chunks, 1):
            source = chunk.get('source', 'Unknown')
            text = chunk.get('text', '')
            context_parts.append(f"[Source: {source}]\n{text}")
        
        return "\n\n".join(context_parts)
    
    def _build_messages(
        self,
        question: str,
        context: str,
        conversation_history: List[Dict[str, str]] = None
    ) -> List[Dict[str, str]]:
        """Build message array for API call"""
        
        # System message with instructions
        system_prompt = """You are a helpful AI assistant that answers questions based on the provided document context.

Guidelines:
- Answer questions accurately based ONLY on the information in the provided context
- If the answer is not in the context, say "I don't have enough information in the document to answer that question."
- Be concise but thorough
- Cite sources when possible (e.g., "According to Page 3...")
- If asked about something not in the document, politely redirect to what IS in the document"""
        
        messages = []
        
        # Add recent conversation history (keep last N messages)
        if conversation_history:
            history = conversation_history[-self.max_history:]
            for msg in history:
                if msg.get('role') in ['user', 'assistant']:
                    messages.append({
                        'role': msg['role'],
                        'content': msg['content']
                    })
        
        # Add current question with context
        user_message = f"""Context from document:
{context}

Question: {question}

Please answer based on the context provided above."""
        
        messages.append({
            'role': 'user',
            'content': user_message
        })
        
        return messages
    
    async def _call_ollama_api(self, messages: List[Dict[str, str]]) -> str:
        """
        Call Ollama API to generate response
        
        Args:
            messages: Conversation messages
            
        Returns:
            Generated text response
        """
        headers = {"Content-Type": "application/json"}
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "options": {
                "num_predict": settings.MAX_TOKENS,
                "temperature": settings.TEMPERATURE
            }
        }
        
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                self.api_url,
                headers=headers,
                json=payload
            )
            
            if response.status_code != 200:
                raise Exception(f"API error: {response.status_code} - {response.text}")
            
            result = response.json()
            
            if 'message' in result and 'content' in result['message']:
                return result['message']['content']
            else:
                raise Exception(f"Unexpected Ollama response format: {result}")
    
    async def generate_suggested_questions(self, chunks: List[Dict[str, str]]) -> List[str]:
        """
        Generate suggested questions based on document content
        
        Args:
            chunks: Document chunks to analyze
            
        Returns:
            List of suggested questions
        """
        if not chunks:
            return [
                "What is this document about?",
                "Can you summarize the main points?",
                "What are the key takeaways?"
            ]
        
        # Build sample content
        sample_content = "\n\n".join([chunk['text'] for chunk in chunks[:3]])
        
        messages = [{
            'role': 'user',
            'content': f"""Based on this document excerpt, generate 5 specific, interesting questions that a reader might want to ask:

{sample_content}

Return ONLY a JSON array of questions, nothing else. Format:
["Question 1?", "Question 2?", "Question 3?", "Question 4?", "Question 5?"]"""
        }]
        
        try:
            response = await self._call_ollama_api(messages)
            
            # Try to parse JSON response
            # Clean up the response in case there's extra text
            response = response.strip()
            if '```json' in response:
                response = response.split('```json')[1].split('```')[0].strip()
            elif '```' in response:
                response = response.split('```')[1].split('```')[0].strip()
            
            questions = json.loads(response)
            
            if isinstance(questions, list) and len(questions) > 0:
                return questions[:5]
            
        except Exception as e:
            print(f"Error generating questions: {e}")
        
        # Fallback questions
        return [
            "What are the main topics covered in this document?",
            "Can you summarize the key points?",
            "What conclusions or recommendations are made?",
            "Are there any important statistics or data?",
            "What is the overall purpose of this document?"
        ]
