# api/kramer/interfaces.py
import dataclasses
from typing import List, Dict, Any, Literal

import dataclasses_json
from genai_processors import content_api

ProcessorPart = content_api.ProcessorPart

@dataclasses_json.dataclass_json
@dataclasses.dataclass(frozen=True)
class Task:
    """A single task within the plan."""
    task_id: str
    description: str
    dependencies: List[str]
    status: Literal['pending', 'completed', 'failed'] = 'pending'
    result: str | None = None
    critique: 'Critique | None' = None

@dataclasses_json.dataclass_json
@dataclasses.dataclass(frozen=True)
class Plan:
    """The full DAG of tasks to be executed."""
    tasks: List[Task]

@dataclasses_json.dataclass_json
@dataclasses.dataclass(frozen=True)
class Critique:
    """The output of the Critic agent."""
    status: Literal['success', 'failure']
    justification: str

@dataclasses.dataclass
class KramerConfig:
    """Configuration for all KRAMER models."""
    # Do not ever use outdated gemini 1.5 models
    model_name: str = 'gemini-2.5-flash'
    # In a real scenario, we might have different models per agent
    # planner_model: str = 'gemini-1.5-pro'
    # executor_model: str = 'gemini-1.5-flash'
    # critic_model: str = 'gemini-1.5-flash'
    # synthesizer_model: str = 'gemini-1.5-pro'
