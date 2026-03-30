from fastapi import FastAPI, HTTPException, Request
import yaml
import os
import subprocess
import json

from .models import Action, Observation, Reward
from .environment import CloudSecEnv

app = FastAPI(title="CloudSec SRE Environment API")
env = CloudSecEnv()

def get_manifest():
    with open("openenv.yaml", "r") as f:
        return yaml.safe_load(f)

@app.get("/")
def health_check():
    return {"status": "ok", "message": "CloudSec SRE Environment is running."}


@app.post("/reset", response_model=Observation)
async def reset_environment(request: Request):
    task_id = "easy_brute_force" 
    
    # 1. Try JSON body
    try:
        body = await request.json()
        if isinstance(body, dict) and "task_id" in body:
            task_id = body["task_id"]
    except Exception:
        pass 
        
    # 2. Try URL query parameter
    if request.query_params.get("task_id"):
        task_id = request.query_params.get("task_id")
        
    try:
        env.set_task(task_id)
        return env.reset()
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/state", response_model=Observation)
def get_current_state():
    if not env.state_data:
        raise HTTPException(status_code=400, detail="Environment not initialized.")
    return env.state()

@app.post("/step")
def take_step(action: Action):
    if not env.state_data:
        raise HTTPException(status_code=400, detail="Environment not initialized.")
    
    obs, reward, done, info = env.step(action)
    return {
        "observation": obs.model_dump(),
        "reward": reward.model_dump(),
        "done": done,
        "info": info
    }

@app.get("/tasks")
def list_tasks():
    manifest = get_manifest()
    return {
        "tasks": manifest.get("tasks", []),
        "action_schema": Action.model_json_schema()
    }

@app.get("/grader")
def get_grader_score():
    if not env.state_data:
        return {"score": 0.0, "message": "Environment not initialized."}
    return {"score": env.final_score, "task_id": env.current_task_id}

@app.post("/baseline")
def trigger_baseline():
    # Allow the run if EITHER orginal key OR the hackathon bot's key is present
    if "OPENAI_API_KEY" not in os.environ and "HF_TOKEN" not in os.environ:
        return {"status": "error", "message": "Missing API token (HF_TOKEN or OPENAI_API_KEY)."}
        
    try:
        subprocess.run(["python", "-u", "inference.py"], check=True)
        
        if os.path.exists("baseline_results.json"):
            with open("baseline_results.json", "r") as f:
                scores = json.load(f)
            return {"status": "success", "scores": scores, "raw_logs": "Execution completed via inference.py."}
        else:
            return {"status": "error", "message": "inference.py ran but did not output results."}
            
    except subprocess.CalledProcessError as e:
        return {"status": "error", "message": "inference.py script crashed."}
    
def main():
    import uvicorn
    uvicorn.run("server.app:app", host="0.0.0.0", port=7860)

if __name__ == "__main__":
    main()