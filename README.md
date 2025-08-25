<div align="center">
Your Smart Document Intelligence System
Tired of manually sifting through documents? This platform uses the power of AI to automatically read, understand, and extract key information for you.
</div>
<p align="center">
<a href="https://github.com/aaronseq12/LLM-powered-document-intelligence-system/actions/workflows/ci-cd.yml">
<img src="https://github.com/aaronseq12/LLM-powered-document-intelligence-system/actions/workflows/ci-cd.yml/badge.svg" alt="CI/CD Status">
</a>
<a href="https://pypi.org/project/llm-document-intelligence/">
<img src="https://img.shields.io/pypi/v/llm-document-intelligence?logo=python" alt="PyPI Version">
</a>
<a href="https://hub.docker.com/r/aaronseq12/llm-document-intelligence">
<img src="https://img.shields.io/docker/pulls/aaronseq12/llm-document-intelligence?logo=docker" alt="Docker Pulls">
</a>
<a href="https://opensource.org/licenses/MIT">
<img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="License: MIT">
</a>
</p>
📖 Table of Contents
 * ✨ Overview
 * 🎯 Key Features
 * 🏗️ System Architecture
 * 🚀 Getting Started
 * 📂 Project Structure
 * ⚙️ Configuration
 * 🛠️ Development & Operations
 * 🤝 Contributing
 * 📜 License
✨ Overview
This project is a complete, production-ready platform designed to make document processing a breeze. By combining Azure's powerful AI services with Large Language Models (LLMs) and modern web technology, it offers a scalable, secure, and fast solution for turning your documents into valuable insights.
🎯 Key Features
| Feature | Description | Technology Stack |
|---|---|---|
| 🧠 AI-Powered Engine | Uses GPT-4 Turbo to understand context and intelligently pull data from messy, unstructured text. | Azure OpenAI, LangChain |
| 📄 Advanced OCR | Accurately extracts text from all kinds of document types and layouts. | Azure Document Intelligence |
| ⚡ Real-time Updates | Watch the status of your documents being processed live through a persistent WebSocket connection. | WebSockets, FastAPI |
| 🖥️ Modern Interface | A clean, responsive, and intuitive user interface designed for a great user experience. | React 18, TypeScript, Material-UI |
| 🚀 High Performance | Built for speed, its asynchronous design handles many documents at once without breaking a sweat. | Async/await, Connection Pooling |
| 🛡️ Enterprise Security | Implements strong security measures like JWT and secure infrastructure to keep your data safe. | JWT, OAuth2, Secure Containers |
| 🐳 Container-Ready | Comes with Docker configurations for easy, consistent, and reproducible deployments anywhere. | Docker, Docker Compose |
| 🔄 CI/CD Automation | A fully automated pipeline handles testing, security scans, and deployment for you. | GitHub Actions |
🏗️ System Architecture
The system is built using a microservices-oriented approach, which keeps things organized, scalable, and easy to maintain.
<details>
<summary><strong>▶️ View Architecture Diagram</strong></summary>
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
 * Python 3.11+ 🐍
 * Node.js 18+ ⚡
 * Docker & Docker Compose 🐳
 * Azure account with AI Services access ☁️
⚡ One-Command Quick Start
This single command clones the repository, sets up your environment, builds the necessary containers, and launches the entire application.
git clone https://github.com/aaronseq12/LLM-powered-document-intelligence-system.git
cd LLM-powered-document-intelligence-system
make quick-start

<br/>
<details>
<summary><strong>▶️ View Manual Setup Steps</strong></summary>
# 1. Install Dependencies
make install-backend
make install-frontend

# 2. Configure Your Environment
make create-env
# Now, edit the new .env file with your credentials

# 3. Launch Services & Database
make dev-services # Starts Postgres & Redis
make db-setup    # Initializes the database

# 4. Run the Application
make dev

</details>
Access Points
 * Frontend Application: http://localhost:3000 🖥️
 * Backend API: http://localhost:8000 ⚙️
 * Interactive API Docs: http://localhost:8000/docs 📚
📂 Project Structure
The repository is neatly organized into modules for the backend, frontend, and infrastructure. This clean separation makes the codebase easy to navigate and scale.
<details>
<summary><strong>▶️ View Directory Tree</strong></summary>
LLM-powered-document-intelligence-system/
├── backend/            # Python/FastAPI application
│   ├── main.py         # API application entry point
│   ├── llm_service.py  # Core logic for LangChain & Azure OpenAI
│   └── ...
├── frontend/           # React/TypeScript application
│   ├── src/
│   ├── components/     # Reusable UI components
│   └── ...
├── docker-compose.yml  # Defines services, networks, and volumes
├── Dockerfile.backend  # Build instructions for the FastAPI app
├── Dockerfile.frontend # Build instructions for the React app
├── Makefile            # Automation scripts for setup and operations
└── .env.example        # Template for environment variables

</details>
⚙️ Configuration
All configuration is handled through environment variables. Just copy .env.example to .env and fill in your details.
# Azure AI Configuration
AZURE_OPENAI_API_KEY=your_openai_key
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_DOCUMENT_INTELLIGENCE_KEY=your_document_intelligence_key

# Database & Redis
DATABASE_URL=postgresql://user:password@localhost:5432/llm_docs
REDIS_URL=redis://localhost:6379

# Security
JWT_SECRET_KEY=your_super_secure_key_here

🛠️ Development & Operations
We've included a Makefile to simplify common development tasks.
| Command | Description |
|---|---|
| make install-backend | Installs Python dependencies. |
| make install-frontend | Installs Node.js dependencies. |
| make dev | Starts all development servers. |
| make build | Builds production-ready Docker images. |
| make test | Runs the complete test suite. |
| make lint | Lints and formats the codebase. |
| make security-scan | Runs security vulnerability checks. |
🤝 Contributing
We welcome and appreciate contributions! Please see our Contributing Guidelines for more details on how to get started.
How to Contribute
 * Fork the project.
 * Create your feature branch (git checkout -b feature/NewCoolThing).
 * Commit your changes (git commit -m 'Add NewCoolThing').
 * Push to the branch (git push origin feature/NewCoolThing).
 * Open a Pull Request.
📜 License
This project is licensed under the MIT License. See the LICENSE file for details.
<div align="center">
⭐ Star this repo if you find it useful!
Made with ❤️ by the Document Intelligence Team
</div>
