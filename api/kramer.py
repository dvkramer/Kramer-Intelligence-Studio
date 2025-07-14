# api/kramer.py

import os
import json
import traceback
from vercel_helpers import VercelRequest, VercelResponse
import google.genai as genai
from google.genai import types

# --- CLIENT CONFIGURATION ---
try:
    genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
    client = genai.Client()
    # CORRECTED MODEL NAME AS PER YOUR INSTRUCTION.
    MODEL_NAME = "gemini-2.5-flash"
except Exception as e:
    print(f"FATAL: Could not configure Gemini client. Error: {e}")
    client = None

# --- AGENT 1: PLANNER ---
def call_planner(user_prompt: str) -> dict:
    """Deconstructs the user request into a JSON plan."""
    prompt = f"""
    You are an expert project planner. Your job is to break down a complex user request into a series of simple, sequential, and dependent steps. Represent this plan as a JSON object that is a list of nodes, where each node has an "id", a "task" description, and a "dependencies" list. The dependency list should contain the IDs of tasks that must be completed before this one can start. The first task should have no dependencies.

    User Request: "{user_prompt}"

    Create the plan. Respond with ONLY the raw JSON object and nothing else.
    """
    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=prompt,
        generation_config={"response_mime_type": "application/json"}
    )
    return json.loads(response.text)

# --- AGENT 2: EXECUTOR ---
def call_executor(task_description: str, context: str, user_prompt: str) -> str:
    """Executes a single task, using Google Search if necessary."""
    prompt = f"""
    You are an Executor agent. Your sole focus is to complete the following task. You have access to a Google Search tool. Use the provided context from previous steps to inform your work. Be concise and factual in your output.

    Original User Goal: "{user_prompt}"
    Context from Previous Steps:
    {context}

    Current Task: "{task_description}"

    Execute the task now.
    """
    grounding_tool = types.Tool(google_search=types.GoogleSearch())
    config = types.GenerateContentConfig(tools=[grounding_tool])

    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=prompt,
        config=config,
    )
    return response.text

# --- AGENT 3: CRITIC ---
def call_critic(task_description: str, executor_output: str, user_prompt: str) -> dict:
    """Verifies the Executor's output."""
    prompt = f"""
    You are a meticulous Critic agent. Your job is to verify the work of another AI. Assess the provided "Execution Result" to see if it successfully and accurately completes the "Task Description" in the context of the "Original User Goal".

    Original User Goal: "{user_prompt}"
    Task Description: "{task_description}"
    Execution Result: "{executor_output}"

    Respond with ONLY a JSON object with two keys: "status" ('success' or 'failure') and "reason" (a brief explanation for your judgment, especially on failure).
    """
    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=prompt,
        generation_config={"response_mime_type": "application/json"}
    )
    return json.loads(response.text)

# --- AGENT 4: SYNTHESIZER ---
def call_synthesizer(verified_results: dict, user_prompt: str) -> str:
    """Assembles the final answer from verified results."""
    results_string = json.dumps(verified_results, indent=2)
    prompt = f"""
    You are a masterful Synthesizer. Your job is to formulate a final, well-written, and comprehensive answer to the user's original request. Use only the provided "Verified Results" from the completed plan. Do not add any information not supported by these results. Weave them together into a single, cohesive response.

    Original User Request: "{user_prompt}"
    Verified Results:
    {results_string}

    Provide the final answer now.
    """
    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=prompt
    )
    return response.text

# --- ORCHESTRATOR / MAIN HANDLER ---
def handler(request: VercelRequest):
    if client is None:
        return VercelResponse(status_code=500, body={"error": "Gemini client not initialized. Check API key."})

    try:
        body = request.body
        user_prompt = body.get("prompt")
        if not user_prompt:
            return VercelResponse(status_code=400, body={"error": "Prompt is required."})

        # 1. PLANNING
        plan_data = call_planner(user_prompt)
        plan = plan_data.get("plan", [])
        if not plan:
            return VercelResponse(status_code=500, body={"error": "Failed to generate a valid plan."})

        # State Management
        results = {}
        node_status = {node["id"]: "pending" for node in plan}
        
        # 2. EXECUTION LOOP
        max_loops = len(plan) + 5  # Safety break
        loops = 0
        while "pending" in node_status.values() and loops < max_loops:
            loops += 1
            progress_made = False
            for node in plan:
                node_id = node["id"]
                if node_status[node_id] == "pending":
                    dependencies = node.get("dependencies", [])
                    if all(node_status.get(dep_id) == "completed" for dep_id in dependencies):
                        progress_made = True
                        context = "\n".join([f"- Result for task {dep_id}: {results.get(dep_id, 'N/A')}" for dep_id in dependencies])
                        
                        executor_output = call_executor(node["task"], context, user_prompt)
                        critic_judgement = call_critic(node["task"], executor_output, user_prompt)

                        if critic_judgement.get("status") == "success":
                            results[node_id] = executor_output
                            node_status[node_id] = "completed"
                        else:
                            results[node_id] = f"FAILED: {critic_judgement.get('reason', 'No reason provided.')}"
                            node_status[node_id] = "failed"
            
            if not progress_made and "pending" in node_status.values():
                 # Handles circular dependencies or other logic stalls
                return VercelResponse(status_code=500, body={"error": "Execution stalled. Check plan for circular dependencies."})


        # 3. SYNTHESIS
        verified_results = {k: v for k, v in results.items() if node_status.get(k) == "completed"}
        if not verified_results:
            return VercelResponse(status_code=500, body={"error": "No tasks were successfully completed. Cannot synthesize a final answer."})

        final_answer = call_synthesizer(verified_results, user_prompt)

        # 4. COMPLETION
        return VercelResponse(status_code=200, body={"answer": final_answer})

    except Exception as e:
        print(traceback.format_exc())
        return VercelResponse(status_code=500, body={"error": str(e)})