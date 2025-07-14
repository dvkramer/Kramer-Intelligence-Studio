# my-man-jules/kramer/processors/executor_and_critic.py

import json
from typing import AsyncIterable

from genai_processors import content_api
from genai_processors import processor
from genai_processors.core import genai_model
from .. import interfaces
from .. import prompts

ProcessorPart = processor.ProcessorPart

class ExecutorAndCritic(processor.PartProcessor):
    """A PartProcessor that executes a task, then immediately critiques the result."""

    def __init__(self, api_key: str, model_name: str = 'gemini-1.5-flash-latest'):
        self.api_key = api_key
        self.model_name = model_name
        self.executor_model = genai_model.GenaiModel(api_key, model_name)
        self.critic_model = genai_model.GenaiModel(
            api_key, model_name, generate_content_config={'response_mime_type': 'application/json'}
        )

    def match(self, part: ProcessorPart) -> bool:
        # This processor only acts on Task dataclasses
        return content_api.is_dataclass(part.mimetype, interfaces.Task)

    async def call(self, part: ProcessorPart, original_query: str, completed_tasks: dict[str, interfaces.Task]) -> AsyncIterable[ProcessorPart]:
        task = part.get_dataclass(interfaces.Task)

        # 1. Execute the task
        dependency_results = "\n".join(
            f"Result from dependent task '{dep_id}': {completed_tasks[dep_id].result}"
            for dep_id in task.dependencies
        )
        executor_prompt = prompts.EXECUTOR_PROMPT.format(
            query=original_query,
            task_description=task.description,
            dependency_results=dependency_results if dependency_results else "None."
        )

        result_parts = []
        async for res_part in self.executor_model(processor.stream_content([executor_prompt])):
            result_parts.append(res_part)
        task.result = content_api.as_text(result_parts)

        # 2. Critique the result
        critic_prompt = prompts.CRITIC_PROMPT.format(
            query=original_query,
            task_description=task.description,
            executor_output=task.result
        )

        critique_parts = []
        async for crit_part in self.critic_model(processor.stream_content([critic_prompt])):
            critique_parts.append(crit_part)

        try:
            critique_data = json.loads(content_api.as_text(critique_parts))
            task.critic_output = interfaces.CriticOutput(**critique_data)
        except json.JSONDecodeError as e:
             task.critic_output = interfaces.CriticOutput(status="failure", justification=f"Critic failed to produce valid JSON. Details: {e}")

        # Yield the updated task with result and critique
        yield ProcessorPart.from_dataclass(task)
