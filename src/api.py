from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
import yaml
import os
import subprocess

from .models import Action, Observation, Reward
from .environment import CloudSecEnv

# Initialize the FastAPI app and our core environment
app = FastAPI(title="CloudSec SRE Environment API")
env = CloudSecEnv()

# Helper function to read the manifest
def get_manifest():
    with open("openenv.yaml", "r") as f:
        return yaml.safe_load(f)


# STANDARD OPENENV ENDPOINTS

@app.get("/")
def health_check():
    """Automated ping to the Space URL — must return 200"""
    return {"status": "ok", "message": "CloudSec SRE Environment is running."}

@app.post("/reset", response_model=Observation)
def reset_environment(task_id: str = "easy_brute_force"):
    """Resets the environment for a specific task."""
    try:
        env.set_task(task_id)
        return env.reset()
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/state", response_model=Observation)
def get_current_state():
    """Returns the current state without taking an action."""
    if not env.state_data:
        raise HTTPException(status_code=400, detail="Environment not initialized. Call /reset first.")
    return env.state()

@app.post("/step")
def take_step(action: Action):
    """Executes an action and returns the new state and reward."""
    if not env.state_data:
        raise HTTPException(status_code=400, detail="Environment not initialized.")
    
    obs, reward, done, info = env.step(action)
    return {
        "observation": obs.model_dump(),
        "reward": reward.model_dump(),
        "done": done,
        "info": info
    }


# CUSTOM ENDPOINTS


@app.get("/tasks")
def list_tasks():
    """Returns list of tasks and the action schema."""
    manifest = get_manifest()
    return {
        "tasks": manifest.get("tasks", []),
        "action_schema": Action.model_json_schema()
    }

@app.get("/grader")
def get_grader_score():
    """Returns grader score after an episode is completed."""
    # To determine the final score, we evaluate the current state
    if not env.state_data:
        return {"score": 0.0, "message": "Environment not initialized."}
    
    score = 0.0
    if env.current_task_id == "easy_brute_force" and not env.state_data.active_alerts:
        score = 1.0
    elif env.current_task_id == "medium_lateral_movement" and not env.state_data.active_alerts:
        score = 1.0
    # (Hard task logic applies here)
    
    return {"score": score, "task_id": env.current_task_id}

@app.post("/baseline")
def trigger_baseline():
    """Triggers inference script and returns baseline score for all 3 tasks."""
    # We use subprocess to run the baseline.py script asynchronously or wait for it
    try:
        # Note: In a real deployment, you'd want to handle this asynchronously 
        # so the HTTP request doesn't time out, but for the hackathon spec, blocking is usually expected.
        result = subprocess.run(
            ["python", "-m", "src.baseline"], 
            capture_output=True, text=True, check=True
        )
        return {"status": "success", "output": result.stdout}
    except subprocess.CalledProcessError as e:
        raise HTTPException(status_code=500, detail=f"Baseline script failed: {e.stderr}")