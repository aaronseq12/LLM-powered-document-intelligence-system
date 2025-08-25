<div align="center">

# LLM-Powered Document Intelligence System

**An enterprise-grade platform for intelligent document processing, leveraging Azure AI and modern cloud-native architecture.**

</div>

<p align="center">
  <a href="https://github.com/aaronseq12/LLM-powered-document-intelligence-system/actions/workflows/ci-cd.yml"><img src="https://github.com/aaronseq12/LLM-powered-document-intelligence-system/actions/workflows/ci-cd.yml/badge.svg" alt="CI/CD Status"></a>
  <a href="https://codecov.io/gh/aaronseq12/LLM-powered-document-intelligence-system"><img src="https://codecov.io/gh/aaronseq12/LLM-powered-document-intelligence-system/branch/main/graph/badge.svg" alt="Coverage"></a>
  <a href="https://opensource.org/licenses/MIT"><img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="License: MIT"></a>
</p>

---

## 📋 Table of Contents

- [Overview](#-overview)
- [Key Features](#-key-features)
- [System Architecture](#-system-architecture)
- [Getting Started](#-getting-started)
- [Project Structure](#-project-structure)
- [Configuration](#-configuration)
- [Development & Operations](#-development--operations)
- [API Endpoints](#-api-endpoints)
- [Contributing](#-contributing)
- [License](#-license)

---

## ✨ Overview

This project is a comprehensive, production-ready platform designed to revolutionize document processing. By integrating **Azure AI services**, **Large Language Models (LLMs)**, and **modern web technologies**, it provides a scalable, secure, and high-performance solution for extracting intelligent insights from documents.

---

## 🎯 Key Features

| Feature                | Description                                                                                             | Technology Stack                        |
| ---------------------- | ------------------------------------------------------------------------------------------------------- | --------------------------------------- |
| **🤖 AI-Powered Engine** | Utilizes GPT-4 Turbo for contextual understanding and intelligent data extraction from unstructured text. | Azure OpenAI, LangChain                 |
| **📄 Advanced OCR** | Achieves high accuracy for diverse document types and layouts.                | Azure Document Intelligence             |
| **⚡ Real-time Updates** | Live status tracking of document processing via a persistent WebSocket connection.                      | WebSockets, FastAPI                     |
| **🖥️ Modern Interface** | A responsive and intuitive user interface built for a seamless user experience.                         | React 18, TypeScript, Material-UI       |
| **🚀 High Performance** | Asynchronous architecture and connection pooling ensure low latency and high throughput.                | Async/await, Connection Pooling         |
| **🛡️ Enterprise Security** | Implements robust security protocols including JWT and secure infrastructure practices.          | JWT, OAuth2, Secure Containers          |
| **🐳 Container-Ready** | Multi-stage Docker builds and Compose configurations for consistent, reproducible deployments.            | Docker, Docker Compose                  |
| **🔄 CI/CD Automation** | Fully automated pipeline for testing, security scanning, and deploying to various environments.           | GitHub Actions                          |

---

## 🏗️ System Architecture

The system follows a microservices-oriented architecture, ensuring separation of concerns, scalability, and maintainability.

<details>
<summary><strong>▶️ View Architecture Diagram</strong></summary>

```mermaid
graph TD
    subgraph "Client Layer"
        A[React App] --> B[API Gateway]
    end

    subgraph "Service Layer"
        B[API Gateway (FastAPI)] --> C{Business Logic}
        C --> D[LLM Service (LangChain)]
        C --> E[Processing Queue (Redis)]
    end

    subgraph "AI & Data Layer"
        D --> F[Azure OpenAI]
        D --> G[Azure Document Intelligence]
        C --> H[PostgreSQL Database]
        C --> I[File Storage]
    end

</details>
🚀 Getting Started
Prerequisites
 * Python 3.11+
 * Node.js 18+
 * Docker & Docker Compose
 * An Azure account with access to AI Services
⚡ One-Command Quick Start
This single command clones the repository, sets up the environment, builds containers, and starts the entire application stack.
git clone [https://github.com/aaronseq12/LLM-powered-document-intelligence-system.git](https://github.com/aaronseq12/LLM-powered-document-intelligence-system.git)
cd LLM-powered-document-intelligence-system
make quick-start

<details>
<summary><strong>▶️ View Manual Setup Instructions</strong></summary>
 * Install Dependencies:
   make install-backend
make install-frontend

 * Configure Environment:
   make create-env 
# Now, edit the generated .env file with your credentials

 * Launch Services & Database:
   make dev-services # Starts Postgres & Redis
make db-setup     # Initializes the database

 * Run the Application:
   make dev

</details>
Access Points
 * Frontend Application: http://localhost:3000
 * Backend API: http://localhost:8000
 * Interactive API Docs: http://localhost:8000/docs
📁 Project Structure
The repository is organized into distinct modules for the backend, frontend, and infrastructure, promoting a clean and scalable codebase.
<details>
<summary><strong>▶️ View Directory Tree</strong></summary>
LLM-powered-document-intelligence-system/
├── backend/                 # Python/FastAPI application
│   ├── main.py              # API application entry point
│   ├── llm_service.py       # Core logic for LangChain & Azure OpenAI
│   ├── database.py          # SQLAlchemy models and DB session
│   └── requirements.txt     # Python dependencies
│
├── frontend/                # React/TypeScript application
│   ├── src/
│   │   ├── components/      # Reusable UI components
│   │   ├── pages/           # Application pages/routes
│   │   └── services/        # API communication layer
│   ├── vite.config.ts       # Vite build configuration
│   └── package.json         # Node.js dependencies
│
├── infrastructure/          # Docker, Gunicorn, and environment setup
│   ├── Dockerfile           # Optimized multi-stage Docker build
│   ├── docker-compose.yml   # Service orchestration
│   └── .env.example         # Template for environment variables
│
└── .github/workflows/       # CI/CD pipelines
    └── ci-cd.yml            # Automated build, test, and deploy workflow

</details>
⚙️ Configuration
Copy the .env.example file to .env and populate it with your service credentials.
# --- Azure AI Services ---
AZURE_OPENAI_API_KEY="your-azure-openai-api-key"
AZURE_OPENAI_ENDPOINT="[https://your-resource.openai.azure.com](https://your-resource.openai.azure.com)"
AZURE_DOCUMENT_INTELLIGENCE_KEY="your-document-intelligence-key"
AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT="[https://your-resource.cognitiveservices.azure.com](https://your-resource.cognitiveservices.azure.com)"

# --- Application ---
DATABASE_URL="postgresql+asyncpg://postgres:password@db:5432/document_intelligence"
REDIS_URL="redis://redis:6379/0"

# --- Security ---
SECRET_KEY="your-super-strong-secret-key"

🛠️ Development & Operations
A comprehensive Makefile provides commands to streamline development and operational tasks.
| Category | Command | Description |
|---|---|---|
| 🚀 General | make dev | Starts the complete development environment. |
| 🧪 Testing | make test | Runs all unit and integration tests. |
| ✨ Quality | make lint | Checks code against style guides. |
|  | make format | Automatically formats all code. |
| 🐳 Docker | make docker-build | Builds all necessary Docker images. |
| 🗃️ Database | make db-migrate | Creates a new database migration file. |
|  | make db-upgrade | Applies all pending migrations to the database. |
🔌 API Endpoints
A RESTful API provides access to all system functionalities. For full details, see the interactive Swagger UI documentation.
| Method | Endpoint | Description |
|---|---|---|
| GET | /health | Health check for the API service. |
| POST | /auth/login | Authenticates a user and returns a JWT. |
| POST | /api/documents/upload | Uploads a new document for processing. |
| GET | /api/documents/{id} | Retrieves metadata for a specific document. |
| GET | /api/documents/{id}/status | Gets the current processing status. |
| WebSocket | /ws/{client_id} | Establishes a WebSocket for real-time updates. |
🤝 Contributing
We welcome contributions! Please fork the repository, create a new branch, and submit a pull request.
📝 License
This project is licensed under the MIT License. See the LICENSE file for details.

