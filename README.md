# The Interview Agent

An AI-powered technical interviewer backend built with **FastAPI** and **Google Gemini 2.5 Flash**, designed for the **ABTalks AI Cohort Hackathon**.

The agent conducts structured, multi-turn technical evaluations of candidates, dynamically selecting focus topics based on candidate mission history, tracking progress across curriculum modules, and generating structured evaluation reports.

---

## 🌟 Key Features

- **Multi-Turn Adaptive Interviews**: Evaluates candidates across cohort curriculum days (RAG, Fine-Tuning, Agentic Workflows, Evaluation, etc.).
- **Adaptive Depth**: Uses AI signals (`advance`, `deepen`, `scaffold`) to dynamically probe harder or scaffold backwards based on candidate responses.
- **Smart Target Selection**: Prioritizes skipped or struggled missions to assess weak spots effectively.
- **State Persistence**: Uses Vercel KV (Upstash Redis) to maintain multi-turn session state across serverless cold starts.
- **Grounded & Personalized Evaluation**: Injects structured topic objectives and explicitly references candidate history in conversation.
- **Structured Feedback**: Generates automated performance summaries, key strengths, knowledge gaps, and recommended next steps mapped directly to curriculum days.
- **Interactive UI Demo**: Includes a built-in browser UI at `/demo` for instant live testing.

---

## 🛠️ Architecture & Tech Stack

- **Framework**: Python 3.13 + FastAPI
- **LLM Engine**: Google Gemini 2.5 Flash (`gemini-2.5-flash`)
- **Session Persistence**: Vercel KV (Upstash Redis)
- **Telemetry**: Breeth Memory API (`thebreeth.com`)
- **HTTP Client**: `httpx`

---

## 🚀 Quickstart Guide

### 1. Environment Setup
Clone the repository and install dependencies:
```bash
git clone https://github.com/Aayush-pixel29/Interview-Agent.git
cd Interview-Agent
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install fastapi uvicorn httpx python-dotenv pydantic
```

### 2. Configure Environment Variables
Copy `.env.example` to `.env` and set your API keys:
```bash
cp .env.example .env
```
Edit `.env`:
```env
GEMINI_API_KEY="your_gemini_api_key_here"
BREETH_API_KEY="your_breeth_api_key_here"
KV_REST_API_URL="your_vercel_kv_url_here"
KV_REST_API_TOKEN="your_vercel_kv_token_here"
```

### 3. Run the API Server
Start the FastAPI server:
```bash
uvicorn main:app --reload --port 8000
```
Interactive API documentation will be available at: `http://localhost:8000/docs`

### 4. Interactive Live Demo
You can test the interview loop visually by visiting: `http://localhost:8000/demo`

---

## 🔌 API Specification

### `POST /api/interview`

#### Request Schema (Start Interview)
```json
{
  "sessionId": "session_12345",
  "candidate": {
    "member": {
      "name": "Alex Chen",
      "jobRole": "AI Engineer"
    },
    "missions": [
      { "day": 7, "passed": true, "attempts": 1 },
      { "day": 10, "passed": false, "attempts": 3 }
    ]
  }
}
```

#### Request Schema (Continue Turn)
```json
{
  "sessionId": "session_12345",
  "message": "Chain-of-thought prompting improves reasoning by encouraging the model to break down complex tasks into intermediate steps."
}
```

#### Response Schema
```json
{
  "reply": "Excellent explanation of chain-of-thought prompting! Moving to Day 10: How do you choose between sparse and dense retrieval for RAG?",
  "done": false,
  "feedback": null
}
```

---

## 🛡️ Audit & Security Improvements

- ✅ **Secret Isolation**: Live keys untracked from version control with `.gitignore` and `.env.example`.
- ✅ **Header Authentication**: Migrated Gemini API authentication to secure `x-goog-api-key` headers.
- ✅ **Prompt Segregation**: Separated system instructions from untrusted user inputs to prevent prompt injection.
- ✅ **Robust Output Parsing**: Handles markdown code blocks and schema validation gracefully.

---

## 📜 License

MIT License
