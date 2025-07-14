# my-man-jules/kramer/agent.py

import asyncio
from typing import AsyncIterable

from genai_processors import content_api
from genai_processors import processor
from genai_processors.core import genai_model
from . import interfaces
from . import prompts
from .processors import planner
from .processors import executor_and_critic

ProcessorPart = processor.ProcessorPart

class KramerAgent(processor.Processor):
    """
    Orchestrates the KRAMER workflow using genai-processors.
    1. Plan: Generates a task graph.
    2. Execute & Critique Loop: Executes tasks whose dependencies are met and critiques them.
    3. Synthesize: Assembles the final report from verified task results.
    """

    def __init__(self, api_key: str, model_name: str = 'gemini-1.5-flash-latest'):
        self.api_key = api_key
        self.model_name = model_name
        self.planner = planner.Planner(api_key, model_name)
        self.executor_critic = executor_and_critic.ExecutorAndCritic(api_key, model_name)
        self.synthesizer = genai_model.GenaiModel(api_key, model_name)

    async def call(self, content: AsyncIterable[ProcessorPart]) -> AsyncIterable[ProcessorPart]:
        query = await content_api.as_text_async(content)
        state = interfaces.KramerState(original_query=query)

        # 1. Planning Stage
        yield processor.status("PLANNING: Deconstructing query into a plan...")
        plan_part: ProcessorPart | None = None
        async for part in self.planner(processor.stream_content([query])):
            if part.is_dataclass and isinstance(part.get_dataclass(), interfaces.Plan):
                plan_part = part
            yield part # Pass through status updates from the planner

        if not plan_part:
            yield processor.status("FATAL ERROR: Planner did not produce a valid plan. Halting.")
            return

        state.plan = plan_part.get_dataclass(interfaces.Plan)

        # 2. Execution & Critique Loop
        tasks_to_process = list(state.plan.tasks)

        while any(task.id not in state.completed_tasks for task in tasks_to_process):
            runnable_tasks = [
                task for task in tasks_to_process
                if task.id not in state.completed_tasks
                and all(dep in state.completed_tasks for dep in task.dependencies)
            ]

            if not runnable_tasks:
                yield processor.status("ERROR: Deadlock detected or all remaining tasks failed. Halting.")
                # You might want to list failed tasks here
                break

            async def process_task(task: interfaces.Task):
                yield processor.status(f"EXECUTING: Task '{task.id}': {task.description}")
                async for updated_task_part in self.executor_critic.call(ProcessorPart.from_dataclass(task), state.original_query, state.completed_tasks):
                    updated_task = updated_task_part.get_dataclass(interfaces.Task)
                    if updated_task.critic_output.status == 'success':
                        state.completed_tasks[updated_task.id] = updated_task
                        yield processor.status(f"PASSED: Task '{updated_task.id}'.")
                    else:
                        # Mark as failed so we don't retry. For this MVP, we halt on any failure.
                        state.completed_tasks[updated_task.id] = updated_task # Store the failure
                        yield processor.status(f"FAILED: Task '{updated_task.id}'. Reason: {updated_task.critic_output.justification}")
                        # Raise an exception to stop the current processing cycle
                        raise Exception(f"Task {updated_task.id} failed critique.")

            # Run tasks concurrently
            coroutines = [process_task(task) for task in runnable_tasks]
            try:
                for coro in coroutines:
                    async for status_part in coro:
                        yield status_part
            except Exception as e:
                 yield processor.status(f"HALTING: {e}")
                 break # Exit the main while loop on failure

        # 3. Synthesis Stage
        successful_tasks = [t for t in state.completed_tasks.values() if t.critic_output and t.critic_output.status == 'success']
        if len(successful_tasks) == 0:
            yield processor.status("SYNTHESIS: No successful tasks to synthesize. Ending.")
            return

        yield processor.status("SYNTHESIZING: Assembling final report from verified results...")

        all_results = "\n\n---\n\n".join(
            f"Result for Task '{task.id} ({task.description})':\n{task.result}"
            for task in successful_tasks
        )
        synthesis_prompt = prompts.SYNTHESIZER_PROMPT.format(query=state.original_query, all_verified_results=all_results)

        final_report_stream = self.synthesizer(processor.stream_content([synthesis_prompt]))

        yield processor.ProcessorPart("\n\n--- FINAL REPORT ---\n\n")
        async for final_part in final_report_stream:
            yield final_part
