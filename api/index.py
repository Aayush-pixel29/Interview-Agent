import sys
import os

# Add parent directory to sys.path so modules (main, interview_engine, breeth_client, prompts) can be imported in Vercel serverless environment
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from main import app
