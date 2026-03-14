"""
Document processor for extracting and chunking text from PDF and TXT files
"""

import io
import re
from typing import List, Dict
from PyPDF2 import PdfReader
from config import settings


class DocumentProcessor:
    """Process and chunk documents"""
    
    def __init__(self):
        self.chunk_size = settings.CHUNK_SIZE
        self.chunk_overlap = settings.CHUNK_OVERLAP
    
    async def process_pdf(self, pdf_content: bytes) -> List[Dict[str, str]]:
        """
        Extract text from PDF and split into chunks
        
        Args:
            pdf_content: Raw PDF file bytes
            
        Returns:
            List of chunk dictionaries with text and metadata
        """
        try:
            # Read PDF
            pdf_file = io.BytesIO(pdf_content)
            pdf_reader = PdfReader(pdf_file)
            
            chunks = []
            
            # Extract text from each page
            for page_num, page in enumerate(pdf_reader.pages, start=1):
                text = page.extract_text()
                
                if text.strip():
                    # Split page into chunks
                    page_chunks = self._create_chunks(text)
                    
                    # Add metadata to each chunk
                    for i, chunk_text in enumerate(page_chunks):
                        chunks.append({
                            'text': chunk_text,
                            'source': f'Page {page_num}',
                            'page': page_num,
                            'chunk_index': i,
                            'type': 'pdf'
                        })
            
            return chunks
            
        except Exception as e:
            raise Exception(f"Error processing PDF: {str(e)}")
    
    async def process_text(self, text_content: str) -> List[Dict[str, str]]:
        """
        Process plain text and split into chunks
        
        Args:
            text_content: Plain text string
            
        Returns:
            List of chunk dictionaries with text and metadata
        """
        try:
            chunks = []
            text_chunks = self._create_chunks(text_content)
            
            for i, chunk_text in enumerate(text_chunks):
                chunks.append({
                    'text': chunk_text,
                    'source': f'Section {i + 1}',
                    'chunk_index': i,
                    'type': 'txt'
                })
            
            return chunks
            
        except Exception as e:
            raise Exception(f"Error processing text: {str(e)}")
    
    def _create_chunks(self, text: str) -> List[str]:
        """
        Split text into overlapping chunks
        
        Args:
            text: Input text to chunk
            
        Returns:
            List of text chunks
        """
        # Clean text
        text = self._clean_text(text)
        
        chunks = []
        start = 0
        text_length = len(text)
        
        while start < text_length:
            # Calculate end position
            end = start + self.chunk_size
            
            # If this isn't the last chunk, try to break at a sentence
            if end < text_length:
                # Look for sentence endings near the chunk boundary
                chunk_text = text[start:end]
                
                # Try to find the last sentence ending
                last_period = chunk_text.rfind('. ')
                last_question = chunk_text.rfind('? ')
                last_exclamation = chunk_text.rfind('! ')
                
                last_sentence_end = max(last_period, last_question, last_exclamation)
                
                # If we found a sentence ending, use it
                if last_sentence_end > self.chunk_size * 0.5:  # At least 50% through chunk
                    end = start + last_sentence_end + 2  # Include the period and space
                
                chunks.append(text[start:end].strip())
                
                # Move start position (with overlap)
                start = end - self.chunk_overlap
            else:
                # Last chunk
                chunks.append(text[start:].strip())
                break
        
        return [chunk for chunk in chunks if chunk]  # Remove empty chunks
    
    def _clean_text(self, text: str) -> str:
        """
        Clean and normalize text
        
        Args:
            text: Raw text
            
        Returns:
            Cleaned text
        """
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove multiple newlines
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        # Strip leading/trailing whitespace
        text = text.strip()
        
        return text
