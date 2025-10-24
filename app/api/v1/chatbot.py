"""RAG-based chatbot endpoints"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
import logging

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.chat import ChatSession, ChatMessage
from app.services.rag_chatbot import rag_chatbot

logger = logging.getLogger(__name__)

router = APIRouter()


class MessageCreate(BaseModel):
    message: str


class MessageResponse(BaseModel):
    id: int
    session_id: int
    sender: str  # 'user' or 'bot'
    message: str
    timestamp: datetime
    
    class Config:
        from_attributes = True


class SessionResponse(BaseModel):
    id: int
    user_id: int
    title: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


@router.post("/sessions", response_model=SessionResponse)
async def create_session(
    current_user: User = Depends(get_current_user), 
    db: Session = Depends(get_db)
):
    """Create a new chat session"""
    session = ChatSession(
        user_id=current_user.id,
        title=f"Chat {datetime.utcnow().strftime('%Y-%m-%d %H:%M')}"
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


@router.get("/sessions", response_model=List[SessionResponse])
async def get_sessions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all chat sessions for current user"""
    sessions = db.query(ChatSession).filter(
        ChatSession.user_id == current_user.id
    ).order_by(ChatSession.updated_at.desc()).all()
    return sessions


@router.get("/sessions/{session_id}/messages", response_model=List[MessageResponse])
async def get_messages(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all messages in a chat session"""
    # Verify session belongs to user
    session = db.query(ChatSession).filter(
        ChatSession.id == session_id,
        ChatSession.user_id == current_user.id
    ).first()
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    messages = db.query(ChatMessage).filter(
        ChatMessage.session_id == session_id
    ).order_by(ChatMessage.timestamp.asc()).all()
    
    return messages


@router.post("/sessions/{session_id}/messages", response_model=MessageResponse)
async def send_message(
    session_id: int,
    message_data: MessageCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Send a message in a chat session"""
    # Verify session belongs to user
    session = db.query(ChatSession).filter(
        ChatSession.id == session_id,
        ChatSession.user_id == current_user.id
    ).first()
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Save user message
    user_message = ChatMessage(
        session_id=session_id,
        sender="user",
        message=message_data.message
    )
    db.add(user_message)
    db.commit()
    db.refresh(user_message)
    
    # Get conversation history for context
    conversation_history = db.query(ChatMessage).filter(
        ChatMessage.session_id == session_id
    ).order_by(ChatMessage.timestamp.desc()).limit(10).all()
    
    # Convert to format expected by RAG chatbot
    context_messages = []
    for msg in reversed(conversation_history):  # Reverse to get chronological order
        context_messages.append({
            'sender': msg.sender,
            'message': msg.message
        })
    
    # Generate intelligent response using RAG chatbot
    logger.info(f"Generating response for: {message_data.message[:100]}...")
    bot_response_text = rag_chatbot.generate_response(
        question=message_data.message,
        conversation_context=context_messages
    )
    
    bot_message = ChatMessage(
        session_id=session_id,
        sender="bot",
        message=bot_response_text
    )
    db.add(bot_message)
    
    # Update session timestamp
    session.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(bot_message)
    
    return bot_message


@router.delete("/sessions/{session_id}")
async def delete_session(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a chat session"""
    session = db.query(ChatSession).filter(
        ChatSession.id == session_id,
        ChatSession.user_id == current_user.id
    ).first()
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Delete all messages in session
    db.query(ChatMessage).filter(ChatMessage.session_id == session_id).delete()
    
    # Delete session
    db.delete(session)
    db.commit()
    
    return {"message": "Session deleted successfully"}


@router.post("/ask")
async def ask_chatbot(
    question: str, 
    current_user: User = Depends(get_current_user), 
    db: Session = Depends(get_db)
):
    """Simple question endpoint (legacy, use sessions instead)"""
    logger.info(f"Legacy ask endpoint used for: {question[:100]}...")
    
    # Generate response using RAG chatbot (no conversation context for legacy endpoint)
    answer = rag_chatbot.generate_response(question=question)
    
    return {
        "question": question,
        "answer": answer
    }


@router.get("/rag/status")
async def get_rag_status(
    current_user: User = Depends(get_current_user)
):
    """Get RAG system status and available document collections"""
    try:
        collections = rag_chatbot.get_available_collections()
        
        return {
            "rag_enabled": True,
            "available_collections": collections,
            "total_documents": len(collections),
            "capabilities": [
                "General AI knowledge (powered by Gemini 2.0 Flash)",
                "Document-based Q&A using RAG",
                "Automatic query routing (RAG vs general)",
                "Conversation context awareness",
                "CLIP embeddings for semantic search"
            ],
            "message": "RAG system is operational and ready to answer questions!"
        }
    except Exception as e:
        logger.error(f"Error getting RAG status: {e}")
        return {
            "rag_enabled": False,
            "error": str(e),
            "message": "RAG system is experiencing issues"
        }
