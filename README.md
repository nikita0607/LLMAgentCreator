# SOSI CHLEN

# LLMAgentCreator

**LLMAgentCreator** is a full-stack application for creating, managing, and interacting with AI agents powered by large language models (LLMs). The platform provides agent lifecycle management, real-time chat capabilities, session handling, authentication, and integration with external services.

## 🚀 Features

- **Agent Management**: Create, configure, and manage AI agents
- **Real-time Chat**: Interactive chat interface with AI agents
- **Session Tracking**: Persistent conversation history and context
- **User Authentication**: Secure login and registration system
- **Webhook Integration**: External service communication (ElevenLabs voice synthesis)
- **Database Migrations**: Version-controlled schema management with Alembic

## 🏗️ Architecture

- **Frontend**: Next.js 15 with TypeScript, React, and Tailwind CSS
- **Backend**: FastAPI with SQLAlchemy ORM and Alembic migrations
- **Database**: PostgreSQL
- **Webhook Service**: FastAPI test service for webhook testing
- **Deployment**: Docker Compose for local development

## 📋 Prerequisites

Before running the project, ensure you have the following installed:

- **Docker** and **Docker Compose**
- **Node.js** (v18+ recommended)
- **Python** 3.11+
- **Git**

## ⚙️ Setup Instructions

### 1. Clone the Repository

```bash
git clone <repository-url>
cd LLMAgentCreator
```

### 2. Environment Configuration

Create a `.env` file in the `backend` directory with the following variables:

```bash
# Backend Environment Variables
cp backend/.env.example backend/.env  # if example exists, otherwise create manually
```

Create `backend/.env` with the following content:

```env
# Database Configuration
DATABASE_URL=postgresql://llm:llm@db:5432/llm_agents

# Redis Configuration (optional)
REDIS_URL=redis://localhost:6379/0

# JWT Configuration
JWT_SECRET=your-super-secret-jwt-key-change-this-in-production
JWT_ALGORITHM=HS256

# External API Keys
ELEVENLABS_API_KEY=your-elevenlabs-api-key
GROQ_API_KEY=your-groq-api-key
```

**Important**: Replace the placeholder values with your actual API keys and secure secrets.

### 3. Frontend Dependencies (Optional for Docker)

Але если ты не знаешь как запустить иди учись емое