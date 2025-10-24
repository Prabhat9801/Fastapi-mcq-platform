"""
RAG-Enabled Chatbot Service
Combines general AI knowledge with document-based RAG capabilities
"""

import logging
from typing import List, Dict, Tuple, Optional
import google.generativeai as genai
from app.core.config import settings
from app.core.exceptions import AppException
from app.services.vector_service import vector_service
from app.services.fast_mcq_generator import fast_mcq_generator

logger = logging.getLogger(__name__)


class RAGChatbot:
    """Intelligent chatbot with RAG capabilities"""
    
    def __init__(self):
        """Initialize the RAG chatbot"""
        self.model = None
        self.initialize()
    
    def initialize(self):
        """Initialize Gemini AI model"""
        try:
            genai.configure(api_key=settings.GOOGLE_API_KEY)
            self.model = genai.GenerativeModel('gemini-2.0-flash-exp')
            logger.info("RAG Chatbot initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing RAG Chatbot: {e}")
            raise AppException(f"Failed to initialize chatbot: {str(e)}")
    
    def should_use_rag(self, question: str) -> bool:
        """
        Determine if the question requires RAG-based document search
        """
        # Keywords that suggest document-based queries
        document_keywords = [
            'according to', 'based on', 'in the document', 'from the text',
            'what does the paper say', 'explain from', 'summarize', 'define',
            'chapter', 'section', 'figure', 'table', 'study', 'research',
            'algorithm', 'method', 'technique', 'approach', 'framework'
        ]
        
        # Technical terms that might be in uploaded documents
        technical_keywords = [
            'cnn', 'neural network', 'deep learning', 'machine learning',
            'fer', 'face', 'emotion', 'recognition', 'classification',
            'mlp', 'convolutional', 'pooling', 'activation', 'backpropagation'
        ]
        
        question_lower = question.lower()
        
        # Check for document-specific keywords
        for keyword in document_keywords:
            if keyword in question_lower:
                return True
        
        # Check for technical keywords that might be in documents
        for keyword in technical_keywords:
            if keyword in question_lower:
                return True
        
        return False
    
    def get_available_collections(self) -> List[str]:
        """Get list of available vector collections"""
        try:
            if hasattr(vector_service, 'client') and vector_service.client:
                collections = vector_service.client.list_collections()
                return [col.name for col in collections]
            return []
        except Exception as e:
            logger.warning(f"Could not get collections: {e}")
            return []
    
    def search_documents(self, question: str, max_chunks: int = 5) -> List[str]:
        """
        Search for relevant document chunks using RAG
        """
        try:
            collections = self.get_available_collections()
            if not collections:
                logger.info("No document collections available for RAG")
                return []
            
            all_chunks = []
            
            # Search across all available collections
            for collection_name in collections:
                try:
                    # Use the fast MCQ generator's CLIP-based search
                    chunks = fast_mcq_generator.retrieve_relevant_chunks(
                        collection_name=collection_name,
                        query=question,
                        n_results=max_chunks // len(collections) + 1
                    )
                    all_chunks.extend(chunks)
                except Exception as e:
                    logger.warning(f"Error searching collection {collection_name}: {e}")
                    continue
            
            # Return top chunks (remove duplicates)
            unique_chunks = []
            seen = set()
            for chunk in all_chunks:
                if chunk not in seen:
                    unique_chunks.append(chunk)
                    seen.add(chunk)
                if len(unique_chunks) >= max_chunks:
                    break
            
            logger.info(f"Found {len(unique_chunks)} relevant chunks for question")
            return unique_chunks
        
        except Exception as e:
            logger.error(f"Error searching documents: {e}")
            return []
    
    def generate_response(self, question: str, conversation_context: List[Dict] = None) -> str:
        """
        Generate intelligent response using either RAG or general knowledge
        """
        try:
            if not self.model:
                self.initialize()
            
            # Decide whether to use RAG
            use_rag = self.should_use_rag(question)
            
            if use_rag:
                return self._generate_rag_response(question, conversation_context)
            else:
                return self._generate_general_response(question, conversation_context)
        
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return f"I apologize, but I encountered an error while processing your question. Please try again."
    
    def _generate_rag_response(self, question: str, conversation_context: List[Dict] = None) -> str:
        """Generate response using RAG with document context"""
        try:
            # Search for relevant document chunks
            relevant_chunks = self.search_documents(question)
            
            if not relevant_chunks:
                # Fall back to general response if no relevant documents found
                return self._generate_general_response(question, conversation_context, 
                                                    fallback_note="I searched through available documents but couldn't find specific relevant information. ")
            
            # Build context from document chunks
            context = "\n\n".join([f"Document excerpt {i+1}: {chunk}" 
                                 for i, chunk in enumerate(relevant_chunks)])
            
            # Build conversation context
            conversation_prompt = ""
            if conversation_context:
                recent_messages = conversation_context[-4:]  # Last 4 messages
                for msg in recent_messages:
                    conversation_prompt += f"{msg['sender']}: {msg['message']}\n"
            
            # Create RAG prompt
            prompt = f"""You are a helpful AI assistant with access to document content. Answer the user's question based on the provided document excerpts and your general knowledge.

Document Context:
{context}

{f"Previous conversation:{conversation_prompt}" if conversation_prompt else ""}

User Question: {question}

Instructions:
1. Prioritize information from the document excerpts when relevant
2. If the documents contain relevant information, cite them in your response
3. If the documents don't contain enough information, supplement with your general knowledge
4. Be accurate, helpful, and conversational
5. If you're not certain about something, say so

Answer:"""

            response = self.model.generate_content(prompt)
            return response.text.strip()
        
        except Exception as e:
            logger.error(f"Error in RAG response generation: {e}")
            return self._generate_general_response(question, conversation_context, 
                                                fallback_note="I had trouble accessing document information, so I'll answer based on my general knowledge. ")
    
    def _generate_general_response(self, question: str, conversation_context: List[Dict] = None, fallback_note: str = "") -> str:
        """Generate response using general AI knowledge"""
        try:
            # Build conversation context
            conversation_prompt = ""
            if conversation_context:
                recent_messages = conversation_context[-4:]  # Last 4 messages
                for msg in recent_messages:
                    conversation_prompt += f"{msg['sender']}: {msg['message']}\n"
            
            # Create general knowledge prompt
            prompt = f"""You are a helpful, knowledgeable AI assistant. Answer the user's question based on your training knowledge.

{f"Previous conversation:{conversation_prompt}" if conversation_prompt else ""}

User Question: {question}

Instructions:
1. Provide accurate, helpful information
2. Be conversational and friendly
3. If you're not certain about something, acknowledge the uncertainty
4. Keep responses concise but informative
5. For technical topics, explain concepts clearly

{fallback_note}Answer:"""

            response = self.model.generate_content(prompt)
            return response.text.strip()
        
        except Exception as e:
            logger.error(f"Error in general response generation: {e}")
            return "I apologize, but I'm having trouble generating a response right now. Please try asking your question again."
    
    def get_conversation_context(self, messages: List[Dict]) -> List[Dict]:
        """Extract relevant context from conversation history"""
        # Return last few messages for context
        return messages[-6:] if messages else []


# Singleton instance
rag_chatbot = RAGChatbot()