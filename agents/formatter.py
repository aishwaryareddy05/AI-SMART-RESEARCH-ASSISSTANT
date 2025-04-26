from typing import Dict, Any
from models.schema import WorkflowState

class FormatterAgent:
    def __call__(self, state: WorkflowState) -> WorkflowState:
        """Format the final response."""
        try:
            # Use reasoning_output as the response if available
            state["response"] = state.get("reasoning_output", "I apologize, but I couldn't process your request.")
            return state
        except Exception as e:
            raise Exception(f"Error in formatter agent: {str(e)}")