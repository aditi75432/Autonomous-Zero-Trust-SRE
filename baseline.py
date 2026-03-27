import os
import json
from openai import OpenAI
from pydantic import ValidationError
from .environment import CloudSecEnv
from .models import Action

def run_baseline():
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("ERROR: OPENAI_API_KEY environment variable not found.")
        return

    client = OpenAI(
        base_url="https://api.groq.com/openai/v1", 
        api_key=api_key
    )
    env = CloudSecEnv()
    
    tasks = ["easy_brute_force", "medium_lateral_movement", "hard_insider_threat"]
    results = {}

    print("Starting OpenEnv Agentic Baseline Evaluation...\n")

    for task in tasks:
        print(f"RUNNING TASK: {task}")
        
        env.set_task(task)
        obs = env.reset()
        done = False
        
        while not done:
            system_prompt = (
                "You are an autonomous Cloud Security Site Reliability Engineer (SRE). "
                "Your objective is to resolve security incidents based on the active alerts and system state. "
                "CRITICAL: You MUST respond ONLY with a valid JSON object matching the provided schema. "
                "Do not include markdown blocks or extra text."
            )
            
            user_prompt = (
                f"ACTION SCHEMA:\n{json.dumps(Action.model_json_schema(), indent=2)}\n\n"
                f"CURRENT ENVIRONMENT STATE:\n{obs.model_dump_json(indent=2)}\n\n"
                "Based on the alerts and state, what is your next action?"
            )

            try:
                response = client.chat.completions.create(
                    model="llama-3.1-8b-instant",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    response_format={ "type": "json_object" }, 
                    temperature=0.0 
                )
                
                llm_output = response.choices[0].message.content
                
                action = Action.model_validate_json(llm_output)
                print(f"Agent Action: {action.action_type.value} -> Target: {action.target}")
                print(f"Justification: {action.justification}")
                
                obs, reward, done, info = env.step(action)
                print(f"Step Reward: {reward.value} | System Message: {reward.message}\n")
                
            except ValidationError as e:
                print(f"Schema Validation Error (Agent Hallucinated): {e}")
                break
            except Exception as e:
                print(f"API or Execution Error: {e}")
                break
        
        final_score = 0.0
        if task == "easy_brute_force" and "198.51.100.44" in env.state_data.blocked_ips:
            final_score = 1.0
        elif task == "medium_lateral_movement" and "frontend-web-pod-2" in env.state_data.isolated_services:
            final_score = 1.0
        elif task == "hard_insider_threat" and "iam-role-billing-service" in env.state_data.revoked_roles:
            final_score = 1.0
            
        results[task] = final_score
        print(f"Task {task} Finished. Final Score: {final_score}\n")

    print("BASELINE RESULTS SUMMARY")
    print("-" * 30)
    for t, s in results.items():
        print(f"{t.ljust(25)} : {s}/1.0")
    print("-" * 30)

    # Save results to a file so the API can read them reliably
    with open("baseline_results.json", "w") as f:
        json.dump(results, f)

if __name__ == "__main__":
    run_baseline()