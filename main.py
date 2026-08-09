from dotenv import load_dotenv

# Ensure environment variables are loaded before any application setup
load_dotenv()

from fastapi import FastAPI, HTTPException
from fastapi.responses import RedirectResponse, HTMLResponse
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

DEMO_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Interview Agent Demo</title>
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; line-height: 1.6; }
        h1 { color: #2d3748; }
        .chat-container { border: 1px solid #e2e8f0; padding: 20px; border-radius: 8px; height: 450px; overflow-y: auto; margin-bottom: 20px; background: #f8fafc; }
        .message { margin-bottom: 15px; padding: 12px; border-radius: 8px; max-width: 85%; }
        .interviewer { background: #ebf8ff; color: #2c5282; margin-right: auto; }
        .candidate { background: #e2e8f0; color: #2d3748; margin-left: auto; }
        .input-group { display: flex; gap: 10px; }
        input[type="text"] { flex-grow: 1; padding: 12px; border-radius: 6px; border: 1px solid #cbd5e0; font-size: 16px; }
        button { padding: 12px 24px; background: #3182ce; color: white; border: none; border-radius: 6px; cursor: pointer; font-size: 16px; font-weight: bold; }
        button:hover { background: #2b6cb0; }
        button:disabled { background: #a0aec0; cursor: not-allowed; }
        #feedback { display: none; background: #f0fff4; border: 1px solid #9ae6b4; padding: 30px; border-radius: 8px; margin-top: 20px; }
        ul { padding-left: 20px; }
        li { margin-bottom: 8px; }
    </style>
</head>
<body>
    <h1>AI Technical Interview Demo</h1>
    <p>This is a live interactive demo of the ABTalks Technical Interview Agent. It simulates a dynamic multi-turn technical evaluation.</p>
    
    <div id="setup" style="text-align: center; margin-top: 40px;">
        <button id="startBtn" onclick="startInterview()">Start Interview Session</button>
    </div>
    
    <div id="chat" style="display:none;">
        <div class="chat-container" id="chatBox"></div>
        <div class="input-group">
            <input type="text" id="userInput" placeholder="Type your technical response here..." onkeypress="if(event.key === 'Enter') sendMessage()">
            <button id="sendBtn" onclick="sendMessage()">Send</button>
        </div>
    </div>

    <div id="feedback"></div>

    <script>
        const sessionId = "demo-" + Math.random().toString(36).substring(7);
        const chatBox = document.getElementById('chatBox');
        
        function formatText(text) {
            return text.replace(/\\n/g, '<br>').replace(/\\*\\*(.*?)\\*\\*/g, '<strong>$1</strong>');
        }
        
        function appendMessage(role, text) {
            const div = document.createElement('div');
            div.className = 'message ' + role;
            const timeStr = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
            div.innerHTML = `<strong>${role === 'interviewer' ? 'AI Interviewer' : 'You'}</strong> <span style="font-size: 0.8em; color: #718096; margin-left: 8px;">${timeStr}</span><br> ${formatText(text)}`;
            chatBox.appendChild(div);
            chatBox.scrollTop = chatBox.scrollHeight;
        }

        async function startInterview() {
            document.getElementById('setup').style.display = 'none';
            document.getElementById('chat').style.display = 'block';
            
            // Mock candidate matching the schema
            const candidate = {
                "member": {
                    "id": "CAND-DEMO-001",
                    "name": "Demo Candidate",
                    "jobRole": "Senior AI Engineer",
                    "yearsExperience": 5,
                    "education": "MS Computer Science"
                },
                "missions": [
                    {"day": 7, "title": "Embeddings & Vectors", "passed": true, "attempts": 1},
                    {"day": 12, "title": "RAG Implementation", "passed": false, "attempts": 3},
                    {"day": 22, "title": "Multi-Agent Systems", "skipped": true}
                ]
            };
            
            appendMessage('interviewer', '<em>Initializing interview session and analyzing candidate history...</em>');
            document.getElementById('sendBtn').disabled = true;
            document.getElementById('userInput').disabled = true;
            
            try {
                const res = await fetch('/api/interview', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({sessionId, candidate})
                });
                const data = await res.json();
                chatBox.innerHTML = ''; 
                appendMessage('interviewer', data.reply || "Error starting interview.");
            } catch(e) {
                chatBox.innerHTML = '';
                appendMessage('interviewer', "Network error reaching /api/interview endpoint.");
            }
            
            document.getElementById('sendBtn').disabled = false;
            document.getElementById('userInput').disabled = false;
            document.getElementById('userInput').focus();
        }

        async function sendMessage() {
            const input = document.getElementById('userInput');
            const text = input.value.trim();
            if(!text) return;
            
            input.value = '';
            document.getElementById('sendBtn').disabled = true;
            input.disabled = true;
            
            appendMessage('candidate', text);
            appendMessage('interviewer', '<em>Evaluating response and preparing next question...</em>');
            
            try {
                const res = await fetch('/api/interview', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({sessionId, message: text})
                });
                const data = await res.json();
                
                chatBox.lastChild.remove();
                
                appendMessage('interviewer', data.reply || "Error continuing interview.");
                
                if(data.done) {
                    document.getElementById('chat').style.display = 'none';
                    const fb = document.getElementById('feedback');
                    fb.style.display = 'block';
                    fb.innerHTML = `
                        <h2>Evaluation Complete</h2>
                        <p><strong>Summary:</strong> ${data.feedback?.summary || 'N/A'}</p>
                        <h3>Technical Strengths</h3>
                        <ul>${(data.feedback?.strengths || []).map(s => `<li>${s}</li>`).join('')}</ul>
                        <h3>Identified Gaps</h3>
                        <ul>${(data.feedback?.gaps || []).map(s => `<li>${s}</li>`).join('')}</ul>
                        <h3>Actionable Recommendations</h3>
                        <ul>${(data.feedback?.next || []).map(s => `<li>${s}</li>`).join('')}</ul>
                        
                        <div style="margin-top: 30px; text-align: center;">
                            <button onclick="window.location.reload()">Start New Session</button>
                        </div>
                    `;
                } else {
                    document.getElementById('sendBtn').disabled = false;
                    input.disabled = false;
                    input.focus();
                }
            } catch(e) {
                chatBox.lastChild.remove();
                appendMessage('interviewer', "Network error reaching API.");
                document.getElementById('sendBtn').disabled = false;
                input.disabled = false;
            }
        }
    </script>
</body>
</html>
"""

@app.get("/demo", response_class=HTMLResponse, include_in_schema=False)
async def get_demo():
    return DEMO_HTML


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