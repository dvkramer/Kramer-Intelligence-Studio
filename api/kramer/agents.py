# api/kramer/agents.py
from genai_processors import processor
from genai_processors.core import genai_model, preamble
from google.genai import types as genai_types

from . import interfaces, prompts

ProcessorPart = processor.ProcessorPart

class PlannerAgent(processor.Processor):
    """Generates a task plan (DAG) from a user query."""
    def __init__(self, api_key: str, config: interfaces.KramerConfig):
        p_preamble = preamble.Preamble([ProcessorPart(prompts.PLANNER_PREAMBLE)])
        p_model = genai_model.GenaiModel(
            api_key=api_key,
            model_name=config.model_name,
            generate_content_config={'response_mime_type': 'application/json', 'response_schema': interfaces.Plan}
        )
        self._pipeline = p_preamble + p_model

    async def call(self, content):
        async for part in self._pipeline(content):
            yield part

class ExecutorAgent(processor.Processor):
    """Executes a single task, potentially with tools."""
    def __init__(self, api_key: str, config: interfaces.KramerConfig):
        p_preamble = preamble.Preamble([ProcessorPart(prompts.EXECUTOR_PREAMBLE)])
        p_model = genai_model.GenaiModel(
            api_key=api_key,
            model_name=config.model_name,
            generate_content_config=genai_types.GenerateContentConfig(
                tools=[genai_types.Tool(google_search=genai_types.GoogleSearch())]
            )
        )
        self._pipeline = p_preamble + p_model

    async def call(self, content):
        async for part in self._pipeline(content):
            yield part

class CriticAgent(processor.Processor):
    """Critiques the output of the Executor."""
    def __init__(self, api_key: str, config: interfaces.KramerConfig):
        p_preamble = preamble.Preamble([ProcessorPart(prompts.CRITIC_PREAMBLE)])
        p_model = genai_model.GenaiModel(
            api_key=api_key,
            model_name=config.model_name,
            generate_content_config={'response_mime_type': 'application/json', 'response_schema': interfaces.Critique}
        )
        self._pipeline = p_preamble + p_model

    async def call(self, content):
        async for part in self._pipeline(content):
            yield part

class SynthesizerAgent(processor.Processor):
    """Synthesizes all verified results into a final answer."""
    def __init__(self, api_key: str, config: interfaces.KramerConfig):
        p_preamble = preamble.Preamble([ProcessorPart(prompts.SYNTHESIZER_PREAMBLE)])
        p_model = genai_model.GenaiModel(api_key=api_key, model_name=config.model_name)
        self._pipeline = p_preamble + p_model

    async def call(self, content):
        async for part in self._pipeline(content):
            yield part
