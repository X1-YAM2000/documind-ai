"""
Test script for DocuMind AI backend
Run this to verify your setup is working correctly
"""

import asyncio
import httpx
import os
from pathlib import Path


BASE_URL = "http://localhost:8000"


async def test_health_check():
    """Test if server is running"""
    print("🔍 Testing health check...")
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/health")
        if response.status_code == 200:
            print("✅ Server is healthy!")
            print(f"   Response: {response.json()}")
        else:
            print(f"❌ Health check failed: {response.status_code}")
    print()


async def test_root():
    """Test root endpoint"""
    print("🔍 Testing root endpoint...")
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/")
        if response.status_code == 200:
            print("✅ Root endpoint working!")
            print(f"   Response: {response.json()}")
        else:
            print(f"❌ Root endpoint failed: {response.status_code}")
    print()


async def test_upload_sample():
    """Test document upload with a sample text file"""
    print("🔍 Testing document upload...")
    
    # Create a sample text file
    sample_text = """
    Artificial Intelligence and Machine Learning
    
    Introduction
    Artificial Intelligence (AI) is the simulation of human intelligence by machines. 
    It involves creating systems that can perform tasks requiring human-like intelligence.
    
    Key Concepts
    Machine Learning is a subset of AI that enables systems to learn from data.
    Deep Learning uses neural networks with multiple layers to process complex patterns.
    
    Applications
    AI is used in healthcare for diagnosis, in finance for fraud detection, 
    and in autonomous vehicles for navigation. The applications are vast and growing.
    
    Conclusion
    AI technology continues to evolve rapidly, transforming industries and creating 
    new possibilities for innovation.
    """
    
    files = {
        'file': ('sample_doc.txt', sample_text.encode(), 'text/plain')
    }
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(f"{BASE_URL}/upload", files=files)
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Upload successful!")
            print(f"   Document ID: {data['document_id']}")
            print(f"   Filename: {data['filename']}")
            print(f"   Total chunks: {data['total_chunks']}")
            return data['document_id']
        else:
            print(f"❌ Upload failed: {response.status_code}")
            print(f"   Error: {response.text}")
            return None
    print()


async def test_ask_question(document_id):
    """Test asking a question"""
    print("🔍 Testing question answering...")
    
    question_data = {
        "question": "What is artificial intelligence?",
        "conversation_history": [],
        "document_id": document_id
    }
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            f"{BASE_URL}/ask",
            json=question_data
        )
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Question answered successfully!")
            print(f"   Question: {question_data['question']}")
            print(f"   Answer: {data['answer'][:200]}...")
            print(f"   Sources: {data['sources']}")
            print(f"   Relevant chunks: {len(data['relevant_chunks'])}")
        else:
            print(f"❌ Question failed: {response.status_code}")
            print(f"   Error: {response.text}")
    print()


async def test_suggested_questions(document_id):
    """Test suggested questions"""
    print("🔍 Testing suggested questions...")
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            f"{BASE_URL}/suggest-questions",
            json={"document_id": document_id}
        )
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Suggested questions generated!")
            print("   Questions:")
            for i, q in enumerate(data['questions'], 1):
                print(f"   {i}. {q}")
        else:
            print(f"❌ Suggested questions failed: {response.status_code}")
    print()


async def test_list_documents():
    """Test listing documents"""
    print("🔍 Testing document listing...")
    
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/documents")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Found {len(data)} document(s)")
            for doc in data:
                print(f"   - {doc['filename']} ({doc['total_chunks']} chunks)")
        else:
            print(f"❌ List documents failed: {response.status_code}")
    print()


async def run_tests():
    """Run all tests"""
    print("=" * 60)
    print("DocuMind AI Backend Test Suite")
    print("=" * 60)
    print()
    
    # Check if server is running
    try:
        await test_health_check()
    except Exception as e:
        print(f"❌ Cannot connect to server at {BASE_URL}")
        print(f"   Error: {e}")
        print("\n💡 Make sure the server is running:")
        print("   python main.py")
        return
    
    await test_root()
    
    # Upload a document
    document_id = await test_upload_sample()
    
    if document_id:
        # Test question answering
        await test_ask_question(document_id)
        
        # Test suggested questions
        await test_suggested_questions(document_id)
        
        # List all documents
        await test_list_documents()
    
    print("=" * 60)
    print("Test suite complete!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(run_tests())
