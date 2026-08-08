import os
import json
import httpx
import asyncio
import logging
from typing import Dict, Any, Tuple, List, Optional
from dotenv import load_dotenv

# Ensure environment variables are loaded at startup
load_dotenv()

from breeth_client import sync_to_breeth
import prompts

logger = logging.getLogger(__name__)

KV_REST_API_URL = os.getenv("KV_REST_API_URL")
KV_REST_API_TOKEN = os.getenv("KV_REST_API_TOKEN")

# Base directory for resolving file resources reliably in serverless environments (Vercel)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CURRICULUM_PATH = os.path.join(BASE_DIR, "curriculum.json")

# In-memory session store fallback
SESSIONS: Dict[str, Dict[str, Any]] = {}

async def get_session(session_id: str) -> Optional[Dict[str, Any]]:
    if KV_REST_API_URL and KV_REST_API_TOKEN:
        url = f"{KV_REST_API_URL.rstrip('/')}/get/{session_id}"
        headers = {"Authorization": f"Bearer {KV_REST_API_TOKEN}"}
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(url, headers=headers)
                if resp.status_code == 200:
                    data = resp.json().get("result")
                    if data:
                        return json.loads(data)
        except Exception as e:
            logger.error(f"Error fetching session from KV: {e}")
    return SESSIONS.get(session_id)

async def save_session(session_id: str, session_data: Dict[str, Any]):
    SESSIONS[session_id] = session_data
    if KV_REST_API_URL and KV_REST_API_TOKEN:
        url = f"{KV_REST_API_URL.rstrip('/')}/set/{session_id}"
        headers = {"Authorization": f"Bearer {KV_REST_API_TOKEN}"}
        try:
            async with httpx.AsyncClient() as client:
                await client.post(url, headers=headers, json=json.dumps(session_data))
        except Exception as e:
            logger.error(f"Error saving session to KV: {e}")

# Load curriculum data at startup
try:
    with open(CURRICULUM_PATH, "r", encoding="utf-8") as f:
        CURRICULUM_DATA = json.load(f)
except Exception as err:
    logger.warning(f"Could not load curriculum.json from {CURRICULUM_PATH}: {err}")
    CURRICULUM_DATA = {"days": []}

def get_day_info(day_num: int) -> Tuple[str, str]:
    """Retrieve topic title and objectives string for a given curriculum day."""
    days_list = CURRICULUM_DATA.get("days", [])
    for d in days_list:
        if d.get("day") == day_num:
            topic = d.get("title", f"Day {day_num} Topics")
            objs = ", ".join(d.get("objectives", []))
            return topic, objs
    return f"Day {day_num} Concepts", "Core AI engineering fundamentals"

async def call_gemini(system_prompt: str, user_prompt: str, response_json: bool = False) -> str:
    """
    Helper to query Gemini REST API safely using header authentication and system_instruction.
    Includes exponential backoff retry logic for 429 Rate Limit and 5xx transient server errors.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY is not set in environment variables.")

    url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent"
    
    headers = {
        "x-goog-api-key": api_key,
        "Content-Type": "application/json"
    }

    payload: Dict[str, Any] = {
        "system_instruction": {
            "parts": [{"text": system_prompt}]
        },
        "contents": [
            {"role": "user", "parts": [{"text": user_prompt}]}
        ],
        "generationConfig": {
            "temperature": 0.7
        }
    }
    
    if response_json:
        payload["generationConfig"]["responseMimeType"] = "application/json"

    max_retries = 4
    delay = 2.0
    
    async with httpx.AsyncClient(timeout=35.0) as client:
        for attempt in range(max_retries):
            try:
                res = await client.post(url, json=payload, headers=headers)
                res.raise_for_status()
                data = res.json()
                return data["candidates"][0]["content"]["parts"][0]["text"]
            except httpx.HTTPStatusError as e:
                if e.response.status_code in [429, 500, 502, 503, 504] and attempt < max_retries - 1:
                    logger.warning(f"Gemini API status {e.response.status_code}. Retrying in {delay}s... (Attempt {attempt+1}/{max_retries})")
                    await asyncio.sleep(delay)
                    delay *= 2.0
                else:
                    raise e
            except (httpx.RequestError, asyncio.TimeoutError) as e:
                if attempt < max_retries - 1:
                    logger.warning(f"Gemini API request error: {e}. Retrying in {delay}s... (Attempt {attempt+1}/{max_retries})")
                    await asyncio.sleep(delay)
                    delay *= 2.0
                else:
                    raise e
                    
    raise RuntimeError("Failed to obtain response from Gemini API after retries.")

def get_candidate_target_days(candidate: Dict[str, Any]) -> List[int]:
    """Selects 4+ curriculum days based on candidate's completed/skipped missions."""
    missions = candidate.get("missions", [])
    
    skipped_days = [m["day"] for m in missions if m.get("skipped")]
    struggled_days = [m["day"] for m in missions if m.get("attempts", 0) >= 3 or not m.get("passed", True)]
    passed_days = [m["day"] for m in missions if m.get("passed")]
    
    target_days: List[int] = []
    for day in skipped_days + struggled_days + passed_days:
        if day not in target_days:
            target_days.append(day)
            
    # Fallback default days if candidate mission list is short
    for fallback in [7, 8, 10, 12, 16, 22, 23, 28]:
        if len(target_days) < 6 and fallback not in target_days:
            target_days.append(fallback)
            
    return target_days

async def handle_interview_turn(session_id: str, candidate_data: Optional[Dict[str, Any]] = None, user_message: Optional[str] = None) -> Tuple[str, bool, Optional[Dict[str, Any]]]:
    # 1. INITIALIZE NEW INTERVIEW SESSION
    if candidate_data:
        target_days = get_candidate_target_days(candidate_data)
        start_day = target_days[0] if target_days else 7
        
        session_data = {
            "candidate": candidate_data,
            "target_days": target_days,
            "asked_questions": 0,
            "covered_days": [],
            "history": [],
            "current_day_index": 0
        }
        await save_session(session_id, session_data)
        
        member = candidate_data.get("member", {})
        c_name = member.get("name", "Candidate")
        c_role = member.get("jobRole", "AI Engineer")
        c_exp = member.get("yearsExperience", 0)
        c_edu = member.get("education", "Computer Science")
        
        missions = candidate_data.get("missions", [])
        skipped_titles = [m.get("title", f"Day {m['day']}") for m in missions if m.get("skipped")]
        struggled_titles = [m.get("title", f"Day {m['day']}") for m in missions if m.get("attempts", 0) >= 3 or not m.get("passed", True)]
        
        day_topic, day_objs = get_day_info(start_day)
        
        initial_prompt = prompts.INITIAL_TURN_TEMPLATE.format(
            candidate_name=c_name,
            candidate_role=c_role,
            years_experience=c_exp,
            education=c_edu,
            skipped_topics=", ".join(skipped_titles) if skipped_titles else "None",
            struggled_topics=", ".join(struggled_titles) if struggled_titles else "None",
            day_num=start_day,
            day_topic=day_topic,
            day_objectives=day_objs
        )
        
        reply_raw = await call_gemini(prompts.SYSTEM_INTERVIEWER, initial_prompt, response_json=True)
        try:
            reply_json = json.loads(reply_raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip())
            reply = reply_json.get("reply", reply_raw)
        except Exception:
            reply = reply_raw
        
        session_data["asked_questions"] = 1
        if start_day not in session_data["covered_days"]:
            session_data["covered_days"].append(start_day)
        session_data["history"].append({"role": "interviewer", "text": reply})
        
        await save_session(session_id, session_data)
        
        # Async memory sync to Breeth
        await sync_to_breeth(session_id, "init", {"candidate": c_name, "role": c_role})
        
        return reply, False, None

    # 2. CONTINUATION TURN
    session = await get_session(session_id)
    if not session:
        return "Session expired or not found. Please restart the interview.", True, None

    # Save candidate response
    session["history"].append({"role": "candidate", "text": user_message})
    await sync_to_breeth(session_id, "user_turn", {"message": user_message})

    asked_cnt = session["asked_questions"]
    covered_days = session["covered_days"]
    target_days = session["target_days"]

    # Check if target criteria met (at least 8 questions and 4 covered days)
    if asked_cnt >= 8 and len(covered_days) >= 4:
        member = session['candidate'].get('member', {})
        c_name = member.get('name', 'Candidate')
        c_role = member.get('jobRole', 'AI Engineer')
        
        feedback_prompt = prompts.FEEDBACK_PROMPT_TEMPLATE.format(
            candidate_name=c_name,
            candidate_role=c_role,
            transcript=json.dumps(session['history'], indent=2)
        )
        
        try:
            feedback_raw = await call_gemini(
                prompts.SYSTEM_EVALUATOR,
                feedback_prompt,
                response_json=True
            )
            
            # Robust JSON cleaning for markdown backticks
            clean_json_str = feedback_raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
            feedback_json = json.loads(clean_json_str)
        except Exception as e:
            logger.error(f"Fallback triggered due to feedback error: {e}")
            feedback_json = {
                "summary": "Thank you for participating. We encountered an issue generating your detailed automated feedback, but your responses have been successfully recorded.",
                "strengths": ["Completed the interview requirements"],
                "gaps": ["Detailed feedback unavailable due to a processing error"],
                "next": ["Await manual review of your interview transcript"]
            }
        
        final_reply = "Thank you for completing the technical interview! I have evaluated your responses across all cohort modules, and your structured feedback report is ready below."
        
        await sync_to_breeth(session_id, "complete", feedback_json)
        
        return final_reply, True, feedback_json

    # Adaptive Depth: Pass current day and next day to LLM
    current_day_index = session.get("current_day_index", 0)
    current_day = target_days[current_day_index] if target_days else 7
    next_day_index = (current_day_index + 1) % len(target_days) if target_days else 0
    next_day = target_days[next_day_index] if target_days else 7
    
    current_topic, current_objs = get_day_info(current_day)
    next_topic, next_objs = get_day_info(next_day)

    member = session['candidate'].get('member', {})
    c_name = member.get('name', 'Candidate')
    c_role = member.get('jobRole', 'AI Engineer')

    interviewer_prompt = prompts.CONTINUATION_TURN_TEMPLATE.format(
        candidate_name=c_name,
        candidate_role=c_role,
        asked_count=asked_cnt,
        covered_count=len(covered_days),
        current_day=current_day,
        current_topic=current_topic,
        current_objectives=current_objs,
        next_day=next_day,
        next_topic=next_topic,
        next_objectives=next_objs,
        transcript_history=json.dumps(session['history'][-4:], indent=2)
    )

    reply_raw = await call_gemini(prompts.SYSTEM_INTERVIEWER, interviewer_prompt, response_json=True)
    
    try:
        reply_json = json.loads(reply_raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip())
        reply = reply_json.get("reply", reply_raw)
        signal = reply_json.get("signal", "advance")
    except Exception:
        reply = reply_raw
        signal = "advance"
    
    # Process signal
    if signal == "advance":
        session["current_day_index"] = next_day_index
        asked_day = next_day
    else:
        # For 'deepen' or 'scaffold', we stay on the current topic
        asked_day = current_day

    if asked_day not in session["covered_days"]:
        session["covered_days"].append(asked_day)
    
    session["asked_questions"] += 1
    session["history"].append({"role": "interviewer", "text": reply})
    await save_session(session_id, session)
    
    return reply, False, None