from fastapi import FastAPI, HTTPException
import yaml
import subprocess

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
def reset_environment(task_id: str = "easy_brute_force"):
    try:
        env.set_task(task_id)
        return env.reset()
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/state", response_model=Observation)
def get_current_state():
    if not env.state_data:
        raise HTTPException(status_code=400, detail="Environment not initialized. Call /reset first.")
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
    
    score = 0.0
    # The presence of the specific task alert determines failure
    alert_ids = [a.alert_id for a in env.state_data.active_alerts]
    
    if env.current_task_id == "easy_brute_force" and "ALT-001" not in alert_ids:
        score = 1.0
    elif env.current_task_id == "medium_lateral_movement" and "ALT-002" not in alert_ids:
        score = 1.0
    elif env.current_task_id == "hard_insider_threat" and "ALT-003" not in alert_ids:
        score = 1.0
    
    return {"score": score, "task_id": env.current_task_id}

# Bulletproof JSON Baseline Return
@app.post("/baseline")
def trigger_baseline():
    try:
        result = subprocess.run(
            ["python", "-m", "src.baseline"], 
            capture_output=True, text=True, check=True
        )
        
        # Parse the stdout to extract scores safely into JSON
        scores = {}
        for line in result.stdout.split("\n"):
            if "easy_brute_force" in line and "/" in line and ":" in line:
                scores["easy_brute_force"] = float(line.split(":")[1].split("/")[0].strip())
            elif "medium_lateral_movement" in line and "/" in line and ":" in line:
                scores["medium_lateral_movement"] = float(line.split(":")[1].split("/")[0].strip())
            elif "hard_insider_threat" in line and "/" in line and ":" in line:
                scores["hard_insider_threat"] = float(line.split(":")[1].split("/")[0].strip())

        return {
            "status": "success",
            "scores": scores,
            "raw_logs": result.stdout
        }
    except subprocess.CalledProcessError as e:
        raise HTTPException(status_code=500, detail=f"Baseline script failed: {e.stderr}")