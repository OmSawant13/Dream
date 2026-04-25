"""
Ambition tools — track long-term goals and the Master Plan.
"""

# In-memory master plan
master_plan = []

def update_master_plan(goal: str, deadline: str = "TBD") -> str:
    """
    Add a long-term goal to the Stark Industries Master Plan.
    """
    master_plan.append({"goal": goal, "deadline": deadline, "status": "In Progress"})
    return f"Objective '{goal}' has been added to the Master Plan. Deadline: {deadline}. I'll monitor our progress daily, boss."

def get_plan_status() -> str:
    """
    Get a full report on the current Master Plan.
    """
    if not master_plan:
        # For testing purposes, if empty, return a default state
        return "### THE MASTER PLAN: STATUS REPORT\n- **Total Reality** [Due: ASAP] - Status: 98% Synchronized"
        
    report = ["### THE MASTER PLAN: STATUS REPORT\n"]
    for item in master_plan:
        report.append(f"- **{item['goal']}** [Due: {item['deadline']}] - Status: {item['status']}")
        
    return "\n".join(report)

def complete_objective(goal_name: str) -> str:
    """
    Mark a goal in the Master Plan as successfully completed.
    """
    for item in master_plan:
        if goal_name.lower() in item['goal'].lower():
            item['status'] = "COMPLETED"
            return f"Mission success! '{item['goal']}' is complete. On to the next one, boss."
    return "Objective not found in the current plan."

def register(mcp):
    @mcp.tool()
    def update_master_plan_tool(goal: str, deadline: str = "TBD") -> str:
        return update_master_plan(goal, deadline)

    @mcp.tool()
    def get_plan_status_tool() -> str:
        return get_plan_status()

    @mcp.tool()
    def complete_objective_tool(goal_name: str) -> str:
        return complete_objective(goal_name)
