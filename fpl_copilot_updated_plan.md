# FPL AI Copilot — Complete Implementation Plan (Updated with Feedback)

> **Goal:** Multi-agent AI system using LangGraph that analyzes your Fantasy Premier League team and recommends captains, transfers, and strategy using live FPL API data.
> 
> **Resume line:** GenAI + Hybrid Agent Pipeline + LangGraph + Tool Calling + API Orchestration + Backtested

---

## System Architecture

```mermaid
graph TD
    A[User enters FPL Team ID] --> B[LangGraph Orchestrator]
    B --> C[Data Collector Node]
    C -->|Try/Except & Retry| D[FPL API]
    D --> C
    C --> E[State: Data & Budgets]
    E --> F[Fixture Analyst Node]
    E --> G[Form Analyst Node]
    F --> H[State: Fixture Scores]
    G --> I[State: Form Scores]
    H --> J[Captain Selector Agent]
    I --> J
    H --> K[Transfer Recommender Agent]
    I --> K
    J --> L[State: Captain Picks]
    K --> M[State: Transfer Suggestions]
    L --> N[Report Generator Agent]
    M --> N
    N --> O[Final Gameweek Report]
    O --> P[FastAPI Backend REST API]
    P --> Q[React/Vite Frontend (Vercel)]
```

---

## The Hybrid AI Pipeline
*   **Nodes (Deterministic Python):** Data Collector, Fixture Analyst, Form Analyst. (Fast, no token cost, 100% reliable).
*   **Agents (LLM Reasoning):** Captain Selector, Transfer Recommender, Report Generator. (Intelligent, creative, tool-assisted).

---

## Step-by-Step Implementation

### Step 1: `src/fpl_client.py` — Resilient FPL API Wrapper
*   **What it does:** Fetches data. Centralizes caching so we don't spam the API.
*   **Feedback Applied:** Added `try/except` logic for when FPL servers crash before deadline to return friendly errors.
*   **Endpoints:** `bootstrap-static`, `fixtures`, `element-summary`, `entry`, `event/picks`, `transfers`.

### Step 2: `src/state.py` — Shared Graph State
*   **What it does:** Defines the input, intermediate states, and outputs.
*   **Feedback Applied (Token Efficiency):** We do not pass the full `all_players` list of 700+ players directly to the LLMs. Instead, the deterministic nodes pre-filter and slice this list down to a `top_20_targets` list to keep inference fast and cheap.

### Step 3: `src/tools.py` — LangChain ReAct Tools
*   **What it does:** Wraps logic into functions that the Transfer Agent can use.
*   **Feedback Applied (Budget Reality):** Added a new tool:
    *   `find_affordable_replacements(position: str, selling_player_id: int, bank_balance: float)` -> Calculates exact selling price of a current squad player and returns players under `selling_price + bank_balance`.
*   **Standard Tools:** `get_player_stats`, `get_upcoming_fixtures`, `get_injury_flagged_players`.

### Step 4: `src/nodes/data_node.py` — Data Collection
*   **What it does:** Uses `fpl_client` to fill state with fixtures, user picks, and budget.
*   **Feedback Applied:** Pulls the *exact selling price* of players from the FPL API (to account for the 50% profit rule), passing it cleanly into the state for the Transfer Agent.

### Step 5: `src/nodes/fixture_node.py` & `src/nodes/form_node.py` — Math Nodes
*   **What they do:** Run standard math computations across the 700+ players list to output `fixture_scores` and `form_scores` for the active state. No LLMs used here.

### Step 6: `src/agents/captain_agent.py` — Captain Selection
*   **What it does:** Takes the user's starting 11, cross-references with `fixture_scores` and `form_scores`, and hits a Groq LLM (LLaMA-3.1-8b) to reason out the best 3 captain choices.

### Step 7: `src/agents/transfer_agent.py` — Transfer Recommender
*   **What it does:** ReAct-pattern agent using Groq. Uses the `find_affordable_replacements` tool when identifying a weak link in the squad. Provides safe, mathematically valid transfer suggestions.

### Step 8: `src/agents/report_agent.py` — Report Generator
*   **What it does:** LLM aggregates the output strings from the Captain and Transfer agents, applies markdown formatting, and generates the final gameweek briefing report.

### Step 9: `src/graph.py` — LangGraph Orchestrator
*   **What it does:** Wires the sequence. Runs Fixture and Form nodes concurrently. Followed by Captain and Transfer agents concurrently.

### Step 10: `tests/evaluate_past_gameweeks.py` — Backtesting & Evaluation
*   **What it does:** Evaluates the AI's past performance setup.
*   **Feedback Applied (The "Wow" Factor):** Iterates over Gameweeks 1-10 of the current season and compares the AI's captain picks against the global average score. Used as a huge flex on your resume.

### Step 11: `app/main.py` — FastAPI Backend
*   **What it does:** The API layer. Exposes REST endpoints to trigger the pipeline and fetch the gameweek report structure.
*   **Feedback Applied (Architecture):** Separates the backend logic from the frontend to allow a premium customized React UI.

### Step 12: `frontend/` — React + Vite Dashboard
*   **What it does:** The presentation layer. A modern, glassmorphic UI utilizing Tailwind CSS (or Vanilla CSS) with a technical football aesthetic.
*   **Feedback Applied (User Experience):** Deployed to Vercel for a buttery-smooth client-side feel. Contains visual representations of the pitch, animated radar charts, and elegant error handling for FPL API rate limits downtime.

---

## Build Checklist (12-15 Hours)

### Phase 1: API & Data Foundation (Day 1)
- [ ] Create folder, venv, `requirements.txt`.
- [ ] Implement `fpl_client.py` with caching and `try/except` for downtime handling.
- [ ] Define `FPLState` in `state.py`.
- [ ] Implement robust budget/selling price calculation tools in `tools.py`.

### Phase 2: Nodes & Agents (Day 2)
- [ ] Implement `data_node.py`, `fixture_node.py`, and `form_node.py`.
- [ ] Verify state is filtering out the massive `all_players` list before hitting agents.
- [ ] Implement `captain_agent.py` and test the prompt structure.
- [ ] Implement `transfer_agent.py` and test ReAct tool usage (`find_affordable_replacements`).
- [ ] Implement `report_agent.py`.

### Phase 3: Graph Logic & Backtesting (Day 3)
- [ ] Wire everything up in `graph.py`.
- [ ] Create `evaluate_past_gameweeks.py`. Run a simulation for 5 weeks.
- [ ] Log the performance vs. Average Manager points to use on your resume.

### Phase 4: UI & Deployment (Day 3)
- [ ] Initialize frontend with `npm create vite@latest frontend -- --template react` and configure styling.
- [ ] Build `main.py` (FastAPI) to expose endpoints to the frontend.
- [ ] Add graceful UI error states for when FPL API crashes or rate limits occur.
- [ ] Deploy the FastAPI backend to Render and the React UI to Vercel.
- [ ] Write a professional `README.md` highlighting the full-stack AI architecture.
