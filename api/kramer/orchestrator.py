# api/kramer/orchestrator.py
import asyncio
import json
from typing import AsyncGenerator, Dict

from genai_processors import content_api, processor, streams
from . import agents, interfaces

class Orchestrator:
    """Manages the KRAMER workflow of plan, execute, critique, synthesize."""

    def __init__(self, api_key: str):
        self._api_key = api_key
        self._config = interfaces.KramerConfig()
        self._planner = agents.PlannerAgent(api_key, self._config)
        self._executor = agents.ExecutorAgent(api_key, self._config)
        self._critic = agents.CriticAgent(api_key, self._config)
        self._synthesizer = agents.SynthesizerAgent(api_key, self._config)

    async def run(self, user_query: str) -> AsyncGenerator[str, None]:
        """Runs the full KRAMER cycle and yields status updates."""

        yield "PHASE: Planning\n"
        plan_input = streams.stream_content([content_api.ProcessorPart(user_query)])
        plan_response = await content_api.run_processor(self._planner, plan_input)
        plan_json = content_api.as_text(plan_response)

        try:
            plan_data = json.loads(plan_json)
            plan = interfaces.Plan.from_dict(plan_data)
        except (json.JSONDecodeError, KeyError) as e:
            yield f"ERROR: Failed to generate a valid plan. Details: {e}\n"
            return

        yield f"STATUS: Plan generated with {len(plan.tasks)} tasks.\n"

        tasks_by_id: Dict[str, interfaces.Task] = {t.task_id: t for t in plan.tasks}
        completed_tasks: Dict[str, interfaces.Task] = {}

        yield "PHASE: Execution & Critique\n"

        while len(completed_tasks) < len(plan.tasks):
            found_task_to_run = False
            for task_id, task in tasks_by_id.items():
                if task.status == 'pending' and all(dep in completed_tasks for dep in task.dependencies):
                    found_task_to_run = True
                    yield f"STATUS: Starting task '{task.task_id}': {task.description}\n"

                    # 1. Execute
                    dep_results = "\n".join([
                        f"Result from prerequisite task '{dep_id}':\n{completed_tasks[dep_id].result}"
                        for dep_id in task.dependencies
                    ])
                    executor_prompt = f"Original Query: {user_query}\n\nTask: {task.description}\n\nPrerequisite Results:\n{dep_results}"
                    exec_input = streams.stream_content([content_api.ProcessorPart(executor_prompt)])
                    exec_response = await content_api.run_processor(self._executor, exec_input)
                    exec_result = content_api.as_text(exec_response)

                    yield f"STATUS: Task '{task.task_id}' executed. Awaiting critique.\n"

                    # 2. Critique
                    critic_prompt = f"Original goal: {user_query}\n\nTask description: {task.description}\n\nExecutor's output:\n{exec_result}"
                    critique_input = streams.stream_content([content_api.ProcessorPart(critic_prompt)])
                    critique_response = await content_api.run_processor(self._critic, critique_input)
                    critique_json = content_api.as_text(critique_response)

                    try:
                        critique = interfaces.Critique.from_json(critique_json)
                        if critique.status == 'success':
                            updated_task = interfaces.Task(
                                task_id=task.task_id, description=task.description, dependencies=task.dependencies,
                                status='completed', result=exec_result, critique=critique
                            )
                            tasks_by_id[task_id] = updated_task
                            completed_tasks[task_id] = updated_task
                            yield f"STATUS: Task '{task.task_id}' PASSED critique. Justification: {critique.justification}\n"
                        else:
                            raise Exception(f"Task '{task.task_id}' FAILED critique. Justification: {critique.justification}")
                    except Exception as e:
                        yield f"ERROR: {e}\n"
                        # Simple failure model: halt on any failure.
                        return

            if not found_task_to_run and len(completed_tasks) < len(plan.tasks):
                yield "ERROR: Deadlock detected in plan. Halting.\n"
                return

        yield "PHASE: Synthesis\n"
        synthesis_prompt = f"Original Query: {user_query}\n\nVerified Results:\n"
        for task in completed_tasks.values():
            synthesis_prompt += f"\n---\nTask: {task.description}\nResult: {task.result}\n---\n"

        synthesis_input = streams.stream_content([content_api.ProcessorPart(synthesis_prompt)])

        final_report = ""
        async for part in self._synthesizer(synthesis_input):
            if part.text:
                final_report += part.text
                yield f"SYNTHESIS_CHUNK:{part.text}"

        yield f"\nPHASE: Complete\n"
