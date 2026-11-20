from abc import ABC, abstractmethod
from typing import Any, Dict, List


class BaseLLMProvider(ABC):
    """Abstract interface for LLM planning engines."""

    @abstractmethod
    def plan_next_step(
        self,
        messages: List[Dict[str, Any]],
        tool_definitions: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Determines the next agent action.
        Returns:
            {
                "type": "tool_calls",
                "tool_calls": [{"name": str, "args": dict, "id": str}]
            }
            or
            {
                "type": "final_answer",
                "content": str
            }
        """
        pass
