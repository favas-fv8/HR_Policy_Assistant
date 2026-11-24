# HR Policy Assistant

AI-powered HR Policy Assistant that allows employees to ask questions about company HR policies and receive accurate answers based on HR-uploaded documents using Retrieval-Augmented Generation (RAG).

## Overview

This project implements a complete HR Policy Assistant system with:

- **Backend**: Django REST Framework with PostgreSQL
- **RAG Pipeline**: Custom implementation using PyMuPDF, Gemini embeddings, and cosine similarity search
- **Frontend**: React + Vite (to be developed)
- **Authentication**: Role-based access control (HR Admin vs Employee)

## Architecture

```text
┌─────────────────────────────────────────────────────────────────┐
│                    HR POLICY ASSISTANT SYSTEM                    │
├─────────────────────┬─────────────────────┬────────────────────┤
│   FRONTEND          │     BACKEND API     │    DATABASE        │
│  (React + Vite)     │  (Django REST Fr.)  │ (PostgreSQL + pgvec)│
├─────────────────────┼─────────────────────┼────────────────────┤
│  UI Components      │  Auth & RBAC        │  auth_users        │
│  Pages              │  User Management    │  employees         │
│  Chat Interface     │  Document Mgmt      │  documents         │
│  Navigation         │  PDF Processing     │  chunks (vector)   │
│  Forms              │  Embedding Service  │  conversations     │
└────────▲─────────────┼────────▲─────────────┼────────▲─────────┘
           │                │                │                │
           │                │                │                │
           ▼                ▼                ▼                ▼
┌─────────────────────────────────────────────────────────────────┐
│                    EXTERNAL SERVICES                            │
│  Google Gemini API (embeddings + generation)                   │
│  Docker & Kubernetes (deployment)                              │
│  GitHub (version control)                                      │
└─────────────────────────────────────────────────────────────────┘
```

## Key Features

### HR Admin

- Secure admin login
- Create, edit, deactivate and manage employee accounts
- Generate employee user IDs and passwords
- Upload, view and delete HR policy documents (PDF)
- Manage uploaded documents
- View employee activity and chat history where authorized
- Manage the knowledge base

### Employee

- Login using credentials created by HR Admin
- View personal profile
- Change password
- Access the AI chatbot
- Create new conversations
- View previous conversations and chat history
- Ask questions about HR policies
- View relevant HR documents and source references
- See document names, page numbers and relevant excerpts supporting answers

### Additional Pages

- Home / Dashboard
- About Us
- Profile
- Change Password
- AI Chatbot
- Document Library
- Login
- Logout

## Technology Stack

### Backend

- **Framework**: Django 4.2.30 (LTS) + Django REST Framework
- **Database**: PostgreSQL with JSONB vector storage (pgvector via Docker optional)
- **AI**: Google Gemini API (`text-embedding-004` for embeddings, `gemini-1.5-flash` for generation)
- **PDF Processing**: PyMuPDF
- **RAG**: Custom Python implementation (no LangChain or LlamaIndex)
- **Authentication**: Django authentication + SimpleJWT
- **API**: DRF ViewSets with role-based permissions

### Frontend (Planned)

- **Framework**: React + Vite
- **State Management**: Redux Toolkit or React Context
- **Routing**: React Router
- **API Client**: Axios with interceptors for auth
- **UI Library**: Lucide icons, custom components

### RAG Pipeline

```text
HR Upload PDF
    ↓
PyMuPDF text extraction
    ↓
Text chunking (sentence-aware, overlap)
    ↓
Gemini embedding generation (text-embedding-004, 3072 dimensions)
    ↓
Store embeddings + metadata in PostgreSQL (JSONB)
    ↓
Employee question → embedding conversion
    ↓
Cosine similarity search (Python implementation)
    ↓
Retrieve top-k relevant chunks
    ↓
Build prompt: "Answer using only: {context}\nQuestion: {question}"
    ↓
Gemini generation (gemini-1.5-flash)
    ↓
Return answer + document references/page numbers
```

## Environment Configuration

### Backend (.env)

```env
# Database Configuration
POSTGRES_DB=hr_assistant
POSTGRES_USER=postgres
POSTGRES_PASSWORD=sql@321
POSTGRES_HOST=localhost
POSTGRES_PORT=5432

# Google Gemini API Configuration
# Get your API key from: https://aistudio.google.com/
GEMINI_API_KEY=your-api-key-here

# Django Configuration
DJANGO_SECRET_KEY=django-insecure-dev-key-do-not-use-in-production
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1

# RAG Configuration
RAG_SIMILARITY_THRESHOLD=0.7
RAG_RETRIEVAL_LIMIT=5
RAG_CHUNK_SIZE=1000
RAG_CHUNK_OVERLAP=200
```

### Frontend (.env)

```env
# Vite Configuration
VITE_API_BASE_URL=http://localhost:8000/api
VITE_ENVIRONMENT=development

# API Timeout (ms)
VITE_API_TIMEOUT=30000
```

### Docker

Docker Compose configuration is available in `docker/docker-compose.yml`:
- Uses `postgres:18` with pgvector enabled via `pgvector/pgvector:pg18` image
- Backend Django application
- Frontend React Vite development server (to be added)

## Database Setup

### PostgreSQL Requirements

- **Database**: `hr_assistant`
- **Username**: `postgres`
- **Password**: `sql@321`
- **Host**: `localhost`
- **Port**: `5432`

### Creating the Database

```bash
# Using psql
psql -U postgres -c "CREATE DATABASE hr_assistant;

# Using the provided script
python manage.py migrate  # After setting up .env
```

### Django Migrations

```bash
cd backend
python manage.py migrate
# Creates all necessary tables:
# - accounts_customuser, auth_permission, etc.
# - documents_document, documents_documentchunk
# - chat_conversation, chat_message
```

## API Endpoints

### Authentication (`api/v1/auth/`)

- `POST /api/v1/auth/token/` - Obtain auth token
- `POST /api/v1/auth/token/refresh/` - Refresh token
- `POST /api/v1/auth/logout/` - Logout

### Accounts (`api/v1/accounts/`)

- `GET /api/v1/accounts/users/` - List all users (HR Admin only)
- `GET /api/v1/accounts/users/me/` - Current user profile
- `POST /api/v1/accounts/users/` - Create new user (HR Admin only)
- `GET /api/v1/accounts/profile/` - Employee profile

### Documents (`api/v1/documents/`)

- `GET /api/v1/documents/` - List all documents
- `POST /api/v1/documents/` - Upload document (HR Admin only)
- `GET /api/v1/documents/<id>/` - Get document details
- `DELETE /api/v1/documents/<id>/` - Delete document (HR Admin only)
- `GET /api/v1/documents/<id>/chunks/` - Get document chunks

### RAG (`api/v1/rag/`)

- `GET /api/v1/rag/` - Pipeline status
- `POST /api/v1/rag/ask/` - Ask question about HR policies
  - Request: `{"question": "Your question here"}`
  - Response: `{"answer": "...", "sources": [...], "reference_count": N}`
- `POST /api/v1/rag/process/` - Process a document through RAG pipeline
  - Request: `{"document_id": 1}`

### Chat (`api/v1/chat/`)

- `GET /api/v1/chat/conversations/` - List conversations
- `POST /api/v1/chat/conversations/new/` - Create new conversation
- `GET /api/v1/chat/conversations/<id>/messages/` - Get conversation messages
- `POST /api/v1/chat/conversations/<id>/send/` - Send message and get AI response

### Security

- **HR Admin endpoints**: User management, document upload/delete
- **Employee endpoints**: Chat, document retrieval, profile view
- **Permission checks**: `is_hr_admin` flag enforced on all sensitive endpoints
- **API keys**: `GEMINI_API_KEY` only in backend `.env`, never exposed to frontend
- **File upload validation**: PDF only, max 10MB

## RAG Architecture

### Workflow

```text
1. HR Uploads PDF Document
   └─ PyMuPDF extracts text
   └─ Text split into chunks (1000 chars, 200 overlap)
   └─ Gemini embeddings (text-embedding-004, 3072 dimensions)
   └─ JSONB stored in PostgreSQL

2. Employee Asks Question
   └─ Question converted to embedding (same model)
   └─ Cosine similarity search against stored embeddings
   └─ Top-k chunks retrieved (configurable threshold: 0.7, limit: 5)
   └─ Prompt built with retrieved context
   └─ Gemini generates grounded answer (gemini-1.5-flash)
   └─ Answer returned with document references and page numbers
```

### Similarity Configuration

- **Threshold**: `RAG_SIMILARITY_THRESHOLD` (0.0-1.0, default 0.7)
  - Higher = more stringent (fewer, more relevant results)
  - Lower = more results (including less relevant)

- **Retrieval Limit**: `RAG_RETRIEVAL_LIMIT` (default 5)
  - Maximum number of chunks to return

- **Similarity Function**: Cosine similarity between query and chunk embeddings
  - Implemented in `backend/vector/similarity.py`
  - Can use Python JSONB or PostgreSQL pgvector `<=>` operator

### Grounded Answer Guidelines

- Answers are based **solely** on the retrieved context
- If context doesn't contain the answer, clearly state information is unavailable
- **Never invent** HR policy information
- Include document references: `[Source: Title, Page N]`
- Excerpts from source documents included in the answer

## Testing

### Running Tests

```bash
# Django system check
python manage.py check

# Verify migrations are up to date
python manage.py makemigrations --check --dry-run

# Run all tests
python manage.py test

# Specific test modules
python -m django test accounts documents rag chat
```

### Test Results (Current)

| Test Module | Tests | Result |
|-------------|-------|--------|
| accounts.CustomUserModelTest | 3 | ✅ Passed |
| accounts.UserPermissionTest | 2 | ✅ Passed |
| documents.DocumentModelTest | 2 | ✅ Passed |
| documents.DocumentChunkTest | 2 | ✅ Passed |

### Manual Testing Checklist

- [ ] User registration (HR Admin + Employee)
- [ ] Login/logout functionality
- [ ] HR Admin can upload documents
- [ ] Employee cannot upload documents (403)
- [ ] HR Admin can delete documents
- [ ] Employee cannot delete documents (403)
- [ ] HR Admin can list all documents
- [ ] Employees can view documents and chunks
- [ ] Create conversation in chat
- [ ] Send message in chat → receive AI response with sources
- [ ] Employee can only access their own conversations
- [ ] RAG question answering with citations
- [ ] Similarity threshold configuration
- [ ] Missing policy information handling

## Development Workflow

### Phase Summary (Completed)

1. ✅ Project structure and environment setup
2. ✅ PostgreSQL database design and Django models
3. ✅ Authentication and role-based permissions
4. ✅ HR document upload and management
5. ✅ PDF extraction, chunking and embedding generation
6. ✅ Vector similarity search (JSONB)
7. ✅ Gemini-powered RAG implementation
8. ✅ Chat APIs, conversation history and citations
9. ✅ Security review and unauthorized access prevention
10. ✅ Automated testing

### Upcoming Phases

- **Phase 12**: React frontend implementation (Vite + TypeScript)
- **Phase 13**: Frontend/backend integration
- **Phase 14**: Testing, security optimization, Docker/Kubernetes

## Getting Started

### Prerequisites

- Python 3.12+
- PostgreSQL 18+ with hr_assistant database
- Google Gemini API key from [AI Studio](https://aistudio.google.com/)
- Docker (optional, for pgvector)

### Installation

```bash
# 1. Clone repository
git clone https://github.com/favas-fv8/HR_Policy_Assistant.git
cd HR_Policy_Assistant

# 2. Backend setup
cd backend
python -m pip install -r requirements.txt
cp .env.example .env
# Edit .env with your values (especially GEMINI_API_KEY)

# 3. Database setup
psql -U postgres -c "CREATE DATABASE hr_assistant"
python manage.py migrate

# 4. Run migrations for all apps
python manage.py migrate

# 5. Create superuser (HR Admin)
python manage.py createsuperuser

# 5. Start development server
python manage.py runserver
```

## Version

v0.1.0 - Backend foundation complete, ready for frontend development