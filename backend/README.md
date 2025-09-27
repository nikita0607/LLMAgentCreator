# LLMAgentCreator Backend

A powerful FastAPI-based backend service for creating, managing, and executing AI agents powered by large language models (LLMs). This service provides RESTful APIs for agent lifecycle management, user authentication, session handling, and external service integrations.

## 🚀 Features

- **Agent Management**: Create, configure, and manage AI agents with custom workflows
- **Real-time Chat**: Handle conversations between users and AI agents
- **Session Tracking**: Maintain conversation history and context across interactions
- **User Authentication**: Secure JWT-based authentication system
- **Webhook Integration**: Connect with external services like ElevenLabs and custom APIs
- **Database Migrations**: Version-controlled schema management with Alembic
- **LLM Integration**: Support for multiple LLM providers (Groq, OpenAI compatible APIs)
- **Voice Synthesis**: Integration with ElevenLabs for voice responses

## 🏗️ Architecture

The backend follows a modular architecture with clear separation of concerns:

```
backend/
├── app/
│   ├── api/                    # API endpoints and routing
│   │   ├── agents.py          # Agent management endpoints
│   │   ├── auth.py            # Authentication endpoints
│   │   ├── sessions.py        # Session management endpoints
│   │   └── webhooks.py        # Webhook integration endpoints
│   ├── core/                  # Core configuration and security
│   │   ├── config.py          # Application settings
│   │   ├── run_migrations.py  # Automatic migration script
│   │   └── security.py        # Authentication and security utilities
│   ├── models/                # SQLAlchemy ORM models
│   │   ├── agent.py           # Agent data model
│   │   ├── session.py         # Session data model
│   │   ├── session_message.py # Message data model
│   │   └── user.py            # User data model
│   ├── schemas/               # Pydantic schemas for request/response
│   │   ├── agent.py           # Agent schemas
│   │   ├── session.py         # Session schemas
│   │   └── user.py            # User schemas
│   ├── services/              # Business logic and external integrations
│   │   ├── agent_runtime.py   # Agent execution engine
│   │   ├── elevenlabs_chat.py # ElevenLabs integration
│   │   └── webhook.py         # Webhook handling service
│   ├── db.py                  # Database connection and session management
│   └── main.py                # FastAPI application entry point
├── migrations/                # Alembic database migrations
├── Dockerfile                 # Container configuration
├── alembic.ini               # Alembic configuration
├── run_migrations.py         # Standalone migration script
├── run_migrations.sh         # Shell script for migrations
├── run_migrations.bat        # Windows batch script for migrations
└── requirements.txt          # Python dependencies
```

## 🛠️ Technology Stack

- **Framework**: FastAPI 0.116.1 - Modern, fast web framework for building APIs
- **Database**: PostgreSQL 15 with SQLAlchemy 2.0.43 ORM
- **Migration Tool**: Alembic 1.16.4 for database schema versioning
- **Authentication**: JWT tokens with python-jose and passlib for password hashing
- **Server**: Uvicorn ASGI server for high-performance async handling
- **External APIs**:
  - Groq SDK for LLM inference
  - ElevenLabs SDK for voice synthesis
- **Configuration**: Pydantic Settings for environment-based configuration
- **Validation**: Pydantic 2.11.7 for data validation and serialization

## 📋 Prerequisites

- Python 3.11+
- PostgreSQL 15
- Docker (recommended for development)
- Git

## 🔧 Installation & Setup

### Option 1: Docker Development (Recommended)

1. **Clone the repository**:

   ```bash
   git clone <repository-url>
   cd LLMAgentCreator
   ```

2. **Set up environment variables**:

   ```bash
   cd backend
   cp .env.example .env  # Create this file if it doesn't exist
   ```

3. **Configure `.env` file**:

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

4. **Start all services**:

   ```bash
   cd ..  # Back to root directory
   docker-compose up --build
   ```

5. **Run database migrations** (now automatic, but can be run manually):
   ```bash
   docker exec -it llm_agents_backend alembic upgrade head
   ```

### Option 2: Local Development

1. **Set up Python virtual environment**:

   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install dependencies**:

   ```bash
   pip install -r requirements.txt
   ```

3. **Set up PostgreSQL database**:

   ```bash
   # Install PostgreSQL and create database
   createdb llm_agents
   createuser llm --pwprompt  # Set password as 'llm'
   ```

4. **Configure environment variables**:

   ```bash
   cp .env.example .env
   # Edit .env with your local database URL:
   # DATABASE_URL=postgresql://llm:llm@localhost:5432/llm_agents
   ```

5. **Run database migrations** (now automatic, but can be run manually):

   ```bash
   # Automatic (when starting the application)
   # Or manually:
   alembic upgrade head
   
   # Or using our standalone script:
   python run_migrations.py
   ```

6. **Start the development server**:
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
   ```

## 🗄️ Database Setup

### Running Migrations

Migrations now run automatically when the application starts. However, you can still run them manually:

```bash
# Create a new migration
alembic revision --autogenerate -m "Description of changes"

# Apply migrations manually
alembic upgrade head

# Using our standalone scripts (choose your platform):
python run_migrations.py    # Python script
./run_migrations.sh         # Linux/Mac script
run_migrations.bat          # Windows batch file

# View migration history
alembic history

# Rollback to previous version
alembic downgrade -1
```

### Database Schema

The application uses the following main entities:

- **User**: User accounts with authentication
- **Agent**: AI agent configurations with workflow definitions
- **Session**: Conversation sessions between users and agents
- **SessionMessage**: Individual messages within sessions

## 🔌 API Endpoints

### Authentication

- `POST /auth/register` - Register a new user
- `POST /auth/login` - User login (returns JWT token)

### Agents

- `GET /agents` - List user's agents
- `POST /agents` - Create a new agent
- `GET /agents/{id}` - Get agent details
- `PUT /agents/{id}` - Update agent configuration
- `DELETE /agents/{id}` - Delete an agent

### Sessions

- `GET /sessions` - List user's sessions
- `POST /sessions` - Create a new session
- `GET /sessions/{id}` - Get session details
- `POST /sessions/{id}/message` - Send message to agent
- `DELETE /sessions/{id}` - Delete a session

### Webhooks

- `POST /webhooks/call` - Execute webhook with dynamic parameters

### API Documentation

When the server is running, interactive API documentation is available at:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 🧪 Testing

### Manual Testing with curl

```bash
# Health check
curl http://localhost:8000/docs

# Register a user
curl -X POST "http://localhost:8000/auth/register" \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "password123"}'

# Login
curl -X POST "http://localhost:8000/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=test@example.com&password=password123"

# Create an agent (with JWT token)
curl -X POST "http://localhost:8000/agents" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "Test Agent", "description": "A test agent"}'
```

### Running Tests

```bash
# Install test dependencies
pip install pytest pytest-asyncio httpx

# Run tests
pytest tests/

# Run with coverage
pytest --cov=app tests/
```

## 🔧 Configuration

### Environment Variables

| Variable             | Description                            | Required | Default                    |
| -------------------- | -------------------------------------- | -------- | -------------------------- |
| `DATABASE_URL`       | PostgreSQL connection string           | ✅       | -                          |
| `REDIS_URL`          | Redis connection string                | ❌       | `redis://localhost:6379/0` |
| `JWT_SECRET`         | Secret key for JWT tokens              | ✅       | -                          |
| `JWT_ALGORITHM`      | JWT signing algorithm                  | ❌       | `HS256`                    |
| `ELEVENLABS_API_KEY` | ElevenLabs API key for voice synthesis | ✅       | -                          |
| `GROQ_API_KEY`       | Groq API key for LLM inference         | ✅       | -                          |

### Application Settings

The application settings are managed through `app/core/config.py` using Pydantic Settings, which automatically loads configuration from environment variables and `.env` files.

## 🚀 Deployment

### Docker Production Deployment

1. **Update docker-compose.yaml for production**:

   ```yaml
   services:
     backend:
       environment:
         - NODE_ENV=production
       # Remove volume mount for production
       # volumes:
       #   - ./backend:/app
   ```

2. **Build and deploy**:
   ```bash
   docker-compose -f docker-compose.prod.yaml up --build -d
   ```

### Manual Production Deployment

1. **Install dependencies**:

   ```bash
   pip install -r requirements.txt
   ```

2. **Set production environment variables**:

   ```bash
   export DATABASE_URL="postgresql://user:password@host:5432/dbname"
   export JWT_SECRET="your-production-secret"
   export ELEVENLABS_API_KEY="your-key"
   export GROQ_API_KEY="your-key"
   ```

3. **Run database migrations** (automatic on startup):

   ```bash
   # Migrations will run automatically when the app starts
   # Manual option:
   alembic upgrade head
   ```

4. **Start with production server**:
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
   ```

## 🔍 Troubleshooting

### Common Issues

1. **Database connection errors**:

   - Verify PostgreSQL is running
   - Check DATABASE_URL format
   - Ensure database exists and user has permissions

2. **Migration failures**:

   ```bash
   # Reset migrations (development only)
   alembic stamp head
   alembic revision --autogenerate -m "Reset migrations"
   ```

3. **JWT token errors**:

   - Verify JWT_SECRET is set
   - Check token expiration
   - Ensure consistent JWT_ALGORITHM

4. **External API failures**:
   - Verify API keys are valid
   - Check network connectivity
   - Review API rate limits

### Logs and Debugging

```bash
# View application logs
docker logs llm_agents_backend

# Enable debug logging
export LOG_LEVEL=DEBUG
uvicorn app.main:app --log-level debug
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Make your changes and add tests
4. Run the test suite: `pytest`
5. Commit your changes: `git commit -am 'Add some feature'`
6. Push to the branch: `git push origin feature/your-feature`
7. Submit a pull request

### Code Style

- Follow PEP 8 style guidelines
- Use type hints for all functions
- Add docstrings for all public functions
- Run `ruff` for linting: `ruff check .`

## 📄 License

[Add your license information here]

## 🆘 Support

For support and questions:

- Create an issue in the repository
- Check the troubleshooting section above
- Review the API documentation at `/docs`