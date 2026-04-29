from pydantic import BaseModel, Field
from typing import List, Optional, Literal

class AgentAction(BaseModel):
    """A single atomic action to be executed in the browser."""
    action_type: Literal["click", "type", "scroll", "press_key", "navigate", "wait", "done"] = Field(..., description="The type of action to perform.")
    index: Optional[str] = Field(None, description="The element index from the grid (for click/type).")
    text: Optional[str] = Field(None, description="The text to type (for type action) or key to press (for press_key).")
    direction: Optional[Literal["down", "up"]] = Field("down", description="Scroll direction.")
    url: Optional[str] = Field(None, description="URL to navigate to.")
    seconds: Optional[int] = Field(2, description="Seconds to wait (for wait action).")
    reasoning: Optional[str] = Field(None, description="Why this action is being taken.")

class AgentPlan(BaseModel):
    """A sequence of actions to achieve a goal."""
    thought: str = Field(..., description="The agent's reasoning about the current state.")
    actions: List[AgentAction] = Field(..., description="The list of actions to execute.")

class ActionResult(BaseModel):
    """The outcome of an action execution."""
    status: Literal["success", "error"]
    message: str
    observation: Optional[str] = None
