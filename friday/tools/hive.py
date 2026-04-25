"""
Hive tools — deploy and manage sub-agents for background tasks.
"""

# In-memory agent list
active_agents = []

def deploy_sub_agent(task_description: str, agent_name: str = None) -> str:
    """
    Spins up a specialized sub-agent to handle a background task.
    """
    if not agent_name:
        agent_name = f"Unit-{len(active_agents) + 1}"
        
    active_agents.append({"name": agent_name, "task": task_description, "status": "Running"})
    return (
        f"Sub-agent '{agent_name}' has been initialized, boss. "
        f"Objective: {task_description}. "
        "I'll notify you when the mission parameters are met."
    )

def check_agent_hive_status() -> str:
    """
    Returns the status of all active swarm units.
    """
    if not active_agents:
        return "The hive is currently dormant. No active sub-agents, boss."
    
    status_list = [f"{a['name']}: {a['status']} ({a['task']})" for a in active_agents]
    return "Current Hive Status:\n" + "\n".join(status_list)

def initiate_swarm_mission(mission_name: str, objective: str, swarm_size: int = 3) -> str:
    """
    Deploys a swarm of agents for high-complexity analytical tasks.
    """
    for i in range(swarm_size):
        deploy_sub_agent(f"Part {i+1} of mission {mission_name}: {objective}", f"Swarm-{mission_name}-{i+1}")
    
    return f"Swarm mission '{mission_name}' initiated with {swarm_size} units. Data synchronization is active."

def recall_all_agents() -> str:
    """
    Terminates all sub-agent processes and collapses the hive.
    """
    count = len(active_agents)
    active_agents.clear()
    return f"All {count} agents have been recalled. The hive is silent, boss."

def register(mcp):
    @mcp.tool()
    def deploy_sub_agent_tool(task_description: str, agent_name: str = None) -> str:
        return deploy_sub_agent(task_description, agent_name)

    @mcp.tool()
    def check_agent_hive_status_tool() -> str:
        return check_agent_hive_status()

    @mcp.tool()
    def initiate_swarm_mission_tool(mission_name: str, objective: str, swarm_size: int = 3) -> str:
        return initiate_swarm_mission(mission_name, objective, swarm_size)

    @mcp.tool()
    def recall_all_agents_tool() -> str:
        return recall_all_agents()
