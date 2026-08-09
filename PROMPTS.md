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
3. Explicitly mention WHY you are starting with this topic (e.g., "I noticed you skipped...", "You had some challenges with...", or "Since you completed...").
4. Ask your FIRST clear, direct technical question specifically targeting Day {day_num} ({day_topic}).
5. Do NOT ask multiple questions at once.

Generate a JSON object matching this exact schema:
{
    "reply": "Your complete spoken response and technical question here",
    "signal": "advance"
}
```

### Continuation Turn Template (`CONTINUATION_TURN_TEMPLATE`)
```text
Interview Progress & Context:
- Candidate: {candidate_name} ({candidate_role})
- Questions asked so far: {asked_count}/8 minimum target
- Unique curriculum days covered: {covered_count}/4 minimum target

Topics:
- CURRENT Topic: Day {current_day} - {current_topic} (Objectives: {current_objectives})
- NEXT Topic: Day {next_day} - {next_topic} (Objectives: {next_objectives})

Recent Interview Transcript:
{transcript_history}

Instructions:
1. Concisely evaluate {candidate_name}'s last answer (acknowledge strong points or point out missing nuances/edge cases).
2. Choose the appropriate signal based on their answer:
   - "advance": If they answered well and you are moving to the NEXT Topic (Day {next_day}).
   - "deepen": If they answered exceptionally well and you want to probe deeper into the CURRENT Topic (Day {current_day}).
   - "scaffold": If they struggled and you need to ask an easier, foundational question on the CURRENT Topic (Day {current_day}).
3. Explicitly mention WHY you are making this move (e.g. "That's a great answer, let's go a bit deeper into..." or "Since you have a good grasp of this, let's move on to...").
4. Transition smoothly and ask ONE intelligent, follow-up technical question based on the topic determined by your signal.

Generate a JSON object matching this exact schema:
{
    "reply": "Your complete spoken evaluation, transition, and next technical question here",
    "signal": "advance" | "deepen" | "scaffold"
}
```

### Final Feedback Prompt Template (`FEEDBACK_PROMPT_TEMPLATE`)
```text
Analyze this complete technical interview transcript for candidate {candidate_name} ({candidate_role}):

Transcript:
{transcript}

Generate a JSON object matching this exact schema:
{
    "summary": "A 2-3 sentence overall assessment of candidate performance, highlighting their technical communication and problem-solving depth.",
    "strengths": ["Key technical strength 1 (explicitly mention which Day/topic this relates to)", "Key technical strength 2 (explicitly mention which Day/topic this relates to)"],
    "gaps": ["Technical gap or weakness 1 (explicitly mention which Day/topic this relates to)", "Technical gap or weakness 2 (explicitly mention which Day/topic this relates to)"],
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

### Iteration 6: Final Polish - Adaptive Depth & Vercel KV
* **User Prompt**: "Locking in Interview Agent. Fix the in-memory session bug... make personalization visible... add adaptive depth... add demo page."
* **AI Output**:
  - Integrated **Vercel KV (Upstash Redis)** into `interview_engine.py` to fix serverless cold-start data loss (P0).
  - Modified prompts to require **JSON responses** to support an `advance`, `deepen`, or `scaffold` signal.
  - Restructured the engine to support **Adaptive Depth**: LLM now decides whether to push forward to a new topic or drill down into the current topic based on the candidate's answer quality.
  - Added explicit prompt instructions for curriculum-mapped feedback in `FEEDBACK_PROMPT_TEMPLATE`.
  - Built an interactive **HTML demo UI** hosted on `GET /demo` in `main.py` for immediate judge testing.

---

## 3. Supplementary Documentation Links

- Detailed AI Usage Log: [`AI_USAGE_LOG.md`](./AI_USAGE_LOG.md)
- Code Audit Report: [`code_audit_report.md`](./code_audit_report.md)
- Project README: [`README.md`](./README.md)