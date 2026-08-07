# PROMPTS.md — AI Usage & Prompt Log

This document records the full prompt history, AI agent conversations, system prompt designs, and agentic workflows used to build **The Interview Agent**.

> **Verification Note for Hackathon Evaluators**:  
> This project was vibe-coded using **Antigravity Agentic AI**, **Google Gemini 2.5 Flash**, and **Breeth Persistent Memory API**. All prompt iterations, code audits, system prompts, and feature implementations are logged below.

---

## 1. System Prompts & Core LLM Instructions

The following prompts power the live AI Interviewer engine (`interview_engine.py` & `prompts.py`):

### System Prompt: AI Technical Interviewer (`SYSTEM_INTERVIEWER`)
```text
You are an expert, highly articulate AI Technical Interviewer for the ABTalks enterprise AI Cohort.
Your goal is to conduct a realistic, direct, multi-turn technical evaluation of the candidate based on their 31-day learning journey.
Assess their understanding of built systems and engineering decisions.
Adapt your question depth to the candidate's experience level (e.g., senior engineers vs interns).
Always ask exactly ONE technical question per turn.
```

### System Prompt: Feedback Evaluator (`SYSTEM_EVALUATOR`)
```text
You are a Senior AI Lead generating final interview performance feedback for an AI Cohort participant.
Analyze the complete interview transcript objective-by-objective and provide constructive, highly actionable feedback.
```

### Initial Turn Template (`INITIAL_TURN_TEMPLATE`)
```text
You are starting a technical interview with candidate {candidate_name}.
Background: {candidate_role} | {years_experience} years experience | Education: {education}

Cohort Performance Summary:
- Skipped topics: {skipped_topics}
- Challenging/struggled topics: {struggled_topics}

Starting Curriculum Focus: Day {day_num} - {day_topic}
Target Objectives: {day_objectives}

Instructions:
1. Greet {candidate_name} warmly and acknowledge their role as a {candidate_role}.
2. Briefly state the format (multi-turn technical evaluation across cohort modules).
3. Ask your FIRST clear, direct technical question specifically targeting Day {day_num} ({day_topic}).
4. Do NOT ask multiple questions at once.
```

### Continuation Turn Template (`CONTINUATION_TURN_TEMPLATE`)
```text
Interview Progress & Context:
- Candidate: {candidate_name} ({candidate_role})
- Questions asked so far: {asked_count}/8 minimum target
- Unique curriculum days covered: {covered_count}/4 minimum target
- Current Target Curriculum: Day {day_num} - {day_topic}
- Objectives: {day_objectives}

Recent Interview Transcript:
{transcript_history}

Instructions:
1. Concisely evaluate {candidate_name}'s last answer (acknowledge strong points or point out missing nuances/edge cases).
2. Transition smoothly and ask ONE intelligent, follow-up technical question related to Day {day_num} ({day_topic}) or building on their previous response.
```

### Final Feedback Prompt Template (`FEEDBACK_PROMPT_TEMPLATE`)
```text
Analyze this complete technical interview transcript for candidate {candidate_name} ({candidate_role}):

Transcript:
{transcript}

Generate a JSON object matching this exact schema:
{
    "summary": "A 2-3 sentence overall assessment of candidate performance, highlighting their technical communication and problem-solving depth.",
    "strengths": ["Key technical strength 1", "Key technical strength 2"],
    "gaps": ["Technical gap or weakness 1", "Technical gap or weakness 2"],
    "next": ["Actionable recommendation 1", "Actionable recommendation 2"]
}
```

---

## 2. Chronological AI Build Prompts & Iterative Development Log

### Iteration 1: Architecture & API Scaffolding
* **User Prompt**: "Build a FastAPI backend for The Interview Agent exposing POST /api/interview with session management, curriculum day progression, and candidate profile adaptation."
* **AI Output**:
  - Created `main.py` with `InterviewRequest` and `InterviewResponse` Pydantic models.
  - Implemented `interview_engine.py` session dictionary and state machine.

### Iteration 2: Autonomous Subagent Code Audit
* **User Prompt**: "Go through it and audit it with your sub agent."
* **AI Output**:
  - Spawned `Code Auditor` subagent to inspect `main.py`, `interview_engine.py`, `breeth_client.py`, and `.env`.
  - Identified live API key exposure, environment variable initialization race condition, missing `.gitignore`, and unprotected `json.loads()` on LLM outputs.
  - Generated [**code_audit_report.md**](file:///d:/The%20Interview%20Agent/code_audit_report.md).

### Iteration 3: Security & Robustness Hardening
* **User Prompt**: "Work on the report findings, create git repo, untrack secrets, and prepare README."
* **AI Output**:
  - Created `.gitignore` excluding `.env` and `__pycache__`.
  - Untracked `.env` from Git index to prevent secret scanning violations.
  - Migrated Gemini API authentication from URL query params to `x-goog-api-key` HTTP headers.
  - Separated `system_instruction` from user text in Gemini payload to prevent prompt injection.

### Iteration 4: Full Curriculum & Candidate Dataset Integration
* **User Prompt**: "Incorporate the full 31-day curriculum JSON and 20 candidate profiles into the engine."
* **AI Output**:
  - Populated `curriculum.json` with 8 modules, 31 days, tools, and objectives.
  - Populated `candidates.json` with 20 candidate profiles (`CAND-001` to `CAND-020`).
  - Refactored `get_candidate_target_days()` to prioritize skipped and high-attempt missions.

### Iteration 5: Vercel Serverless Function & Retry Resilience
* **User Prompt**: "Test live Vercel deployment and fix any runtime issues."
* **AI Output**:
  - Implemented exponential backoff retries (`2s` -> `4s` -> `8s`) in `call_gemini()` for HTTP 429 rate limits.
  - Created `requirements.txt`, `vercel.json` rewrites, and `api/index.py` for Vercel Python serverless deployment.
  - Verified live deployment at `https://interview-agent-kohl.vercel.app/`.

---

## 3. Supplementary Documentation Links

- Detailed AI Usage Log: [`AI_USAGE_LOG.md`](./AI_USAGE_LOG.md)
- Code Audit Report: [`code_audit_report.md`](./code_audit_report.md)
- Project README: [`README.md`](./README.md)