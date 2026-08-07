from dotenv import load_dotenv

# Ensure environment variables are loaded before any application setup
load_dotenv()

from fastapi import FastAPI, HTTPException
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from interview_engine import handle_interview_turn

app = FastAPI(
    title="The Interview Agent - ABTalks Hackathon",
    description="Multi-turn AI technical interview engine built with FastAPI and Google Gemini 2.5 Flash.",
    version="1.0.0"
)

# Redirect root URL directly to Swagger documentation
@app.get("/", include_in_schema=False)
async def root():
    return RedirectResponse(url="/docs")

class Feedback(BaseModel):
    summary: str
    strengths: List[str]
    gaps: List[str]
    next: List[str]

class InterviewRequest(BaseModel):
    sessionId: str
    candidate: Optional[Dict[str, Any]] = None
    message: Optional[str] = None

class InterviewResponse(BaseModel):
    reply: str
    done: bool
    feedback: Optional[Feedback] = None

@app.post("/api/interview", response_model=InterviewResponse)
async def conduct_interview(request: InterviewRequest):
    if not request.candidate and not request.message:
        raise HTTPException(
            status_code=400,
            detail="Either 'candidate' (to start) or 'message' (to continue) must be provided."
        )

    try:
        reply, done, feedback_data = await handle_interview_turn(
            session_id=request.sessionId,
            candidate_data=request.candidate,
            user_message=request.message
        )
    except Exception as err:
        raise HTTPException(status_code=500, detail=f"Interview engine processing error: {str(err)}")

    feedback_obj = None
    if feedback_data:
        try:
            feedback_obj = Feedback(**feedback_data)
        except Exception as err:
            # Fallback for minor schema mismatches
            feedback_obj = Feedback(
                summary=feedback_data.get("summary", "Evaluation complete."),
                strengths=feedback_data.get("strengths", []),
                gaps=feedback_data.get("gaps", []),
                next=feedback_data.get("next", [])
            )

    return InterviewResponse(
        reply=reply,
        done=done,
        feedback=feedback_obj
    )