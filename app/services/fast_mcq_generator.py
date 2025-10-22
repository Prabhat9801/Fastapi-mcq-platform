"""
Fast MCQ Generation Service using CLIP + ChromaDB + Gemini
Optimized for speed and efficiency based on working app.py implementation
"""

from typing import List, Dict, Optional, Tuple
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
import logging
from PyPDF2 import PdfReader
import torch
from transformers import CLIPProcessor, CLIPModel
import secrets
import os
import numpy as np

from app.core.config import settings
from app.core.exceptions import AppException

logger = logging.getLogger(__name__)

# Import existing vector service to avoid conflicts
try:
    from app.services.vector_service import vector_service
    USE_SHARED_VECTOR_SERVICE = True
except:
    USE_SHARED_VECTOR_SERVICE = False
    logger.warning("Could not import vector_service, will create independent instance")


class ClipEmbeddingFunction:
    """Fast CLIP-based embedding function for text"""
    
    def __init__(self, model_path: str = None):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        
        # Use local model if available, otherwise download
        if model_path and os.path.exists(model_path):
            self.model = CLIPModel.from_pretrained(model_path).to(self.device)
            self.processor = CLIPProcessor.from_pretrained(model_path)
        else:
            self.model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32").to(self.device)
            self.processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")
        
        logger.info(f"CLIP model loaded on device: {self.device}")
    
    def embed_documents(self, texts):
        """Generate embeddings for documents (compatible with vector_service)"""
        return self._embed(texts)
    
    def embed_query(self, text):
        """Generate embedding for query (compatible with vector_service)"""
        return self._embed([text])[0]
    
    def _embed(self, texts):
        """Internal embedding method"""
        if isinstance(texts, str):
            texts = [texts]
        
        inputs = self.processor(
            text=texts, 
            return_tensors="pt", 
            padding=True, 
            truncation=True
        ).to(self.device)
        
        with torch.no_grad():
            embeddings = self.model.get_text_features(**inputs)
        
        return embeddings.cpu().numpy().tolist()


class FastMCQGenerator:
    """
    High-performance MCQ generator using CLIP embeddings + ChromaDB + Gemini
    Based on proven app.py implementation
    Uses shared vector_service to avoid conflicts
    """
    
    def __init__(self):
        # Initialize Gemini LLM
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash",
            temperature=0,
            google_api_key=settings.GOOGLE_API_KEY
        )
        self.parser = JsonOutputParser()
        
        # Initialize CLIP embeddings (will be used with vector_service)
        self.clip_embeddings = ClipEmbeddingFunction()
        
        logger.info("FastMCQGenerator initialized with CLIP + shared vector service")
    
    def extract_text_from_pdf(self, pdf_path: str, pages: Optional[str] = None) -> str:
        """
        Fast PDF text extraction using PyPDF2 (no OCR)
        """
        try:
            reader = PdfReader(pdf_path)
            text = ""
            
            # Handle None, empty string, or invalid input
            if not pages or pages.strip() == "" or pages.strip().lower() == "string":
                pages = None
            
            if pages is None:
                # Extract all pages
                for page in reader.pages:
                    text += page.extract_text() or ""
            else:
                # Parse page specification
                try:
                    page_numbers = set()
                    page_ranges = pages.split(',')
                    
                    for page_range in page_ranges:
                        page_range = page_range.strip()
                        if '-' in page_range:
                            start, end = map(int, page_range.split('-'))
                            page_numbers.update(range(start - 1, end))
                        else:
                            page_numbers.add(int(page_range) - 1)
                    
                    # Extract specified pages
                    for page_num in sorted(page_numbers):
                        if 0 <= page_num < len(reader.pages):
                            text += reader.pages[page_num].extract_text() or ""
                            
                except ValueError as e:
                    logger.warning(f"Invalid page specification '{pages}', using all pages")
                    # Fall back to all pages
                    for page in reader.pages:
                        text += page.extract_text() or ""
            
            if not text.strip():
                raise AppException("No text could be extracted from PDF")
            
            logger.info(f"Extracted {len(text)} characters from PDF")
            return text
            
        except Exception as e:
            logger.error(f"Error extracting text from PDF: {e}")
            raise AppException(f"Failed to extract PDF text: {str(e)}")
    
    def chunk_text(self, text: str, chunk_size: int = 50, overlap: int = 10) -> List[str]:
        """
        Intelligently chunk text by words with overlap
        
        Args:
            text: Input text
            chunk_size: Words per chunk
            overlap: Overlapping words between chunks
        
        Returns:
            List of text chunks
        """
        words = text.split()
        chunks = []
        
        for i in range(0, len(words), chunk_size - overlap):
            chunk = " ".join(words[i:i + chunk_size])
            if chunk.strip():
                chunks.append(chunk)
        
        logger.info(f"Created {len(chunks)} chunks from text")
        return chunks
    
    def get_or_create_collection(self, collection_name: str):
        """Get or create ChromaDB collection using shared vector service"""
        try:
            # Use existing vector_service to avoid conflicts
            # Pass metadata as dictionary, not the embedding function
            metadata = {"created_by": "fast_mcq_generator", "embedding_model": "clip"}
            vector_service.create_collection(collection_name, metadata)
            logger.info(f"Created/reused collection: {collection_name}")
            return collection_name
        except Exception as e:
            logger.error(f"Error creating collection: {e}")
            raise AppException(f"Failed to create collection: {str(e)}")
    
    def add_to_vector_db(self, collection_name: str, chunks: List[str]):
        """Add text chunks to vector database using CLIP embeddings"""
        try:
            # Get the collection directly from vector service
            collection = vector_service.client.get_collection(name=collection_name)
            
            # Generate CLIP embeddings
            embeddings = self.clip_embeddings.embed_documents(chunks)
            
            # Generate IDs
            ids = [f"clip_chunk_{i}" for i in range(len(chunks))]
            
            # Add to collection with CLIP embeddings
            collection.add(
                documents=chunks,
                embeddings=embeddings,
                ids=ids
            )
            
            logger.info(f"Added {len(chunks)} chunks to vector database")
        except Exception as e:
            logger.error(f"Error adding to vector DB: {e}")
            raise AppException(f"Failed to add documents: {str(e)}")
    
    def retrieve_relevant_chunks(
        self, 
        collection_name: str,
        query: str, 
        n_results: int = 3
    ) -> List[str]:
        """Retrieve most relevant chunks using CLIP embeddings"""
        try:
            # Get the collection directly from vector service
            collection = vector_service.client.get_collection(name=collection_name)
            
            # Generate CLIP embedding for the query
            query_embedding = self.clip_embeddings.embed_query(query)
            
            # Query the collection
            results = collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results
            )
            
            chunks = results['documents'][0] if results['documents'] else []
            logger.info(f"Retrieved {len(chunks)} relevant chunks for query")
            
            return chunks
        except Exception as e:
            logger.error(f"Error retrieving chunks: {e}")
            raise AppException(f"Failed to retrieve chunks: {str(e)}")
    
    def generate_mcqs(
        self,
        context: str,
        query_scope: str,
        num_questions: int = 10,
        difficulty_level: str = "medium"
    ) -> List[Dict]:
        """
        Generate MCQs from context using Gemini
        
        Args:
            context: Source text for questions
            query_scope: Topic focus for questions
            num_questions: Number of questions to generate
            difficulty_level: easy, medium, or hard
        
        Returns:
            List of MCQ dictionaries
        """
        try:
            # Create prompt
            prompt = ChatPromptTemplate.from_messages([
                ("system", "You are a quiz generator. Generate multiple-choice questions."),
                ("human", """Context: {context}

Generate {num_questions} multiple-choice questions (MCQs) in JSON format.
Focus on the topic: {query_scope}
Difficulty level: {difficulty_level}

Requirements:
- Each question should have exactly 4 options
- Provide the correct answer index (0-3)
- Questions should be clear and unambiguous
- Options should be plausible and relevant

Output format:
[
  {{
    "question": "Question text here?",
    "options": ["Option A", "Option B", "Option C", "Option D"],
    "correct_answer_index": 0
  }}
]

Generate {num_questions} questions now:""")
            ])
            
            # Format prompt
            formatted_prompt = prompt.format(
                context=context,
                query_scope=query_scope,
                num_questions=num_questions,
                difficulty_level=difficulty_level
            )
            
            # Generate MCQs
            response = self.llm.invoke(formatted_prompt)
            mcqs = self.parser.parse(response.content)
            
            if not mcqs or len(mcqs) == 0:
                raise AppException("Failed to generate MCQs")
            
            logger.info(f"Generated {len(mcqs)} MCQs")
            return mcqs
            
        except Exception as e:
            logger.error(f"Error generating MCQs: {e}")
            raise AppException(f"MCQ generation failed: {str(e)}")
    
    def generate_test_from_pdf(
        self,
        pdf_path: str,
        num_questions: int = 10,
        difficulty_level: str = "medium",
        topic_scope: str = "comprehensive",
        specific_pages: Optional[str] = None,
        chunk_size: int = 50,
        overlap: int = 10,
        retrieval_chunks: int = 3
    ) -> Tuple[List[Dict], str]:
        """
        Complete pipeline: PDF -> Chunks -> Vector DB -> Retrieval -> MCQ Generation
        Uses shared vector_service to avoid conflicts
        
        Args:
            pdf_path: Path to PDF file
            num_questions: Number of questions to generate
            difficulty_level: Question difficulty
            topic_scope: Topic focus
            specific_pages: Page specification (optional)
            chunk_size: Words per chunk
            overlap: Overlapping words
            retrieval_chunks: Number of chunks to retrieve for context
        
        Returns:
            Tuple of (MCQs list, collection_name)
        """
        collection_name = None
        
        try:
            # Step 1: Extract text from PDF
            logger.info("Step 1: Extracting text from PDF")
            text = self.extract_text_from_pdf(pdf_path, specific_pages)
            
            # Step 2: Chunk text
            logger.info("Step 2: Chunking text")
            chunks = self.chunk_text(text, chunk_size, overlap)
            
            if not chunks:
                raise AppException("No text chunks generated from PDF")
            
            # Step 3: Create vector database collection
            logger.info("Step 3: Creating vector database collection")
            collection_name = f"test_{secrets.token_hex(8)}"
            self.get_or_create_collection(collection_name)
            
            # Step 4: Add chunks to vector DB
            logger.info("Step 4: Adding chunks to vector database")
            self.add_to_vector_db(collection_name, chunks)
            
            # Step 5: Retrieve relevant chunks
            logger.info("Step 5: Retrieving relevant context")
            context_chunks = self.retrieve_relevant_chunks(
                collection_name,
                topic_scope,
                n_results=retrieval_chunks
            )
            
            if not context_chunks:
                raise AppException("No relevant context found")
            
            context_text = " ".join(context_chunks)
            
            # Step 6: Generate MCQs
            logger.info("Step 6: Generating MCQs with Gemini")
            mcqs = self.generate_mcqs(
                context_text,
                topic_scope,
                num_questions,
                difficulty_level
            )
            
            logger.info(f"✅ Successfully generated {len(mcqs)} MCQs")
            return mcqs, collection_name
            
        except Exception as e:
            # Cleanup on error
            if collection_name:
                try:
                    self.delete_collection(collection_name)
                    logger.info(f"Cleaned up collection: {collection_name}")
                except:
                    pass
            
            logger.error(f"Test generation failed: {e}")
            raise AppException(f"Failed to generate test: {str(e)}")
    
    def delete_collection(self, collection_name: str):
        """Delete a vector database collection using shared vector service"""
        try:
            vector_service.delete_collection(collection_name)
            logger.info(f"Deleted collection: {collection_name}")
        except Exception as e:
            logger.warning(f"Failed to delete collection {collection_name}: {e}")


# Singleton instance
fast_mcq_generator = FastMCQGenerator()
