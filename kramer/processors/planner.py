# my-man-jules/kramer/processors/planner.py

import json
from typing import AsyncIterable

from genai_processors import content_api
from genai_processors import processor
from genai_processors.core import genai_model
from genai_processors.core import preamble
from .. import interfaces
from .. import prompts

ProcessorPart = processor.ProcessorPart

class Planner(processor.Processor):
    """Generates a Plan dataclass from a user query."""

    def __init__(self, api_key: str, model_name: str = 'gemini-1.5-flash-latest'):
        p_preamble = preamble.Preamble(
            content=[ProcessorPart(prompts.PLANNER_PROMPT)]
        )
        p_genai_model = genai_model.GenaiModel(
            api_key=api_key,
            model_name=model_name,
            generate_content_config={'response_mime_type': 'application/json'},
        )
        self._pipeline = p_preamble + p_genai_model

    async def call(self, content: AsyncIterable[ProcessorPart]) -> AsyncIterable[ProcessorPart]:
        query = content_api.as_text(content)
        # We need to format the prompt with the query
        formatted_prompt_part = ProcessorPart(prompts.PLANNER_PROMPT.format(query=query))

        json_parts = []
        model = genai_model.GenaiModel(api_key=self._pipeline.processors[-1].api_key, model_name=self._pipeline.processors[-1].model_name, generate_content_config={'response_mime_type': 'application/json'})

        async for part in model(processor.stream_content([formatted_prompt_part])):
            json_parts.append(part)

        json_text = content_api.as_text(json_parts)
        try:
            plan_data = json.loads(json_text)
            plan = interfaces.Plan(**plan_data)
            yield ProcessorPart.from_dataclass(plan)
            yield processor.status(f"Plan generated with {len(plan.tasks)} tasks.")
        except json.JSONDecodeError as e:
            yield processor.status(f"ERROR: Planner failed to produce valid JSON. Details: {e}\nRaw output: {json_text}")
