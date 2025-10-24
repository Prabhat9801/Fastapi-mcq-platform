"""
Smart MCQ Generation Service using Google Gemini and RAG
Supports images, tables, and intelligent question generation
"""

from typing import List, Dict, Optional
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
import json
import logging
import random

from app.core.config import settings
from app.core.exceptions import AppException
from app.services.vector_service import vector_service

logger = logging.getLogger(__name__)


class MCQGenerator:
    """Intelligent MCQ generation using LLM and RAG"""
    
    def __init__(self):
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash-exp",
            temperature=0.3,
            google_api_key=settings.GOOGLE_API_KEY
        )
        self.parser = JsonOutputParser()
    
    def generate_mcqs(
        self,
        context: str,
        num_questions: int = 10,
        difficulty_level: str = "medium",
        topic_scope: str = "comprehensive",
        question_types: Optional[List[str]] = None,
        include_images: bool = False,
        image_contexts: Optional[List[Dict]] = None
    ) -> List[Dict]:
        """
        Generate MCQs from context with advanced options
        
        Args:
            context: Source text for questions
            num_questions: Number of questions to generate
            difficulty_level: easy, medium, hard
            topic_scope: Specific topic focus or "comprehensive"
            question_types: List of question types to include
            include_images: Whether to include image-based questions
            image_contexts: List of extracted images with OCR text
        
        Returns:
            List of question dictionaries
        """
        try:
            # Prepare difficulty-specific instructions
            difficulty_instructions = {
                "easy": "Focus on factual recall and basic understanding. Use straightforward language.",
                "medium": "Include conceptual questions requiring understanding and application. Mix factual and analytical questions.",
                "hard": "Focus on analysis, evaluation, and complex problem-solving. Include scenario-based questions."
            }
            
            # Build the prompt
            prompt_template = ChatPromptTemplate.from_messages([
                ("system", self._get_system_prompt(difficulty_level, difficulty_instructions)),
                ("human", self._get_human_prompt(
                    context, num_questions, difficulty_level, topic_scope,
                    include_images, image_contexts
                ))
            ])
            
            # Generate questions
            chain = prompt_template | self.llm | self.parser
            
            logger.info(f"Generating {num_questions} {difficulty_level} MCQs...")
            
            response = chain.invoke({
                "context": context[:15000],  # Limit context size
                "num_questions": num_questions,
                "difficulty": difficulty_level,
                "topic_scope": topic_scope
            })
            
            # Validate and post-process questions
            questions = self._validate_and_enhance_questions(response)
            
            logger.info(f"Successfully generated {len(questions)} questions")
            
            return questions
            
        except Exception as e:
            logger.error(f"Error generating MCQs: {e}")
            raise AppException(f"MCQ generation failed: {str(e)}")
    
    def _get_system_prompt(self, difficulty_level: str, difficulty_instructions: Dict) -> str:
        """Get system prompt for LLM"""
        return f"""You are an expert educational content creator specializing in creating high-quality multiple-choice questions (MCQs).

Your task is to generate well-crafted MCQs that:
1. Test genuine understanding, not just memorization
2. Have clear, unambiguous questions
3. Include plausible distractors (wrong options)
4. Provide detailed explanations for correct answers
5. Follow the specified difficulty level

Difficulty Level: {difficulty_level}
{difficulty_instructions.get(difficulty_level, '')}

Output Format (JSON array):
[
  {{
    "question": "Clear question text",
    "options": ["Option A", "Option B", "Option C", "Option D"],
    "correct_answer_index": 0,
    "correct_answer": "Option A",
    "explanation": "Detailed explanation of why this is correct",
    "difficulty_level": "{difficulty_level}",
    "topic_tags": ["Topic 1", "Topic 2"],
    "marks": 1,
    "question_type": "single_choice"
  }}
]

IMPORTANT:
- Generate exactly the requested number of questions
- Ensure all 4 options are unique and plausible
- Correct answer index must be 0, 1, 2, or 3
- Explanation should be educational and detailed
- Topic tags should be specific and relevant
"""
    
    def _get_human_prompt(
        self,
        context: str,
        num_questions: int,
        difficulty_level: str,
        topic_scope: str,
        include_images: bool,
        image_contexts: Optional[List[Dict]]
    ) -> str:
        """Get human prompt with context"""
        
        base_prompt = f"""Based on the following context, generate {num_questions} high-quality MCQs.

Context:
{context}

Requirements:
- Number of questions: {num_questions}
- Difficulty level: {difficulty_level}
- Topic focus: {topic_scope}
- Ensure questions test understanding, not just recall
- Distribute questions across different topics in the context
- Make distractors plausible but clearly incorrect
"""
        
        if include_images and image_contexts:
            image_info = "\n\nImage Context Available:\n"
            for img in image_contexts[:3]:  # Include up to 3 images
                image_info += f"- Image from page {img.get('page', 'N/A')}: {img.get('ocr_text', 'No text')[:200]}\n"
            base_prompt += image_info
        
        return base_prompt
    
    def _validate_and_enhance_questions(self, questions: List[Dict]) -> List[Dict]:
        """Validate and enhance generated questions"""
        validated = []
        
        for i, q in enumerate(questions):
            try:
                # Ensure required fields
                if not all(key in q for key in ['question', 'options', 'correct_answer_index']):
                    logger.warning(f"Question {i} missing required fields, skipping")
                    continue
                
                # Validate options
                if len(q['options']) != 4:
                    logger.warning(f"Question {i} doesn't have 4 options, skipping")
                    continue
                
                # Validate correct answer index
                if not (0 <= q['correct_answer_index'] < 4):
                    logger.warning(f"Question {i} has invalid correct_answer_index, skipping")
                    continue
                
                # Add missing fields with defaults
                q.setdefault('explanation', 'Correct answer selected.')
                q.setdefault('difficulty_level', 'medium')
                q.setdefault('topic_tags', [])
                q.setdefault('marks', 1)
                q.setdefault('question_type', 'single_choice')
                q.setdefault('question_number', i + 1)
                
                # Ensure correct_answer field exists
                q['correct_answer'] = q['options'][q['correct_answer_index']]
                
                validated.append(q)
                
            except Exception as e:
                logger.warning(f"Error validating question {i}: {e}")
                continue
        
        return validated
    
    def generate_from_document(
        self,
        collection_name: str,
        query_scope: str,
        num_questions: int = 10,
        difficulty_level: str = "medium",
        n_context_chunks: int = 5
    ) -> List[Dict]:
        """
        Generate MCQs from document stored in vector database
        
        Args:
            collection_name: ChromaDB collection name
            query_scope: Topic/query to focus on
            num_questions: Number of questions
            difficulty_level: Difficulty level
            n_context_chunks: Number of relevant chunks to retrieve
        
        Returns:
            List of generated questions
        """
        try:
            # Retrieve relevant context from vector database
            results = vector_service.query_documents(
                collection_name=collection_name,
                query_texts=[query_scope],
                n_results=n_context_chunks
            )
            
            # Combine retrieved documents
            if results and results['documents']:
                context = " ".join(results['documents'][0])
            else:
                raise AppException("No relevant context found in document")
            
            # Generate MCQs
            questions = self.generate_mcqs(
                context=context,
                num_questions=num_questions,
                difficulty_level=difficulty_level,
                topic_scope=query_scope
            )
            
            return questions
            
        except Exception as e:
            logger.error(f"Error generating MCQs from document: {e}")
            raise AppException(f"Document-based MCQ generation failed: {str(e)}")
    
    def regenerate_question(self, original_question: Dict, modification_request: str) -> Dict:
        """
        Regenerate a single question based on feedback
        """
        try:
            prompt = ChatPromptTemplate.from_messages([
                ("system", "You are an MCQ improvement expert. Modify the given question based on the user's request."),
                ("human", f"""Original Question:
{json.dumps(original_question, indent=2)}

Modification Request: {modification_request}

Generate an improved version in the same JSON format.""")
            ])
            
            chain = prompt | self.llm | self.parser
            improved = chain.invoke({})
            
            # Validate
            validated = self._validate_and_enhance_questions([improved])
            
            return validated[0] if validated else original_question
            
        except Exception as e:
            logger.error(f"Error regenerating question: {e}")
            return original_question


# Singleton instance
mcq_generator = MCQGenerator()
