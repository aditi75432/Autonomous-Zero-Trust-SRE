import os
import json
import time
from openai import OpenAI
from pydantic import ValidationError

from server.environment import CloudSecEnv
from server.models import Action

def run_baseline():
    # 1. DYNAMIC API KEY: Checks for Phase 2 HF_TOKEN first, falls back to your OPENAI_API_KEY
    api_key = os.environ.get("HF_TOKEN") or os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("ERROR: Neither HF_TOKEN nor OPENAI_API_KEY environment variables found.")
        return

    # 2. DYNAMIC BASE URL: Checks for Phase 2 URL, falls back to Groq
    base_url = os.environ.get("API_BASE_URL", "https://api.groq.com/openai/v1")
    
    # 3. DYNAMIC MODEL: Checks for Phase 2 Nemotron/Llama model, falls back to orginal
    model_name = os.environ.get("MODEL_NAME", "llama-3.1-8b-instant")

    # The required OpenAI Client initialization
    client = OpenAI(
        base_url=base_url, 
        api_key=api_key
    )
    env = CloudSecEnv()
    tasks = ["easy_brute_force", "medium_lateral_movement", "hard_insider_threat"]
    results = {}

    print("Starting OpenEnv Agentic Baseline Evaluation...")
    print(f"Injecting Agent: {model_name} via {base_url}\n")

    for task in tasks:
        print(f"RUNNING TASK: {task}")
        env.set_task(task)
        obs = env.reset()
        done = False
        
        while not done:
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
                # 4. USING THE DYNAMIC MODEL NAME HERE
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
                action = Action.model_validate_json(llm_output)
                
                obs, reward, done, info = env.step(action)
                
            except ValidationError as e:
                print(f"Schema Validation Error: {e}")
                break
            except Exception as e:
                print(f"API Error: {e}")
                break
        
        results[task] = env.final_score
        time.sleep(2) 

    with open("baseline_results.json", "w") as f:
        json.dump(results, f)
    print("Baseline execution complete. Results saved.")

if __name__ == "__main__":
    run_baseline()