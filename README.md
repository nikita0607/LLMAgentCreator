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

If you plan to run the frontend outside Docker:

```bash
cd frontend
npm install
cd ..
```

## 🐳 Running with Docker (Recommended)

### Quick Start

```bash
# Build and start all services
docker-compose up --build
```

This will start:

- **PostgreSQL Database** on port `5432`
- **Backend API** on port `8000`
- **Webhook Test Service** on port `8080`

### Service URLs

- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Webhook Test Service**: http://localhost:8080
- **Database**: localhost:5432 (user: `llm`, password: `llm`, database: `llm_agents`)

### Database Migrations

Migrations are handled automatically when the backend container starts. If you need to run them manually:

```bash
# Enter the backend container
docker exec -it llm_agents_backend bash

# Run migrations
alembic upgrade head
```

## 💻 Local Development (Without Docker)

### Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
export DATABASE_URL="postgresql://llm:llm@localhost:5432/llm_agents"
export JWT_SECRET="your-secret-key"
export ELEVENLABS_API_KEY="your-key"
export GROQ_API_KEY="your-key"

# Run database migrations
alembic upgrade head

# Start the backend server
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

The frontend will be available at http://localhost:3000

### Database Setup (Local PostgreSQL)

If running without Docker, you need a local PostgreSQL instance:

```bash
# Install PostgreSQL (macOS)
brew install postgresql
brew services start postgresql

# Create database and user
psql postgres
CREATE USER llm WITH PASSWORD 'llm';
CREATE DATABASE llm_agents OWNER llm;
GRANT ALL PRIVILEGES ON DATABASE llm_agents TO llm;
\q
```

## 🔧 API Keys Setup

### ElevenLabs API Key

1. Visit [ElevenLabs](https://elevenlabs.io/)
2. Create an account and get your API key
3. Add it to your `.env` file as `ELEVENLABS_API_KEY`

### Groq API Key

1. Visit [Groq](https://groq.com/)
2. Create an account and get your API key
3. Add it to your `.env` file as `GROQ_API_KEY`

## 📚 Usage

1. **Access the Application**: Open http://localhost:3000 (if running frontend separately) or use the API directly at http://localhost:8000

2. **Register/Login**: Create a user account through the authentication endpoints

3. **Create Agents**: Use the agent management interface to create and configure AI agents

4. **Start Chatting**: Interact with your agents through the chat interface

5. **API Documentation**: Visit http://localhost:8000/docs for interactive API documentation

## 🛠️ Development Commands

```bash
# View logs
docker-compose logs -f

# Stop services
docker-compose down

# Rebuild services
docker-compose up --build

# Run backend tests (if available)
docker exec -it llm_agents_backend pytest

# Access backend shell
docker exec -it llm_agents_backend bash

# Access database
docker exec -it llm_agents_db psql -U llm -d llm_agents
```

## 📁 Project Structure

```
LLMAgentCreator/
├── backend/                 # FastAPI backend
│   ├── app/
│   │   ├── api/            # API endpoints
│   │   ├── core/           # Configuration and security
│   │   ├── models/         # SQLAlchemy models
│   │   ├── schemas/        # Pydantic schemas
│   │   ├── services/       # Business logic
│   │   └── main.py         # FastAPI application
│   ├── migrations/         # Alembic migrations
│   └── requirements.txt    # Python dependencies
├── frontend/               # Next.js frontend
│   ├── app/               # Next.js app router
│   ├── components/        # React components
│   └── lib/              # Utilities and API client
├── test_webhook/          # Webhook test service
└── docker-compose.yaml    # Docker orchestration
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make your changes and commit: `git commit -m 'Add feature'`
4. Push to the branch: `git push origin feature-name`
5. Submit a pull request

## 📄 License

[Add your license information here]

## 📞 Support

If you encounter any issues or have questions:

1. Check the troubleshooting section above
2. Review the API documentation at http://localhost:8000/docs
3. Create an issue in the repository

---

**Happy coding! 🚀**
