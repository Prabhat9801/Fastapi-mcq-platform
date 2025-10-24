"""
Vector Database Service using ChromaDB
Manages document embeddings and retrieval
"""

import chromadb
from chromadb.config import Settings as ChromaSettings
import torch
from transformers import CLIPProcessor, CLIPModel
from typing import List, Optional, Dict
import logging

from app.core.config import settings
from app.core.exceptions import AppException

logger = logging.getLogger(__name__)


class VectorService:
    """ChromaDB vector database service with CLIP embeddings"""
    
    def __init__(self):
        self.client = None
        self.clip_model = None
        self.clip_processor = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.initialized = False
    
    def initialize(self):
        """Initialize ChromaDB client and CLIP model"""
        try:
            # Initialize ChromaDB
            self.client = chromadb.PersistentClient(
                path="./chroma_db",
                settings=ChromaSettings(anonymized_telemetry=False)
            )
            
            # Load CLIP model
            logger.info("Loading CLIP model...")
            
            # Try to load from local path first
            try:
                self.clip_model = CLIPModel.from_pretrained(settings.CLIP_MODEL_PATH).to(self.device)
                self.clip_processor = CLIPProcessor.from_pretrained(settings.CLIP_MODEL_PATH)
                logger.info(f"Loaded CLIP model from {settings.CLIP_MODEL_PATH}")
            except:
                # Download if not available
                logger.info("Downloading CLIP model from HuggingFace...")
                model_name = "openai/clip-vit-base-patch32"
                self.clip_model = CLIPModel.from_pretrained(model_name).to(self.device)
                self.clip_processor = CLIPProcessor.from_pretrained(model_name)
                logger.info("CLIP model downloaded successfully")
            
            self.initialized = True
            logger.info("Vector service initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing vector service: {e}")
            raise AppException(f"Vector service initialization failed: {str(e)}")
    
    def get_text_embedding(self, texts: List[str]) -> List[List[float]]:
        """Generate CLIP embeddings for text"""
        if not self.initialized:
            self.initialize()
        
        try:
            inputs = self.clip_processor(
                text=texts,
                return_tensors="pt",
                padding=True,
                truncation=True,
                max_length=77
            ).to(self.device)
            
            with torch.no_grad():
                embeddings = self.clip_model.get_text_features(**inputs)
            
            return embeddings.cpu().numpy().tolist()
            
        except Exception as e:
            logger.error(f"Error generating embeddings: {e}")
            raise AppException(f"Embedding generation failed: {str(e)}")
    
    def create_collection(self, collection_name: str, metadata: Optional[Dict] = None) -> chromadb.Collection:
        """Create a new collection"""
        if not self.initialized:
            self.initialize()
        
        try:
            collection = self.client.get_or_create_collection(
                name=collection_name,
                metadata=metadata or {}
            )
            logger.info(f"Collection '{collection_name}' created/retrieved")
            return collection
            
        except Exception as e:
            logger.error(f"Error creating collection: {e}")
            raise AppException(f"Collection creation failed: {str(e)}")
    
    def add_documents(
        self,
        collection_name: str,
        documents: List[str],
        metadatas: Optional[List[Dict]] = None,
        ids: Optional[List[str]] = None
    ):
        """Add documents to collection with embeddings"""
        if not self.initialized:
            self.initialize()
        
        try:
            collection = self.client.get_collection(name=collection_name)
            
            # Generate embeddings
            embeddings = self.get_text_embedding(documents)
            
            # Generate IDs if not provided
            if ids is None:
                ids = [f"doc_{i}" for i in range(len(documents))]
            
            # Add to collection in batches
            batch_size = 100
            for i in range(0, len(documents), batch_size):
                end_idx = min(i + batch_size, len(documents))
                
                collection.add(
                    documents=documents[i:end_idx],
                    embeddings=embeddings[i:end_idx],
                    metadatas=metadatas[i:end_idx] if metadatas else None,
                    ids=ids[i:end_idx]
                )
            
            logger.info(f"Added {len(documents)} documents to '{collection_name}'")
            
        except Exception as e:
            logger.error(f"Error adding documents: {e}")
            raise AppException(f"Failed to add documents: {str(e)}")
    
    def query_documents(
        self,
        collection_name: str,
        query_texts: List[str],
        n_results: int = 5,
        where: Optional[Dict] = None
    ) -> Dict:
        """Query documents from collection"""
        if not self.initialized:
            self.initialize()
        
        try:
            collection = self.client.get_collection(name=collection_name)
            
            # Generate query embeddings
            query_embeddings = self.get_text_embedding(query_texts)
            
            # Query collection
            results = collection.query(
                query_embeddings=query_embeddings,
                n_results=n_results,
                where=where
            )
            
            return results
            
        except Exception as e:
            logger.error(f"Error querying documents: {e}")
            raise AppException(f"Document query failed: {str(e)}")
    
    def delete_collection(self, collection_name: str):
        """Delete a collection"""
        if not self.initialized:
            self.initialize()
        
        try:
            self.client.delete_collection(name=collection_name)
            logger.info(f"Collection '{collection_name}' deleted")
            
        except Exception as e:
            logger.error(f"Error deleting collection: {e}")
            raise AppException(f"Collection deletion failed: {str(e)}")
    
    def get_collection_info(self, collection_name: str) -> Dict:
        """Get collection information"""
        if not self.initialized:
            self.initialize()
        
        try:
            collection = self.client.get_collection(name=collection_name)
            return {
                "name": collection.name,
                "count": collection.count(),
                "metadata": collection.metadata
            }
            
        except Exception as e:
            logger.error(f"Error getting collection info: {e}")
            return None


# Singleton instance
vector_service = VectorService()


def initialize_vector_db():
    """Initialize vector database on startup"""
    vector_service.initialize()
