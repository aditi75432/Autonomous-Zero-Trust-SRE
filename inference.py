import os
import json
import time
from typing import List, Optional
from openai import OpenAI
from pydantic import ValidationError

from server.environment import CloudSecEnv
from server.models import Action

def log_start(task: str, env: str, model: str) -> None:
    print(f"[START] task={task} env={env} model={model}", flush=True)

def log_step(step: int, action: str, reward: float, done: bool, error: Optional[str]) -> None:
    error_val = error if error else "null"
    done_val = str(done).lower()
    print(f"[STEP] step={step} action={action} reward={reward:.2f} done={done_val} error={error_val}", flush=True)

def log_end(success: bool, steps: int, score: float, rewards: List[float]) -> None:
    rewards_str = ",".join(f"{r:.2f}" for r in rewards)
    print(f"[END] success={str(success).lower()} steps={steps} score={score:.3f} rewards={rewards_str}", flush=True)

def run_baseline():
    api_key = os.environ.get("HF_TOKEN") or os.environ.get("OPENAI_API_KEY")
    if not api_key:
        return

    base_url = os.environ.get("API_BASE_URL", "https://api.groq.com/openai/v1")
    model_name = os.environ.get("MODEL_NAME", "llama-3.1-8b-instant")
    benchmark_name = "cloudsec-sre-env"

    client = OpenAI(
        base_url=base_url, 
        api_key=api_key
    )
    env = CloudSecEnv()
    tasks = ["easy_brute_force", "medium_lateral_movement", "hard_insider_threat"]
    results = {}

    for task in tasks:
        env.set_task(task)
        obs = env.reset()
        done = False
        step_count = 0
        rewards = []
        
        log_start(task=task, env=benchmark_name, model=model_name)
        
        while not done and step_count < 10:
            step_count += 1
            error_msg = None
            action_str = "unknown"
            reward_val = 0.0
            
            system_prompt = (
                "You are an autonomous Cloud Security Site Reliability Engineer (SRE). "
                "Your objective is to resolve security incidents based on the active alerts and system state. "
                "CRITICAL: You MUST respond ONLY with a valid JSON object matching the provided schema."
            )
            
            user_prompt = (
                f"ACTION SCHEMA:\n{json.dumps(Action.model_json_schema(), indent=2)}\n\n"
                f"CURRENT ENVIRONMENT STATE:\n{obs.model_dump_json(indent=2)}\n\n"
                "Based on the alerts and state, what is your next action?"
            )

            try:
                response = client.chat.completions.create(
                    model=model_name,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    response_format={ "type": "json_object" }, 
                    temperature=0.0 
                )
                
                llm_output = response.choices[0].message.content
                action_str = json.dumps(json.loads(llm_output), separators=(',', ':'))
                action = Action.model_validate_json(llm_output)
                
                obs, reward, done, info = env.step(action)
                reward_val = reward.value
                
            except ValidationError as e:
                error_msg = "SchemaValidationError"
                done = True
            except Exception as e:
                error_msg = "APIError"
                done = True
                
            rewards.append(reward_val)
            log_step(step=step_count, action=action_str, reward=reward_val, done=done, error=error_msg)
        
        score = sum(rewards)
        score = min(max(score, 0.0), 1.0)
        success = score > 0.0
        
        log_end(success=success, steps=step_count, score=score, rewards=rewards)
        results[task] = env.final_score
        time.sleep(2) 

    with open("baseline_results.json", "w") as f:
        json.dump(results, f)

if __name__ == "__main__":
    run_baseline()