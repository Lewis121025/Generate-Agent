# Lewis AI System

A dual-mode AI orchestration platform that provides structured workflows for creative content generation and general-purpose task automation.

## System Architecture

The system is built on a modular FastAPI backend with three primary routing layers:

### Core Routers

- **Creative Router** (`/creative`) - Manages multi-stage creative workflows from brief intake to final asset delivery
- **General Router** (`/general`) - Handles ReAct-based task execution with tool orchestration and iterative planning
- **Governance Router** (`/governance`) - Provides cost monitoring, usage analytics, and audit trails

### Service Layer

The application follows a layered architecture:

```
FastAPI Application
├── Router Layer (creative, general, governance)
├── Business Logic Layer (workflows, sessions, orchestrators)
├── Service Layer (agents, tooling, providers, cost monitoring)
└── Infrastructure Layer (database, cache, storage, vector DB)
```

### Data Persistence

- **PostgreSQL** - Primary relational database for projects, sessions, tool executions, and governance data
- **Redis** - Distributed caching, session state management, and rate limiting
- **Weaviate** - Vector database for semantic search and long-term memory
- **S3-Compatible Storage** - Object storage for generated artifacts and media files

### Workflow Orchestration

**Creative Mode** implements a staged pipeline:
- Brief intake and validation
- Script generation and refinement
- Storyboard planning
- Asset rendering
- Quality control and distribution

**General Mode** uses a ReAct loop:
- Task planning and decomposition
- Tool selection and execution
- Result synthesis and iteration
- Budget-aware execution with automatic throttling

## Technology Stack

### Backend

- **Runtime**: Python 3.11+
- **Framework**: FastAPI with async/await support
- **ORM**: SQLAlchemy 2.0 with asyncpg driver
- **Migrations**: Alembic for schema management
- **Caching**: Redis with async client
- **Vector DB**: Weaviate client with in-memory fallback
- **Storage**: boto3 for S3-compatible object storage
- **Task Queue**: ARQ for background job processing
- **Sandbox**: E2B Code Interpreter for secure code execution

### Frontend

- **Framework**: Next.js 14 with App Router
- **Language**: TypeScript
- **UI Library**: React 18
- **Styling**: Tailwind CSS
- **Components**: Radix UI primitives
- **State Management**: Zustand
- **Data Fetching**: TanStack Query
- **Animations**: Framer Motion

### Infrastructure

- **Containerization**: Docker with multi-stage builds
- **Orchestration**: Docker Compose
- **Database**: PostgreSQL 15+
- **Cache**: Redis 7+
- **Vector Store**: Weaviate (optional)

## Quick Start

### Prerequisites

- Python 3.11 or higher
- Node.js 18+ (for frontend)
- Docker and Docker Compose (for containerized deployment)
- PostgreSQL, Redis, and Weaviate (or use Docker Compose services)

### Installation

1. Clone the repository
2. Copy `.env.example` to `.env` and configure required API keys
3. Install backend dependencies: `pip install -e .`
4. Install frontend dependencies: `cd frontend && npm install`
5. Initialize database: `python -m lewis_ai_system.cli init-db`
6. Start services: `docker compose up -d` or use the provided startup scripts

### Configuration

Key environment variables:
- `DATABASE_URL` - PostgreSQL connection string
- `REDIS_URL` - Redis connection string
- `VECTOR_DB_URL` - Weaviate endpoint (optional)
- `S3_*` - Object storage credentials
- Provider API keys (OpenRouter, Runway, Pika, etc.)

See `.env.example` for complete configuration options.

## Project Structure

```
lewis_ai_system/
├── src/lewis_ai_system/
│   ├── routers/          # API route handlers
│   ├── creative/         # Creative workflow logic
│   ├── general/          # General session management
│   ├── governance/       # Cost and usage tracking
│   ├── agents.py         # Agent orchestration
│   ├── tooling.py        # Tool registry and execution
│   ├── providers.py      # LLM provider abstraction
│   ├── database.py       # SQLAlchemy models and setup
│   ├── redis_cache.py    # Cache management
│   ├── vector_db.py      # Vector database client
│   └── main.py           # FastAPI application
├── frontend/             # Next.js application
├── tests/                # Test suite
└── alembic/              # Database migrations
```

## License

MIT License
