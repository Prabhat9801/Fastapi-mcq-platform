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
import random

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
        Enhanced with better page filtering and content validation
        """
        try:
            reader = PdfReader(pdf_path)
            text = ""
            extracted_pages = []
            
            # Handle None, empty string, or invalid input
            if not pages or pages.strip() == "" or pages.strip().lower() == "string":
                pages = None
            
            if pages is None:
                # Extract all pages
                for i, page in enumerate(reader.pages):
                    page_text = page.extract_text() or ""
                    text += f"\n--- Page {i+1} ---\n{page_text}"
                    extracted_pages.append(i+1)
            else:
                # Parse page specification
                try:
                    page_numbers = set()
                    page_ranges = pages.split(',')
                    
                    for page_range in page_ranges:
                        page_range = page_range.strip()
                        if '-' in page_range:
                            start, end = map(int, page_range.split('-'))
                            # Ensure we don't exceed available pages
                            end = min(end, len(reader.pages))
                            page_numbers.update(range(start - 1, end))
                        else:
                            page_num = int(page_range) - 1
                            if page_num < len(reader.pages):
                                page_numbers.add(page_num)
                    
                    # Extract specified pages with clear markers
                    for page_num in sorted(page_numbers):
                        if 0 <= page_num < len(reader.pages):
                            page_text = reader.pages[page_num].extract_text() or ""
                            text += f"\n--- Page {page_num+1} ---\n{page_text}"
                            extracted_pages.append(page_num+1)
                            
                except ValueError as e:
                    logger.warning(f"Invalid page specification '{pages}', using first 50 pages")
                    # Fall back to first 50 pages
                    max_pages = min(50, len(reader.pages))
                    for i in range(max_pages):
                        page_text = reader.pages[i].extract_text() or ""
                        text += f"\n--- Page {i+1} ---\n{page_text}"
                        extracted_pages.append(i+1)
            
            if not text.strip():
                raise AppException("No text could be extracted from PDF")
            
            logger.info(f"Extracted {len(text)} characters from PDF pages: {extracted_pages}")
            
            # Filter content to ensure it's relevant to the specified range
            if pages and "1-50" in pages:
                # Additional validation for chapter 1 content (pages 1-50)
                text = self._filter_chapter_content(text, chapter=1)
            
            return text
            
        except Exception as e:
            logger.error(f"Error extracting text from PDF: {e}")
            raise AppException(f"Failed to extract PDF text: {str(e)}")
    
    def _filter_chapter_content(self, text: str, chapter: int) -> str:
        """
        Filter content to ensure it's from the specified chapter only
        Enhanced with Hindi language support
        """
        try:
            # Look for chapter markers and keywords (English and Hindi)
            chapter_keywords = {
                1: {
                    "english": ["electric charges", "electric field", "coulomb's law", "gauss", "electrostatic", "matrices", "determinant", "inverse", "transpose", "derivative", "differentiation"],
                    "hindi": ["विद्युत आवेश", "विद्युत क्षेत्र", "कूलॉम", "गौस", "स्थिर विद्युत", "आवेश", "विद्युतीय", "मैट्रिक्स", "सारणिक", "अवकलन"]
                },
                2: {
                    "english": ["electrostatic potential", "potential energy", "equipotential", "conductor", "integration", "integral", "antiderivative", "calculus"],
                    "hindi": ["विद्युत विभव", "विभव ऊर्जा", "समविभव", "चालक", "संधारित्र", "समाकलन", "कैलकुलस"]
                },
                3: {
                    "english": ["current electricity", "ohm's law", "resistance", "kirchhoff", "trigonometry", "functions", "limits"],
                    "hindi": ["धारा", "ओम नियम", "प्रतिरोध", "किर्चहॉफ", "विद्युत धारा", "त्रिकोणमिति", "फलन"]
                },
                # Add more chapters as needed
            }
            
            if chapter in chapter_keywords:
                keywords_dict = chapter_keywords[chapter]
                english_keywords = keywords_dict["english"]
                hindi_keywords = keywords_dict["hindi"]
                
                # Split text into sections and filter by relevance
                sections = text.split("--- Page")
                filtered_sections = []
                
                for section in sections:
                    if not section.strip():
                        continue
                        
                    # Check if section contains chapter-relevant keywords (English or Hindi)
                    section_lower = section.lower()
                    english_count = sum(1 for keyword in english_keywords if keyword in section_lower)
                    hindi_count = sum(1 for keyword in hindi_keywords if keyword in section)
                    keyword_count = english_count + hindi_count
                    
                    # Include section if it has relevant keywords OR is from early pages (likely chapter 1)
                    page_match = False
                    if "---" in section:
                        try:
                            page_num = int(section.split("---")[0].strip())
                            page_match = page_num <= 50  # Assuming chapter 1 is in first 50 pages
                        except:
                            page_match = True
                    
                    if keyword_count > 0 or page_match:
                        filtered_sections.append("--- Page" + section if not section.startswith(" ") else section)
                
                if filtered_sections:
                    filtered_text = "".join(filtered_sections)
                    logger.info(f"Filtered content to {len(filtered_text)} characters for chapter {chapter}")
                    return filtered_text
            
            return text  # Return original if no filtering applied
            
        except Exception as e:
            logger.warning(f"Error filtering chapter content: {e}")
            return text
    
    def chunk_text(self, text: str, chunk_size: int = 100, overlap: int = 20) -> List[str]:
        """
        Intelligently chunk text by sentences and words with overlap
        Enhanced to preserve context and create more meaningful chunks
        
        Args:
            text: Input text
            chunk_size: Words per chunk (increased for better context)
            overlap: Overlapping words between chunks
        
        Returns:
            List of text chunks with preserved context
        """
        try:
            # First, try to split by sentences for better context preservation
            import re
            sentences = re.split(r'[.!?]+', text)
            
            # If sentences are too long, fall back to word-based chunking
            words = text.split()
            chunks = []
            
            # Create overlapping chunks with better context
            for i in range(0, len(words), chunk_size - overlap):
                chunk_words = words[i:i + chunk_size]
                
                # Try to end chunks at sentence boundaries when possible
                chunk_text = " ".join(chunk_words)
                
                # Add page markers if present for context
                if "--- Page" in chunk_text:
                    # Keep page markers for context
                    pass
                
                if chunk_text.strip():
                    # Clean up the chunk
                    chunk_text = chunk_text.strip()
                    
                    # Ensure chunks have meaningful content
                    if len(chunk_text.split()) >= 10:  # At least 10 words
                        chunks.append(chunk_text)
            
            logger.info(f"Created {len(chunks)} enhanced chunks from text")
            return chunks
            
        except Exception as e:
            logger.warning(f"Error in enhanced chunking, falling back to simple method: {e}")
            
            # Fallback to simple word chunking
            words = text.split()
            chunks = []
            
            for i in range(0, len(words), chunk_size - overlap):
                chunk = " ".join(words[i:i + chunk_size])
                if chunk.strip():
                    chunks.append(chunk)
            
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
    
    def detect_language(self, text: str) -> str:
        """
        Detect the primary language of the text content
        
        Args:
            text: Input text to analyze
            
        Returns:
            Language code ('hi' for Hindi, 'en' for English, etc.)
        """
        try:
            # Check for Devanagari script (Hindi)
            hindi_chars = sum(1 for char in text if '\u0900' <= char <= '\u097F')
            total_chars = len([char for char in text if char.isalpha()])
            
            if total_chars > 0:
                hindi_ratio = hindi_chars / total_chars
                
                # If more than 30% Hindi characters, consider it Hindi
                if hindi_ratio > 0.3:
                    logger.info(f"Detected Hindi content ({hindi_ratio:.2%} Devanagari characters)")
                    return 'hi'
                else:
                    logger.info(f"Detected English content ({hindi_ratio:.2%} Devanagari characters)")
                    return 'en'
            
            return 'en'  # Default to English
            
        except Exception as e:
            logger.warning(f"Error detecting language: {e}")
            return 'en'
    
    def _detect_subject_type(self, text: str) -> str:
        """
        Detect the subject type from content
        
        Args:
            text: Input text to analyze
            
        Returns:
            Subject type ('mathematics', 'physics', 'chemistry', etc.)
        """
        try:
            text_lower = text.lower()
            
            # Mathematics keywords
            math_keywords = [
                'calculus', 'derivative', 'integral', 'matrix', 'algebra', 'geometry',
                'trigonometry', 'logarithm', 'differential', 'integration', 'limit',
                'गणित', 'कैलकुलस', 'अवकलन', 'समाकलन', 'मैट्रिक्स', 'बीजगणित'
            ]
            
            # Physics keywords
            physics_keywords = [
                'electric', 'magnetic', 'force', 'energy', 'momentum', 'charge',
                'विद्युत', 'चुम्बकीय', 'बल', 'ऊर्जा', 'आवेश'
            ]
            
            # Chemistry keywords
            chemistry_keywords = [
                'chemical', 'reaction', 'molecule', 'atom', 'bond', 'acid', 'base',
                'रसायन', 'अभिक्रिया', 'अणु', 'परमाणु'
            ]
            
            math_count = sum(1 for keyword in math_keywords if keyword in text_lower)
            physics_count = sum(1 for keyword in physics_keywords if keyword in text_lower)
            chemistry_count = sum(1 for keyword in chemistry_keywords if keyword in text_lower)
            
            if math_count > physics_count and math_count > chemistry_count:
                logger.info(f"Detected Mathematics content (score: {math_count})")
                return 'mathematics'
            elif physics_count > chemistry_count:
                logger.info(f"Detected Physics content (score: {physics_count})")
                return 'physics'
            elif chemistry_count > 0:
                logger.info(f"Detected Chemistry content (score: {chemistry_count})")
                return 'chemistry'
            else:
                logger.info("Could not detect specific subject, defaulting to general")
                return 'general'
                
        except Exception as e:
            logger.warning(f"Error detecting subject type: {e}")
            return 'general'
    
    def _randomize_answer_positions(self, mcqs: List[Dict]) -> List[Dict]:
        """
        Post-process MCQs to randomize answer positions
        Ensures correct answers are distributed across all option positions
        """
        try:
            randomized_mcqs = []
            
            for mcq in mcqs:
                options = mcq["options"].copy()
                correct_index = mcq["correct_answer_index"]
                
                # Get the correct answer
                correct_answer = options[correct_index]
                
                # Generate a new random position for correct answer (0-3)
                new_correct_index = random.randint(0, 3)
                
                # If the new position is different, swap the answers
                if new_correct_index != correct_index:
                    # Swap correct answer to new position
                    options[correct_index], options[new_correct_index] = options[new_correct_index], options[correct_index]
                
                randomized_mcqs.append({
                    "question": mcq["question"],
                    "options": options,
                    "correct_answer_index": new_correct_index
                })
            
            logger.info(f"Randomized answer positions for {len(mcqs)} questions")
            return randomized_mcqs
            
        except Exception as e:
            logger.warning(f"Error randomizing answers, returning original: {e}")
            return mcqs
    
    def generate_mcqs(
        self,
        context: str,
        query_scope: str,
        num_questions: int = 10,
        difficulty_level: str = "medium"
    ) -> List[Dict]:
        """
        Generate MCQs from context using Gemini
        Enhanced with multi-language support (Hindi/English)
        
        Args:
            context: Source text for questions
            query_scope: Topic focus for questions
            num_questions: Number of questions to generate
            difficulty_level: easy, medium, or hard
        
        Returns:
            List of MCQ dictionaries
        """
        try:
            # Detect language from context
            detected_language = self.detect_language(context)
            logger.info(f"Detected language: {detected_language}")
            
            # Detect subject type from context
            subject_type = self._detect_subject_type(context)
            logger.info(f"Detected subject: {subject_type}")
            
            # Create language and subject-specific prompts
            if detected_language == 'hi':
                # Hindi prompt with subject awareness
                system_message = "आप एक पेशेवर प्रश्न निर्माता हैं जो हिंदी में व्यापक MCQ प्रश्न बनाते हैं।"
                if subject_type == 'mathematics':
                    system_message += " आप गणित के विषय में विशेषज्ञ हैं।"
                
                prompt = ChatPromptTemplate.from_messages([
                    ("system", system_message),
                    ("human", """निम्नलिखित संदर्भ के आधार पर, {num_questions} बहुविकल्पीय प्रश्न (MCQs) JSON प्रारूप में बनाएं।
विषय पर फोकस करें: {query_scope}
कठिनाई स्तर: {difficulty_level}

संदर्भ:
{context}

प्रश्न निर्माण की आवश्यकताएं:

1. प्रश्न के प्रकार:
   - क्या प्रश्न: "क्या है...?", "क्या होता है जब...?", "की विशेषताएं क्या हैं...?"
   - कैसे प्रश्न: "कैसे काम करता है...?", "कैसे गणना की जाती है...?", "कैसे निर्धारित किया जा सकता है...?"
   - कहाँ प्रश्न: "कहाँ पाया जाता है...?", "कहाँ होता है...?", "कहाँ लागू होता है...?"
   - क्यों प्रश्न: "क्यों होता है...?", "क्यों महत्वपूर्ण है...?", "क्यों उपयोग किया जाता है...?"
   - कब प्रश्न: "कब होता है...?", "कब लागू होता है...?", "कब उपयोग करना चाहिए...?"

2. प्रश्न प्रारूप:
   क) प्रत्यक्ष प्रश्न (स्वतंत्र):
      उदाहरण: "विद्युत आवेश की इकाई क्या है?"
   
   ख) संदर्भ आधारित प्रश्न (संबंधित पाठ अंश सहित):
      उदाहरण: "दी गई जानकारी के अनुसार: 'विद्युत आवेश क्वांटीकृत है और प्राथमिक आवेश 1.6 × 10⁻¹⁹ कूलॉम है।' प्राथमिक आवेश का परिमाण क्या है?"
   
   ग) स्थिति आधारित प्रश्न:
      उदाहरण: "यदि +2μC और -3μC के दो बिंदु आवेश 10cm की दूरी पर रखे गए हैं, तो उनके बीच बल की प्रकृति क्या है?"

3. प्रारूपण नियम:
   - प्रत्येक प्रश्न में बिल्कुल 4 विकल्प होने चाहिए
   - सही उत्तर सूचकांक प्रदान करें (0-3)
   - संदर्भ आधारित प्रश्नों के लिए, संबंधित पाठ अंश प्रश्न में शामिल करें
   - विकल्पों को प्रशंसनीय और प्रासंगिक बनाएं
   - सुनिश्चित करें कि प्रश्न {query_scope} की समझ का परीक्षण करते हैं

आउटपुट प्रारूप:
[
  {{
    "question": "प्रत्यक्ष प्रश्न या संदर्भ आधारित प्रश्न पाठ अंश के साथ",
    "options": ["विकल्प A", "विकल्प B", "विकल्प C", "विकल्प D"],
    "correct_answer_index": 0
  }}
]

अच्छे प्रश्नों के उदाहरण:

प्रत्यक्ष प्रश्न:
{{
  "question": "कूलॉम नियतांक की SI इकाई में क्या है?",
  "options": ["9 × 10⁹ N⋅m²/C²", "8.85 × 10⁻¹² F/m", "1.6 × 10⁻¹⁹ C", "6.02 × 10²³ mol⁻¹"],
  "correct_answer_index": 0
}}

संदर्भ आधारित प्रश्न:
{{
  "question": "दिए गए पाठ के अनुसार: 'विद्युत क्षेत्र को प्रति इकाई धनात्मक आवेश के बल के रूप में परिभाषित किया जाता है।' विद्युत क्षेत्र की SI इकाई क्या है?",
  "options": ["न्यूटन प्रति कूलॉम (N/C)", "कूलॉम प्रति न्यूटन (C/N)", "जूल प्रति कूलॉम (J/C)", "कूलॉम प्रति मीटर (C/m)"],
  "correct_answer_index": 0
}}

अब {num_questions} हिंदी प्रश्न बनाएं, प्रत्यक्ष, संदर्भ आधारित, और स्थिति आधारित प्रश्नों को मिलाकर:""")
                ])
            else:
                # English prompt with subject awareness
                system_message = "You are a professional quiz generator who creates comprehensive MCQ questions in English."
                if subject_type == 'mathematics':
                    system_message += " You are an expert in mathematics and ensure mathematical accuracy."
                
                prompt = ChatPromptTemplate.from_messages([
                    ("system", system_message),
                    ("human", """Based on the following context, generate {num_questions} multiple-choice questions (MCQs) in JSON format.
Focus on the topic: {query_scope}
Difficulty level: {difficulty_level}

Context:
{context}

QUESTION GENERATION REQUIREMENTS:

CRITICAL MATHEMATICS RULES (if mathematics content):
- Use proper mathematical notation: fractions as a/b, exponents as x^2, etc.
- Ensure mathematical accuracy in all calculations
- Avoid complex Unicode symbols - use standard ASCII math notation
- For matrices, use simple notation like [[1,2],[3,4]] instead of special brackets
- NEVER ask about exam instructions, question paper format, or administrative details
- FOCUS ONLY on mathematical concepts, formulas, calculations, and problem-solving

GENERAL REQUIREMENTS:

1. QUESTION TYPES TO CREATE:
   - What questions: "What is...?", "What happens when...?", "What are the characteristics of...?"
   - How questions: "How does...work?", "How is...calculated?", "How can...be determined?"
   - Where questions: "Where is...found?", "Where does...occur?", "Where is...applied?"
   - Why questions: "Why does...happen?", "Why is...important?", "Why is...used?"
   - When questions: "When does...occur?", "When is...applied?", "When should...be used?"

2. QUESTION FORMATS:
   a) DIRECT QUESTIONS (standalone): 
      Example: "What is the unit of electric charge?"
   
   b) CONTEXT-BASED QUESTIONS (include relevant text excerpt):
      Example: "According to the given information: 'Electric charge is quantized and the elementary charge is 1.6 × 10⁻¹⁹ coulombs.' What is the magnitude of elementary charge?"
   
   c) CONDITION-BASED QUESTIONS:
      Example: "If two point charges of +2μC and -3μC are placed 10cm apart, what is the nature of force between them?"

3. FORMATTING RULES:
   - Each question must have exactly 4 options
   - Provide correct answer index (0-3)
   - For context-based questions, include the relevant text excerpt in the question
   - Make options plausible and relevant
   - Ensure questions test understanding of {query_scope}

OUTPUT FORMAT:
[
  {{
    "question": "Direct question or context-based question with text excerpt included",
    "options": ["Option A", "Option B", "Option C", "Option D"],
    "correct_answer_index": 0
  }}
]

MATHEMATICS QUESTION EXAMPLES:

DIRECT MATHEMATICS QUESTION:
{{
  "question": "What is the derivative of sin(x) with respect to x?",
  "options": ["cos(x)", "-cos(x)", "sin(x)", "-sin(x)"],
  "correct_answer_index": 0
}}

CALCULATION-BASED QUESTION:
{{
  "question": "If A = [[2, 1], [0, 3]], what is the determinant of matrix A?",
  "options": ["5", "6", "7", "8"],
  "correct_answer_index": 1
}}

CONTEXT-BASED MATHEMATICS QUESTION:
{{
  "question": "According to the given formula: 'The derivative of x^n is nx^(n-1).' What is the derivative of x^3?",
  "options": ["3x^2", "x^2", "3x^3", "x^3"],
  "correct_answer_index": 0
}}

Generate {num_questions} English questions now, focusing on mathematical concepts and avoiding administrative content:""")
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
            
            # Apply post-processing randomization to fix answer bias
            mcqs = self._randomize_answer_positions(mcqs)
            
            logger.info(f"Generated {len(mcqs)} MCQs with randomized answer positions")
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
        chunk_size: int = 100,  # Increased for better context
        overlap: int = 20,      # Increased for better overlap
        retrieval_chunks: int = 5  # Increased for more context
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
            
            # Step 5: Retrieve relevant chunks with enhanced strategy
            logger.info("Step 5: Retrieving relevant context with enhanced search")
            
            # Detect language and create appropriate search query
            detected_language = self.detect_language(text)
            
            # Detect subject type for better search queries
            subject_type = self._detect_subject_type(text)
            
            # Create more specific query based on topic scope, pages, language, and subject
            search_query = topic_scope
            if subject_type == "mathematics":
                if detected_language == 'hi':
                    search_query = "गणित कैलकुलस बीजगणित ज्यामिति अवकलन समाकलन मैट्रिक्स"
                else:
                    search_query = "mathematics calculus algebra geometry derivatives integrals matrix"
            elif specific_pages and "1-50" in specific_pages:
                if detected_language == 'hi':
                    search_query = "विद्युत आवेश विद्युत क्षेत्र कूलॉम नियम गौस प्रमेय स्थिर विद्युत"
                else:
                    search_query = "electric charges electric fields coulomb law gauss theorem electrostatics"
            elif topic_scope == "comprehensive":
                if detected_language == 'hi':
                    search_query = "विद्युत आवेश क्षेत्र स्थिर विद्युत विभव ऊर्जा"
                else:
                    search_query = "electric charges fields electrostatic potential energy"
            
            # Retrieve more chunks for better context (increased from default)
            enhanced_retrieval_chunks = max(retrieval_chunks, 5)  # At least 5 chunks
            
            context_chunks = self.retrieve_relevant_chunks(
                collection_name,
                search_query,
                n_results=enhanced_retrieval_chunks
            )
            
            if not context_chunks:
                # Fallback: try broader search based on detected language
                logger.warning("No chunks found with specific query, trying broader search")
                fallback_query = "भौतिकी विद्युत" if detected_language == 'hi' else "physics electric"
                context_chunks = self.retrieve_relevant_chunks(
                    collection_name,
                    fallback_query,
                    n_results=enhanced_retrieval_chunks
                )
            
            if not context_chunks:
                raise AppException("No relevant context found even with broader search")
            
            # Combine chunks with clear separators for better context
            context_text = "\n\n--- CONTEXT SECTION ---\n".join(context_chunks)
            
            logger.info(f"Using {len(context_chunks)} chunks with {len(context_text)} characters of context")
            
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
