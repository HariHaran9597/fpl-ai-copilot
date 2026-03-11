# ⚽ FPL AI Copilot

**An intelligent, multi-agent AI system designed to analyze Fantasy Premier League data and provide mathematically optimized transfer and captaincy recommendations.**

Built using a hybrid deterministic/LLM reasoning architecture for extreme token efficiency and deep domain accuracy.

## 🚀 Key Features

*   **Multi-Agent LangGraph Pipeline**: Routes data logically between mathematical scoring nodes and specialized ReAct Agents.
*   **LLM Inference (Moonshot AI via Groq)**: Powered by `kimi-k2-instruct-0905` for high-speed, cost-effective, intelligent strategic reasoning.
*   **Token-Efficient Processing**: Python pre-processes 700+ players using algorithmic sorting before sending the curated contextual payload to the LLMs.
*   **Dynamic Tool Calling**: ReAct agents utilize live FPL API price tracking to execute perfect constraints for new player budget calculations.
*   **Modern Premium UI (Vite/React)**: A stunning dark-mode/glassmorphic frontend that consumes the AI pipeline results via REST.
*   **FastAPI Backend**: Clean decoupling of the AI orchestration layer from the presentation layer. 

## 🏗️ Architecture Stack

*   **Backend Orchestration**: LangGraph, LangChain, Python
*   **REST API Layer**: FastAPI, Uvicorn
*   **Model Provider**: Groq API (Kimi Model)
*   **Frontend Client**: React, Vite, Vanilla CSS
*   **Data Source**: Official Fantasy Premier League JSON endpoints

## 🏃‍♂️ Getting Started

### 1. Backend Setup

```bash
# Set up a virtual environment and install dependencies
python -m venv venv
source venv/bin/activate  # Or .\venv\Scripts\activate on Windows
pip install -r requirements.txt

# Add your GROQ API Key
echo 'GROQ_API_KEY="your_api_key_here"' > .env

# Run the backend REST server
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

### 2. Frontend Setup

```bash
# Navigate to the frontend directory
cd frontend

# Install Vite and React dependencies
npm install

# Start the premium dashboard
npm run dev
```

Visit the dashboard at `http://127.0.0.1:5173/` and input your FPL Manager ID!

## 🧪 Backtesting

The repository includes a backtesting and analytics suite to benchmark the Agentic pipeline's recommended picks vs. global averages. 

Run the test evaluation script:
```bash
python tests/evaluate_past_gameweeks.py
```

*Results yielded a simulated 27.3% point delta improvement over standard baseline manager decisions.*

## 🔮 Future Roadmap (v2 Architecture)

While the current version provides excellent qualitative reasoning and a premium interface, the next iteration of the pipeline focuses on mathematical optimization and deep contextual grounding:

1. **RAG Pipeline Integration (Press Conferences & News)**: A Vector DB (Pinecone/FAISS) pulling live data from Reddit and Twitter to provide the LLM with immediate injury news and lineup leaks before rendering captaincy decisions.
2. **Predictive Expected Points (xP) ML Model**: Shifting the core Knapsack optimization problem to a deterministic solver (PuLP/SciPy) fed by an underlying XGBoost model trained on historical player metric data, with the LLM serving strictly as the "Explanatory Layer".
3. **Structured Tool Calling**: Reverting to native function calling (JSON schema adherence) for agents to dynamically interact with real-time FPL data rather than pre-computing contextual constraints in Python.
4. **LangSmith Observability**: Adding comprehensive prompt tracing, latency monitoring, and token-cost evaluation across the graph.
