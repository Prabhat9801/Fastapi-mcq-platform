# 🎯 Smart MCQ Platform

A comprehensive AI-powered Multiple Choice Question (MCQ) platform built with FastAPI, featuring intelligent question generation with **multi-language support** (Hindi/English), **subject-specific expertise** (Mathematics, Physics, Chemistry), user management, subscription handling, and advanced document processing capabilities.

## 📋 Table of Contents

- [Overview](#overview)
- [🆕 New Features](#-new-features)
- [Features](#features)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Installation & Setup](#installation--setup)
- [Configuration](#configuration)
- [Usage](#usage)
- [Language Support](#language-support)
- [API Documentation](#api-documentation)
- [Workflow Diagram](#workflow-diagram)
- [File & Folder Details](#file--folder-details)
- [Contributing](#contributing)
- [License](#license)

## 🌟 Overview

Smart MCQ Platform is an enterprise-grade examination system that leverages artificial intelligence to automatically generate high-quality multiple-choice questions from uploaded documents. The platform now features **advanced multi-language support**, **subject-specific AI models**, and **intelligent content processing** for both Hindi and English educational content.

### 🚀 Key Capabilities
- **🌐 Multi-Language AI**: Automatic language detection and native question generation in Hindi/English
- **🧮 Subject-Specific Expertise**: Specialized AI models for Mathematics, Physics, Chemistry with accurate calculations
- **🤖 Advanced AI Integration**: Google Gemini AI and LangChain for intelligent MCQ creation
- **📄 Smart Document Processing**: PDF, DOCX, images with OCR capabilities and page-specific filtering
- **🔍 Vector Search**: ChromaDB integration with CLIP embeddings for semantic similarity matching
- **👥 User Management**: Role-based access control with JWT authentication
- **💳 Subscription System**: Flexible subscription plans with payment integration
- **💬 Real-time Chat**: AI-powered multilingual chatbot for instant assistance
- **📊 Comprehensive Analytics**: Performance tracking and detailed reporting

## 🆕 New Features

### 🌐 Multi-Language Support
- **🇮🇳 Hindi Language**: Native Hindi question generation with proper Devanagari script support
- **🇬🇧 English Language**: Enhanced English question generation with improved accuracy
- **🔄 Automatic Detection**: Smart language detection based on document content
- **📚 Bilingual Keywords**: Subject-specific keyword matching in both languages

### 🧮 Mathematics Specialization
- **🔢 Mathematical Accuracy**: Specialized prompts ensuring correct calculations and formulas
- **📐 Clean Notation**: Standard ASCII mathematical notation (x^2, a/b, [[matrix]])
- **🧠 Expert AI**: Mathematics-specific system prompts for enhanced accuracy
- **🚫 No Admin Questions**: Filters out exam instructions, focuses only on mathematical concepts

### 📝 Enhanced Question Types
- **❓ What Questions**: "What is...", "What happens when...", "What are the characteristics..."
- **🔧 How Questions**: "How does...work?", "How is...calculated?", "How can...be determined?"
- **📍 Where Questions**: "Where is...found?", "Where does...occur?", "Where is...applied?"
- **🤔 Why Questions**: "Why does...happen?", "Why is...important?", "Why is...used?"
- **⏰ When Questions**: "When does...occur?", "When is...applied?", "When should...be used?"

### 🎯 Question Formats
1. **Direct Questions**: Standalone factual questions
2. **Context-Based Questions**: Include relevant text excerpts with proper attribution
3. **Condition-Based Questions**: Scenario-based problem-solving questions

## ✨ Features

### 🤖 AI & Machine Learning
- **🧠 Advanced Gemini AI Integration** with subject-specific expertise for natural language processing
- **🖼️ CLIP Model** for image and text embeddings with enhanced multilingual support
- **🗄️ Vector Database** with ChromaDB for semantic search and content retrieval
- **🎯 Intelligent Question Generation** with difficulty levels, topic scope, and language awareness
- **📱 OCR Support** with Tesseract for image-based documents and scanned content
- **🔍 Smart Content Filtering** with chapter-specific keyword matching

### 📚 Enhanced Document Processing
- **📄 Multi-format Support**: PDF, DOCX, images with intelligent content extraction
- **🧠 Language-Aware Processing**: Automatic detection and processing of Hindi/English content
- **📖 Page-specific Processing** for targeted question generation with chapter filtering
- **⚡ Fast Processing Pipeline** using CLIP + ChromaDB + Gemini for 3-5x speed improvement
- **🔧 Subject Detection**: Mathematics, Physics, Chemistry content identification
- **📊 Batch Processing** capabilities for multiple documents with progress tracking

### 👥 User Management & Security
- **🔐 Role-based Access Control** (Admin, Teacher, Student) with granular permissions
- **🎫 JWT Authentication** with secure token management and refresh tokens
- **👤 Comprehensive User Profiles** with detailed analytics and learning progress
- **📈 Activity Tracking** and performance monitoring with visual dashboards
- **🔒 Security Features** with input validation and SQL injection prevention

### 💳 Payment & Subscriptions
- **💰 Stripe Integration** for international payments with webhook support
- **🇮🇳 Razorpay Support** for Indian market with UPI and wallet support
- **📋 Flexible Subscription Plans** with feature limitations and usage tracking
- **📧 Automated Billing** and invoice generation with email notifications
- **💎 Freemium Model** with free and premium content differentiation

### 📊 Advanced Platform Features
- **💬 Multilingual Real-time Chat** with AI-powered responses in Hindi/English
- **📝 Advanced Test Management** with comprehensive settings and scheduling
- **📈 Performance Analytics** with detailed reporting and progress tracking
- **📧 Smart Notifications** via email with customizable templates
- **📱 SMS Integration** via Twilio for important alerts and notifications

## 🛠 Tech Stack

### Backend
- **FastAPI** (0.117.1) - Modern Python web framework
- **SQLAlchemy** (2.0.43) - ORM for database operations
- **Alembic** (1.17.0) - Database migrations
- **PostgreSQL/SQLite** - Database systems
- **Redis** - Caching and session management

### AI & ML
- **LangChain** (0.3.27) - LLM orchestration framework
- **Google Generative AI** (0.8.5) - Gemini AI integration
- **Transformers** (4.55.4) - Hugging Face transformers
- **PyTorch** (2.8.0) - Deep learning framework
- **ChromaDB** (1.0.20) - Vector database
- **Sentence Transformers** (5.1.1) - Text embeddings

### Document Processing
- **PyPDF2** (3.0.1) - PDF processing
- **PyMuPDF** (1.26.5) - Advanced PDF operations
- **Pytesseract** (0.3.13) - OCR capabilities
- **python-docx** (1.2.0) - Word document processing
- **Pillow** (11.3.0) - Image processing

### Payment & Integrations
- **Stripe** (13.0.1) - Payment processing
- **Razorpay** (2.0.0) - Indian payment gateway
- **Twilio** (9.8.3) - SMS services
- **FastAPI-Mail** (1.5.2) - Email services

## 📂 Project Structure

```
Fastapi-mcq-platform/
├── 📁 app/                          # Main application package
│   ├── 📁 api/                      # API layer
│   │   └── 📁 v1/                   # API version 1
│   │       ├── admin.py             # Admin management endpoints
│   │       ├── auth.py              # Authentication endpoints
│   │       ├── categories.py        # Category management
│   │       ├── chatbot.py           # Chatbot API endpoints
│   │       ├── subscriptions.py     # Subscription management
│   │       ├── tests.py             # Test management endpoints
│   │       └── users.py             # User management endpoints
│   ├── 📁 core/                     # Core application logic
│   │   ├── config.py                # Application configuration
│   │   ├── database.py              # Database connection & setup
│   │   ├── exceptions.py            # Custom exception classes
│   │   └── security.py              # Security utilities
│   ├── 📁 models/                   # Database models
│   │   ├── attempt.py               # Test attempt models
│   │   ├── category.py              # Category models
│   │   ├── chat.py                  # Chat models
│   │   ├── chatbot.py               # Chatbot models
│   │   ├── gamification.py          # Gamification models
│   │   ├── subscription.py          # Subscription models
│   │   ├── test.py                  # Test models
│   │   └── user.py                  # User models
│   └── 📁 services/                 # Business logic layer
│       ├── document_processor.py    # Document processing service
│       ├── fast_mcq_generator.py    # Fast MCQ generation
│       ├── mcq_generator.py         # Main MCQ generation
│       ├── rag_chatbot.py           # RAG-based chatbot
│       └── vector_service.py        # Vector database operations
├── 📁 models/                       # Pre-trained models
│   └── 📁 clip-vit-base-patch32/    # CLIP model files
├── 📁 myenv/                        # Virtual environment
├── 📁 monitoring/                   # Monitoring configurations
├── 📁 uploads/                      # File upload directory
├── main.py                          # Application entry point
├── requirements.txt                 # Python dependencies
├── .env                            # Environment variables
├── .env.example                    # Environment template
├── Procfile                        # Heroku deployment config
└── README.md                       # Project documentation
```

## 🚀 Quick Start with Docker

### 🐳 Using Pre-built Docker Image (Recommended)

The easiest way to get started is using the pre-built Docker image from Docker Hub:

```bash
# Pull the latest image from Docker Hub
docker pull prabhat9801/fastapi_mcq_platform

# Run the container
docker run -p 8000:8000 prabhat9801/fastapi_mcq_platform

# Access the application
# API Documentation: http://localhost:8000/api/docs
# Health Check: http://localhost:8000/health
```

### 🔧 Environment Variables for Docker

To customize the Docker deployment, you can pass environment variables:

```bash
docker run -p 8000:8000 \
  -e GOOGLE_API_KEY="your-google-api-key" \
  -e DATABASE_URL="sqlite:///./mcq_platform.db" \
  -e SECRET_KEY="your-secret-key" \
  prabhat9801/fastapi_mcq_platform
```

### 📦 Docker Hub Repository

- **Docker Hub**: [prabhat9801/fastapi_mcq_platform](https://hub.docker.com/r/prabhat9801/fastapi_mcq_platform)
- **GitHub Repository**: [Prabhat9801/Fastapi-mcq-platform](https://github.com/Prabhat9801/Fastapi-mcq-platform)

---

## ⚙️ Manual Installation & Setup

### Prerequisites
- Python 3.8 or higher
- PostgreSQL (optional, SQLite works for development)
- Redis (optional, for caching)
- Git

### Step 1: Clone the Repository
```bash
git clone https://github.com/Prabhat9801/Fastapi-mcq-platform.git
cd Fastapi-mcq-platform
```

### Step 2: Create Virtual Environment
```bash
# Windows
python -m venv myenv
myenv\Scripts\activate

# Linux/Mac
python -m venv myenv
source myenv/bin/activate
```

### Step 3: Install Dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### Step 4: Environment Configuration
```bash
# Copy environment template
cp .env.example .env

# Edit .env file with your configurations
# Key settings to configure:
# - GOOGLE_API_KEY: Your Google Gemini API key
# - DATABASE_URL: Your database connection string
# - SECRET_KEY: Generate a strong secret key
# - Payment gateway credentials (Stripe, Razorpay)
```

### Step 5: Database Setup
```bash
# For SQLite (default development setup)
# Database will be created automatically

# For PostgreSQL
# 1. Create database: mcq_platform
# 2. Update DATABASE_URL in .env
# 3. Run migrations
alembic upgrade head
```

### Step 6: Download Required Models
```bash
# Create models directory
mkdir models
cd models

# Clone CLIP model from Hugging Face
git clone https://huggingface.co/openai/clip-vit-base-patch32

# Go back to project root
cd ..
```

**Alternative Model Download Methods:**

**Option A: Using Hugging Face Hub (Recommended)**
```bash
# Install huggingface_hub if not already installed
pip install huggingface_hub

# Download model using Python
python -c "
from huggingface_hub import snapshot_download
snapshot_download(
    repo_id='openai/clip-vit-base-patch32',
    local_dir='./models/clip-vit-base-patch32',
    local_dir_use_symlinks=False
)
"
```

**Option B: Automatic Download (First Run)**
```bash
# The model will be downloaded automatically on first use
# Check app/services/vector_service.py for auto-download logic
```

## 🔧 Model Configuration

### CLIP Model Details
- **Model**: OpenAI CLIP ViT-B/32
- **Repository**: https://huggingface.co/openai/clip-vit-base-patch32
- **Size**: ~600MB
- **Purpose**: Text and image embeddings for vector search

### Environment Variables for Models
```env
# Model Configuration
CLIP_MODEL_PATH=./models/clip-vit-base-patch32
HUGGINGFACEHUB_API_TOKEN=your-huggingface-token  # Optional for private models
MODEL_CACHE_DIR=./models
```

### Troubleshooting Model Setup

**If model download fails:**
```bash
# Method 1: Direct download using wget/curl
wget -r --no-parent https://huggingface.co/openai/clip-vit-base-patch32/resolve/main/

# Method 2: Manual download
# Visit: https://huggingface.co/openai/clip-vit-base-patch32
# Download required files to ./models/clip-vit-base-patch32/
```

**Required model files:**
- `config.json`
- `pytorch_model.bin` or `model.safetensors`
- `tokenizer.json`
- `tokenizer_config.json`
- `vocab.json`
- `merges.txt`

### Step 7: Run the Application
```bash
# Development mode
python main.py

# Or using uvicorn directly
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

### Step 8: Access the Application
- **API Documentation**: http://localhost:8000/api/docs
- **ReDoc Documentation**: http://localhost:8000/api/redoc
- **Health Check**: http://localhost:8000/health

## 🔧 Configuration

### Environment Variables

#### Server Configuration
```env
APP_NAME="Smart MCQ Platform"
DEBUG=True
HOST=0.0.0.0
PORT=8000
```

#### Database Configuration
```env
# PostgreSQL (Production)
DATABASE_URL=postgresql://user:password@localhost:5432/mcq_platform

# SQLite (Development)
DATABASE_URL=sqlite:///./mcq_platform.db
```

#### Security Settings
```env
SECRET_KEY=your-secret-key-here-generate-a-strong-one
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=10080
```

#### AI Services
```env
GOOGLE_API_KEY="your-google-gemini-api-key"
HUGGINGFACEHUB_API_TOKEN="your-huggingface-token"
CLIP_MODEL_PATH=./models/clip-vit-base-patch32
```

#### File Upload Settings
```env
UPLOAD_DIR=./uploads
MAX_UPLOAD_SIZE=52428800  # 50MB
TESSERACT_CMD=C:/Program Files/Tesseract-OCR/tesseract.exe  # Windows
```

## 🚀 Usage

### Admin Panel Usage

#### 1. Create Admin User
```bash
python create_admin.py
```

#### 2. Generate MCQs from Documents
```python
# Using the API
POST /api/v1/admin/tests/generate-fast

# Form data:
{
    "file": "document.pdf",
    "test_series_id": 1,
    "test_name": "Chapter 1 Test",
    "num_questions": 10,
    "difficulty_level": "medium",
    "topic_scope": "comprehensive",
    "duration_minutes": 60,
    "specific_pages": "1-10"  # Optional
}
```

#### 3. User Management
```python
# Create user
POST /api/v1/users/register

# Get user details
GET /api/v1/users/{user_id}

# Update user role
PUT /api/v1/admin/users/{user_id}/role
```

### Student/User Usage

#### 1. Authentication
```python
# Register
POST /api/v1/auth/register

# Login
POST /api/v1/auth/login

# Response includes JWT token for subsequent requests
```

#### 2. Take Tests
```python
# Get available tests
GET /api/v1/tests/

# Start test attempt
POST /api/v1/tests/{test_id}/start

# Submit answers
POST /api/v1/tests/{test_id}/submit
```

#### 3. Chat with AI
```python
# Send message to chatbot
POST /api/v1/chat/message
{
    "message": "Explain photosynthesis",
    "context": "biology"
}
```

## 📖 API Documentation

### Authentication Endpoints
- `POST /api/v1/auth/register` - User registration
- `POST /api/v1/auth/login` - User login
- `POST /api/v1/auth/refresh` - Refresh JWT token
- `POST /api/v1/auth/logout` - User logout

### Admin Endpoints
- `POST /api/v1/admin/tests/generate` - Generate MCQs (slow, thorough)
- `POST /api/v1/admin/tests/generate-fast` - Generate MCQs (fast)
- `GET /api/v1/admin/users` - List all users
- `PUT /api/v1/admin/users/{user_id}/role` - Update user role
- `DELETE /api/v1/admin/tests/{test_id}` - Delete test

### Test Management
- `GET /api/v1/tests/` - List available tests
- `GET /api/v1/tests/{test_id}` - Get test details
- `POST /api/v1/tests/{test_id}/start` - Start test attempt
- `POST /api/v1/tests/{test_id}/submit` - Submit test answers
- `GET /api/v1/tests/{test_id}/results` - Get test results

### Chatbot Endpoints
- `POST /api/v1/chat/message` - Send message to AI chatbot
- `GET /api/v1/chat/history` - Get chat history
- `DELETE /api/v1/chat/history` - Clear chat history

### Subscription Management
- `GET /api/v1/subscriptions/plans` - List subscription plans
- `POST /api/v1/subscriptions/subscribe` - Subscribe to plan
- `GET /api/v1/subscriptions/status` - Check subscription status

## 🔄 Workflow Diagram

### MCQ Generation & Processing Flow

```mermaid
graph TB
    subgraph "Document Processing"
        A[📄 User Uploads Document] --> B[🔧 Document Processor]
        B --> C{📋 Document Type?}
        C -->|PDF| D[📖 PyPDF2/PyMuPDF<br/>Extraction]
        C -->|DOCX| E[📝 python-docx<br/>Extraction]
        C -->|Image| F[👁️ Tesseract OCR<br/>Processing]
    end
    
    subgraph "AI Processing Pipeline"
        D --> G[🧹 Text Preprocessing]
        E --> G
        F --> G
        G --> H[🎯 CLIP Embeddings<br/>Generation]
        H --> I[💾 ChromaDB<br/>Vector Storage]
        I --> J[🔗 LangChain<br/>Processing]
        J --> K[🤖 Google Gemini AI<br/>Analysis]
        K --> L[❓ MCQ Generation<br/>& Formatting]
    end
    
    subgraph "Quality & Storage"
        L --> M[✅ Question Validation<br/>& Quality Check]
        M --> N[🗄️ Database Storage<br/>SQLite/PostgreSQL]
        N --> O[📡 API Response<br/>to Client]
    end
    
    subgraph "Test Taking Flow"
        P[👤 User Takes Test] --> Q[📝 Answer Submission]
        Q --> R[🎯 Automatic Scoring<br/>& Evaluation]
        R --> S[📊 Results & Analytics<br/>Dashboard]
    end
    
    subgraph "AI Chat System"
        T[💬 User Chat Query] --> U[🧠 RAG System<br/>Processing]
        U --> I
        U --> V[🔍 Context Retrieval<br/>from Vectors]
        V --> W[🤖 AI Response<br/>Generation]
        W --> X[💬 Chat Response<br/>to User]
    end
    
    style A fill:#e1f5fe
    style O fill:#c8e6c9
    style S fill:#fff3e0
    style X fill:#f3e5f5
```

### Alternative Text-Based Flow

For environments where Mermaid diagrams don't render, here's the workflow in text format:

#### 📄 Document Processing Pipeline
```
1. Document Upload → 2. Format Detection → 3. Content Extraction
   ↓                    ↓                    ↓
   [PDF/DOCX/Image] → [Type Analysis] → [Text/OCR Processing]
```

#### 🤖 AI Processing Chain
```
4. Text Preprocessing → 5. CLIP Embeddings → 6. Vector Storage
   ↓                    ↓                    ↓
   [Clean & Format] → [Generate Vectors] → [ChromaDB Store]
   
7. LangChain Process → 8. Gemini AI → 9. MCQ Generation
   ↓                   ↓             ↓
   [Context Setup] → [AI Analysis] → [Question Creation]
```

#### ✅ Validation & Storage
```
10. Quality Check → 11. Database Store → 12. API Response
    ↓               ↓                   ↓
    [Validate] → [SQLite/PostgreSQL] → [JSON Response]
```

#### 🎓 Test Taking Process
```
User Login → Select Test → Answer Questions → Submit → Auto-Score → Results
     ↓           ↓             ↓              ↓         ↓          ↓
  [Auth] → [Test Selection] → [UI Interface] → [DB] → [Algorithm] → [Dashboard]
```

#### 💬 Chat System Flow
```
User Query → RAG Processing → Vector Search → Context Retrieval → AI Response
     ↓            ↓              ↓               ↓                ↓
  [Input] → [Question Analysis] → [ChromaDB] → [Relevant Docs] → [Gemini AI]
```

### Key Processing Components

| Component | Technology | Purpose |
|-----------|------------|---------|
| **Document Parser** | PyPDF2, PyMuPDF, python-docx | Extract text from various formats |
| **OCR Engine** | Tesseract | Process image-based documents |
| **Embeddings** | CLIP ViT-B/32 | Generate semantic vectors |
| **Vector DB** | ChromaDB | Store and search document embeddings |
| **AI Engine** | Google Gemini | Generate intelligent MCQs |
| **Framework** | LangChain | Orchestrate AI workflows |
| **Database** | SQLAlchemy + PostgreSQL/SQLite | Persistent data storage |
| **API** | FastAPI | RESTful web service interface |

## 📁 File & Folder Details

### Core Application Files

#### `main.py`
- **Purpose**: Application entry point and FastAPI app configuration
- **Key Features**:
  - CORS middleware setup
  - Database initialization
  - Vector database setup
  - Global exception handling
  - Health check endpoints
  - Lifespan management

#### `app/core/config.py`
- **Purpose**: Centralized configuration management
- **Features**:
  - Environment variable loading
  - Validation of configuration parameters
  - Default value management
  - Type safety with Pydantic

#### `app/core/database.py`
- **Purpose**: Database connection and session management
- **Components**:
  - SQLAlchemy engine configuration
  - Database session factory
  - Connection pool management
  - Database URL handling

#### `app/core/security.py`
- **Purpose**: Authentication and security utilities
- **Functions**:
  - JWT token creation and validation
  - Password hashing and verification
  - Security dependencies for routes
  - Role-based access control

#### `app/core/exceptions.py`
- **Purpose**: Custom exception classes
- **Exception Types**:
  - `AppException`: Base application exception
  - `AuthException`: Authentication errors
  - `ValidationException`: Data validation errors
  - `DatabaseException`: Database operation errors

### API Layer (`app/api/v1/`)

#### `admin.py`
- **Purpose**: Administrative endpoints
- **Key Endpoints**:
  - MCQ generation from documents
  - User management (role updates, account management)
  - Test management (create, update, delete)
  - System statistics and analytics
- **Security**: Admin role required for all endpoints

#### `auth.py`
- **Purpose**: Authentication and authorization
- **Endpoints**:
  - User registration with email verification
  - Login with JWT token generation
  - Token refresh mechanism
  - Password reset functionality
  - Logout and token invalidation

#### `tests.py`
- **Purpose**: Test and examination management
- **Features**:
  - Test creation and configuration
  - Test attempt management
  - Real-time test taking
  - Answer submission and validation
  - Results calculation and analytics
  - Test history and performance tracking

#### `users.py`
- **Purpose**: User profile and account management
- **Functions**:
  - Profile viewing and updating
  - Account settings management
  - Activity history
  - Performance analytics
  - Subscription status

#### `chatbot.py`
- **Purpose**: AI-powered chat functionality
- **Capabilities**:
  - Natural language query processing
  - Context-aware responses
  - Chat history management
  - Multi-turn conversations
  - Subject-specific assistance

#### `subscriptions.py`
- **Purpose**: Subscription and payment management
- **Features**:
  - Subscription plan management
  - Payment processing (Stripe, Razorpay)
  - Billing history
  - Feature access control
  - Subscription analytics

#### `categories.py`
- **Purpose**: Subject and category management
- **Functions**:
  - Subject categorization
  - Topic organization
  - Category-based filtering
  - Hierarchical category structure

### Data Models (`app/models/`)

#### `user.py`
- **Models**: User, UserRole, UserStatus
- **Features**:
  - User authentication data
  - Role-based permissions
  - Profile information
  - Activity tracking
  - Relationship definitions

#### `test.py`
- **Models**: Test, Question, Choice, TestSeries
- **Components**:
  - Test configuration
  - Question bank management
  - Multiple choice options
  - Test series organization
  - Difficulty levels and topics

#### `attempt.py`
- **Models**: TestAttempt, UserAnswer, TestResult
- **Tracking**:
  - Test attempt sessions
  - Individual answer recording
  - Time tracking
  - Score calculation
  - Performance metrics

#### `subscription.py`
- **Models**: SubscriptionPlan, UserSubscription, Payment
- **Management**:
  - Subscription tier definitions
  - User subscription status
  - Payment transaction records
  - Feature access control

#### `chat.py`
- **Models**: ChatSession, ChatMessage
- **Features**:
  - Chat session management
  - Message history
  - Context preservation
  - User interaction tracking

### Business Logic (`app/services/`)

#### `mcq_generator.py`
- **Purpose**: Main MCQ generation service
- **Capabilities**:
  - Integration with Google Gemini AI
  - Question quality validation
  - Difficulty level assignment
  - Topic categorization
  - Batch question generation

#### `fast_mcq_generator.py`
- **Purpose**: Optimized MCQ generation
- **Features**:
  - Faster processing using CLIP embeddings
  - ChromaDB integration
  - Streamlined question creation
  - Reduced API calls
  - Improved performance metrics

#### `document_processor.py`
- **Purpose**: Multi-format document processing
- **Supported Formats**:
  - PDF processing (PyPDF2, PyMuPDF)
  - Word document handling (python-docx)
  - Image OCR (Tesseract)
  - Text extraction and cleaning
  - Metadata extraction

#### `vector_service.py`
- **Purpose**: Vector database operations
- **Functions**:
  - ChromaDB management
  - Document embedding storage
  - Similarity search
  - Vector indexing
  - Retrieval operations

#### `rag_chatbot.py`
- **Purpose**: Retrieval-Augmented Generation chatbot
- **Features**:
  - Context-aware responses
  - Document-based knowledge retrieval
  - Multi-turn conversation support
  - Subject-specific assistance
  - Response quality optimization

### Configuration Files

#### `.env` / `.env.example`
- **Purpose**: Environment configuration
- **Categories**:
  - Server settings (host, port, debug mode)
  - Database configuration
  - API keys and secrets
  - Third-party service credentials
  - File upload settings

#### `requirements.txt`
- **Purpose**: Python package dependencies
- **Categories**:
  - Core FastAPI framework
  - Database and ORM packages
  - AI and ML libraries
  - Document processing tools
  - Payment and communication services

#### `Procfile`
- **Purpose**: Heroku deployment configuration
- **Content**: Web process definition for production deployment

### Supporting Directories

#### `models/`
- **Purpose**: Pre-trained model storage
- **Contents**:
  - CLIP model files
  - Model configurations
  - Tokenizer files
  - Model metadata

#### `uploads/`
- **Purpose**: Temporary file storage
- **Usage**:
  - Document upload handling
  - File processing workspace
  - Temporary storage during processing

#### `myenv/`
- **Purpose**: Python virtual environment
- **Contents**:
  - Isolated Python installation
  - Project-specific packages
  - Environment-specific configurations

## 🔒 Security Features

### Authentication & Authorization
- **JWT Token-based Authentication**
- **Role-based Access Control** (Admin, Teacher, Student)
- **Password Hashing** with bcrypt
- **Token Expiration** and refresh mechanisms
- **Secure Session Management**

### Data Protection
- **Input Validation** with Pydantic models
- **SQL Injection Prevention** via SQLAlchemy ORM
- **XSS Protection** through proper data sanitization
- **CORS Configuration** for cross-origin requests
- **File Upload Validation** and size limits

### API Security
- **Rate Limiting** for API endpoints
- **Request Size Limits** to prevent DoS attacks
- **Secure Headers** implementation
- **Environment Variable Protection**
- **Error Handling** without information disclosure

## 📊 Performance Optimization

### Database Optimization
- **Connection Pooling** for efficient database access
- **Query Optimization** with proper indexing
- **Lazy Loading** for related data
- **Database Migration Management** with Alembic

### Caching Strategy
- **Redis Integration** for session and data caching
- **Vector Caching** for frequently accessed embeddings
- **API Response Caching** for static data
- **Model Caching** to reduce loading times

### AI/ML Optimization
- **Model Caching** to avoid repeated downloads
- **Batch Processing** for multiple documents
- **Async Processing** for long-running tasks
- **Efficient Embedding Storage** with ChromaDB

## 🚢 Deployment

## 🚢 Deployment

### 🐳 Docker Deployment (Production Ready)

#### Option 1: Using Pre-built Image from Docker Hub
```bash
# Pull and run the latest image
docker pull prabhat9801/fastapi_mcq_platform
docker run -d -p 8000:8000 \
  --name mcq-platform \
  -e GOOGLE_API_KEY="your-api-key" \
  -e SECRET_KEY="your-secret-key" \
  prabhat9801/fastapi_mcq_platform
```

#### Option 2: Build Your Own Image
```bash
# Clone the repository
git clone https://github.com/Prabhat9801/Fastapi-mcq-platform.git
cd Fastapi-mcq-platform

# Build the Docker image
docker build -t fastapi-mcq-platform .

# Run the container
docker run -d -p 8000:8000 \
  --name mcq-platform \
  -e GOOGLE_API_KEY="your-api-key" \
  -e SECRET_KEY="your-secret-key" \
  fastapi-mcq-platform
```

#### Docker Compose (Recommended for Production)
```yaml
# docker-compose.yml
version: '3.8'
services:
  mcq-platform:
    image: prabhat9801/fastapi_mcq_platform
    ports:
      - "8000:8000"
    environment:
      - GOOGLE_API_KEY=your-google-api-key
      - DATABASE_URL=postgresql://user:password@db:5432/mcq_platform
      - SECRET_KEY=your-secret-key
      - REDIS_URL=redis://redis:6379
    depends_on:
      - db
      - redis
    volumes:
      - ./uploads:/app/uploads
      - ./models:/app/models

  db:
    image: postgres:15
    environment:
      - POSTGRES_DB=mcq_platform
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=password
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    
volumes:
  postgres_data:
```

```bash
# Run with Docker Compose
docker-compose up -d
```

### 🌐 Cloud Deployment

#### Deploy to any cloud platform that supports Docker:

**AWS ECS/EKS:**
```bash
# Use the Docker image: prabhat9801/fastapi_mcq_platform
```

**Google Cloud Run:**
```bash
gcloud run deploy mcq-platform \
  --image=prabhat9801/fastapi_mcq_platform \
  --platform=managed \
  --region=us-central1 \
  --allow-unauthenticated
```

**Azure Container Instances:**
```bash
az container create \
  --resource-group myResourceGroup \
  --name mcq-platform \
  --image prabhat9801/fastapi_mcq_platform \
  --ports 8000
```

**DigitalOcean App Platform:**
- Use Docker Hub image: `prabhat9801/fastapi_mcq_platform`
- Set environment variables in the dashboard

### Local Development
```bash
# Clone and setup
git clone <repository-url>
cd Fastapi-mcq-platform
python -m venv myenv
myenv\Scripts\activate  # Windows
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your settings

# Run application
python main.py
```

### 🐳 Building Custom Docker Image

If you want to build your own Docker image with modifications:

```bash
# Clone the repository
git clone https://github.com/Prabhat9801/Fastapi-mcq-platform.git
cd Fastapi-mcq-platform

# Build the image
docker build -t your-username/fastapi-mcq-platform .

# Run the container
docker run -p 8000:8000 your-username/fastapi-mcq-platform

# Push to your Docker Hub (optional)
docker tag your-username/fastapi-mcq-platform your-username/fastapi-mcq-platform:latest
docker push your-username/fastapi-mcq-platform:latest
```

### Docker Image Details

- **Base Image**: `python:3.10-slim`
- **Exposed Port**: `8000`
- **Working Directory**: `/app`
- **Pre-installed**: All dependencies from `requirements.txt`
- **Auto-runs**: Admin user creation on startup

### Heroku Deployment
1. **Prepare Procfile** (already included)
2. **Set Environment Variables** in Heroku dashboard
3. **Deploy**:
```bash
heroku create your-app-name
git push heroku main
```

**Note**: For easier deployment, consider using the Docker image:
```bash
# Deploy using Docker on Heroku
heroku container:push web --app your-app-name
heroku container:release web --app your-app-name
```

### Production Considerations
- **Database**: Use PostgreSQL instead of SQLite
- **Redis**: Set up Redis for caching
- **Environment Variables**: Secure API keys and secrets
- **Monitoring**: Implement logging and error tracking
- **Load Balancing**: Use nginx or similar for high traffic
- **SSL/TLS**: Enable HTTPS for production

## 🧪 Testing

### Running Tests
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app

# Run specific test file
pytest tests/test_mcq_generator.py
```

### Test Categories
- **Unit Tests**: Individual function testing
- **Integration Tests**: API endpoint testing
- **Database Tests**: Model and query testing
- **Authentication Tests**: Security feature testing

## 🤝 Contributing

### Development Setup
1. Fork the repository
2. Clone your fork
3. Create a feature branch
4. Make your changes
5. Add tests for new features
6. Run the test suite
7. Submit a pull request

### Code Style
- Follow PEP 8 guidelines
- Use type hints where applicable
- Document functions and classes
- Write meaningful commit messages

### Reporting Issues
- Use GitHub Issues for bug reports
- Provide detailed reproduction steps
- Include environment information
- Add relevant logs and error messages

## 📄 License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## � Repository Links

- **GitHub Repository**: [https://github.com/Prabhat9801/Fastapi-mcq-platform](https://github.com/Prabhat9801/Fastapi-mcq-platform)
- **Docker Hub**: [https://hub.docker.com/r/prabhat9801/fastapi_mcq_platform](https://hub.docker.com/r/prabhat9801/fastapi_mcq_platform)

## �👥 Support

### Getting Help
- **Documentation**: Check this README and API docs at `http://localhost:8000/api/docs`
- **Issues**: Report bugs via [GitHub Issues](https://github.com/Prabhat9801/Fastapi-mcq-platform/issues)
- **Discussions**: Use [GitHub Discussions](https://github.com/Prabhat9801/Fastapi-mcq-platform/discussions) for questions
- **Docker Hub**: Check [Docker Hub repository](https://hub.docker.com/r/prabhat9801/fastapi_mcq_platform) for image updates

### Community
- Star ⭐ the repository if you find it useful
- Fork and contribute to the project
- Share feedback and suggestions
- Help others in discussions

---

**Made with ❤️ by the Smart MCQ Platform Team**

*Last Updated: October 2024*
