# R.E.I (Retrieval & Execution Interface)

REI is an advanced, dual-stream diagnostic assistant designed to bridge the gap between static knowledge and active pipeline execution. By balancing semantic memory vectorization (Retrieval) with dynamic matrix orchestration (Execution), REI provides a highly precise, context-aware interface for data-driven tasks.

## Highlights
- **Dual-Stream Architecture:** Integrates RAG (Retrieval-Augmented Generation) with dynamic tool execution.
- **Adaptive Personas:** Context-aware responses via configurable personality profiles (Technical, Casual, Friendly, Minimalist).
- **Intelligent Fallback:** Automated Google Search Grounding for queries outside the local knowledge base.
- **Observability:** Built-in diagnostic telemetry to track memory usage and pipeline routing.

## Tech Stack
- **Framework:** FastAPI
- **LLM:** Google Gemini 3.1 Flash / 3.5 Flash
- **Memory:** SQLite-based vector & history management
- **Orchestration:** Agentic routing logic
- **Frontend:** Next.JS (Typescript)

## Core Agentic Tracks
- RAG: Semantic search for localized document retrieval.
- TOOL: Execution of data slicing, correlation analysis, and categorical distribution.
- HYBRID: Integrated retrieval and analysis for complex queries.
- FALLBACK: Automated web-grounding via Google Search.



## Quick Start
A. For Backend
1. **Clone the repo:**
   ```bash
   git clone [https://github.com/Avidrei/REI.git](https://github.com/Avidrei/REI.git)
   cd REI
   cd backend

2. **Create virtual environment**
   ```bash
   python -m venv venv

1. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   
2. **Create .env file**
   ```bash
   GEMINI_API_KEY="your_api_key_here"

3. **Launch Backend**
   ```bash
   uvicorn main:app --reload

B. For Frontend
1. **Change directory to frontend**
   ```bash
   cd frontend

2. **Install dependencies**
   ```bash
   npm i

3. **Launch Next.JS frontend**
   ```bash
   npm run dev


  
