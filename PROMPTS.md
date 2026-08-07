# AI Interview Agent - System Architecture & Prompt Design Log

## 1. System Architecture
- **Framework**: FastAPI + Python 3.13
- **LLM Reasoning**: Google Gemini 2.5 Flash (`gemini-2.5-flash`) via direct REST API with native `system_instruction` support and header-based authentication.
- **Memory & State**: Breeth Persistent Memory Graph (`thebreeth.com`) + In-Memory Fallback Engine.

## 2. Verification Strategy & Audit Compliance
1. **Dynamic Target Selection**: Candidate mission metrics (skipped, struggled, passed) automatically map target curriculum days for focus evaluation.
2. **Curriculum-Grounded Prompts**: Questions are constructed using structured cohort topic objectives loaded from `curriculum.json`.
3. **8-Question & 4-Day Progress Enforcement**: Monitored turn-by-turn in `interview_engine.py`.
4. **Structured Feedback Generation**: JSON response mode combined with robust markdown backtick stripping and Pydantic validation fallback.
5. **Security & Prompt Injection Protection**: System instructions are segregated from candidate responses, and secrets are excluded from version control via `.gitignore`.